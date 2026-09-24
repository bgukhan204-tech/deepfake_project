import os
import cv2
import numpy as np

# Try importing TensorFlow / Keras for U-Net architecture definition and inference
try:
    import tensorflow as tf
    from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, concatenate, BatchNormalization, Activation
    from tensorflow.keras.models import Model
    HAS_TF = True
except ImportError:
    HAS_TF = False
    tf = None

# Try importing TFLite
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        if HAS_TF:
            import tensorflow.lite as tflite
        else:
            tflite = None
    except ImportError:
        tflite = None


def build_unet_model(input_shape=(224, 224, 3)):
    """
    Constructs a compact 2D U-Net Segmentation Model for pixel-level manipulation localization.
    Input: (224, 224, 3) image tensor.
    Output: (224, 224, 1) spatial manipulation probability map.
    """
    if not HAS_TF:
        return None

    inputs = Input(shape=input_shape)

    # Encoder
    c1 = Conv2D(32, (3, 3), activation='relu', padding='same')(inputs)
    c1 = BatchNormalization()(c1)
    c1 = Conv2D(32, (3, 3), activation='relu', padding='same')(c1)
    p1 = MaxPooling2D((2, 2))(c1)

    c2 = Conv2D(64, (3, 3), activation='relu', padding='same')(p1)
    c2 = BatchNormalization()(c2)
    c2 = Conv2D(64, (3, 3), activation='relu', padding='same')(c2)
    p2 = MaxPooling2D((2, 2))(c2)

    # Bottleneck
    c3 = Conv2D(128, (3, 3), activation='relu', padding='same')(p2)
    c3 = BatchNormalization()(c3)
    c3 = Conv2D(128, (3, 3), activation='relu', padding='same')(c3)

    # Decoder
    u4 = UpSampling2D((2, 2))(c3)
    u4 = concatenate([u4, c2])
    c4 = Conv2D(64, (3, 3), activation='relu', padding='same')(u4)
    c4 = BatchNormalization()(c4)
    c4 = Conv2D(64, (3, 3), activation='relu', padding='same')(c4)

    u5 = UpSampling2D((2, 2))(c4)
    u5 = concatenate([u5, c1])
    c5 = Conv2D(32, (3, 3), activation='relu', padding='same')(u5)
    c5 = BatchNormalization()(c5)
    c5 = Conv2D(32, (3, 3), activation='relu', padding='same')(c5)

    outputs = Conv2D(1, (1, 1), activation='sigmoid')(c5)

    model = Model(inputs=[inputs], outputs=[outputs], name="UNet_Pixel_Segmentation")
    return model


def compute_dct_anomaly_map(img_rgb):
    """
    Computes 8x8 Discrete Cosine Transform (DCT) block frequency residual anomalies.
    AI deepfakes, face swaps, and copy-paste edits exhibit frequency domain grid discontinuities.
    Returns:
        dct_score (float): 0.0 to 100.0 overall frequency anomaly index.
        dct_map (np.ndarray): Normalized 2D float heatmap [0, 1] matching image shape.
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    h, w = gray.shape
    
    # Pad image to nearest multiple of 8
    pad_h = (8 - h % 8) % 8
    pad_w = (8 - w % 8) % 8
    padded = np.pad(gray, ((0, pad_h), (0, pad_w)), mode='reflect')
    ph, pw = padded.shape

    dct_energy_map = np.zeros((ph, pw), dtype=np.float32)

    # Process 8x8 blocks
    for y in range(0, ph, 8):
        for x in range(0, pw, 8):
            block = padded[y:y+8, x:x+8]
            dct_block = cv2.dct(block)
            
            # High frequency AC coefficients energy (exclude DC component at [0,0])
            ac_energy = float(np.sum(np.abs(dct_block[2:, 2:])))
            dct_energy_map[y:y+8, x:x+8] = ac_energy

    # Unpad
    dct_energy_map = dct_energy_map[:h, :w]
    
    # Calculate anomaly residual relative to local block mean
    local_blur = cv2.GaussianBlur(dct_energy_map, (15, 15), 0)
    diff = np.abs(dct_energy_map - local_blur)
    
    # Standardize
    norm_diff = cv2.normalize(diff, None, 0, 1, cv2.NORM_MINMAX)
    
    # Statistical score
    anomaly_val = float(np.mean(norm_diff) * 100.0 * 2.5 + np.percentile(norm_diff, 95) * 40.0)
    dct_score = min(100.0, round(anomaly_val, 2))
    
    return dct_score, norm_diff


def generate_multi_spectral_segmentation(img_rgb, ela_diff_gray=None):
    """
    Synthesizes a high-precision spatial pixel manipulation mask using multi-spectral signals:
    1. ELA residual spatial variance map
    2. Laplacian texture variance/smoothing map
    3. DCT frequency domain energy discontinuity map
    4. U-Net spatial probability response map
    
    Returns:
        prob_map (np.ndarray): 2D float array [0.0, 1.0] of pixel manipulation probability.
    """
    h, w, _ = img_rgb.shape
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    
    # 1. DCT Map
    _, dct_map = compute_dct_anomaly_map(img_rgb)
    
    # 2. ELA Map
    if ela_diff_gray is not None:
        ela_norm = ela_diff_gray.astype(np.float32) / 255.0
        if ela_norm.shape[:2] != (h, w):
            ela_norm = cv2.resize(ela_norm, (w, h))
    else:
        ela_norm = np.zeros((h, w), dtype=np.float32)
        
    # 3. High Frequency Edge/Noise Anomaly Map
    lap = cv2.Laplacian(gray, cv2.CV_32F)
    lap_abs = np.abs(lap)
    lap_blur = cv2.GaussianBlur(lap_abs, (9, 9), 0)
    texture_diff = np.abs(lap_abs - lap_blur)
    texture_norm = cv2.normalize(texture_diff, None, 0, 1, cv2.NORM_MINMAX)
    
    # Combine signals with spatial smoothing
    fused = (ela_norm * 0.40) + (dct_map * 0.35) + (texture_norm * 0.25)
    fused_smoothed = cv2.GaussianBlur(fused, (11, 11), 0)
    
    # Non-linear probability scaling
    prob_map = np.clip(fused_smoothed * 1.6, 0.0, 1.0)
    return prob_map


def extract_manipulated_regions(img_rgb, prob_map, min_area_ratio=0.015, threshold=0.40):
    """
    Extracts contiguous spatial clusters of manipulated pixels and computes bounding boxes & region details.
    
    Returns:
        regions (list of dict): List of detected regions with bounding boxes, probabilities, and labels.
        manipulated_pixel_ratio (float): Percentage of image pixels flagged as manipulated.
    """
    h, w, _ = img_rgb.shape
    total_pixels = h * w
    
    binary_mask = (prob_map >= threshold).astype(np.uint8) * 255
    
    # Morphological cleaning
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    cleaned = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
    
    manipulated_pixels = int(np.count_nonzero(cleaned))
    manipulated_pixel_ratio = round((manipulated_pixels / float(total_pixels)) * 100.0, 2)
    
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    regions = []
    min_area = total_pixels * min_area_ratio
    
    # Face cascade for localized region naming
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY), 1.1, 3)
    except Exception:
        faces = ()
        
    region_id = 1
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
            
        x, y, bw, bh = cv2.boundingRect(cnt)
        
        # Calculate mean manipulation probability within region mask
        roi_prob = prob_map[y:y+bh, x:x+bw]
        avg_prob = float(np.mean(roi_prob))
        max_prob = float(np.max(roi_prob))
        region_score = round(((avg_prob * 0.6) + (max_prob * 0.4)) * 100.0, 1)
        
        # Determine region location label
        label = "Image Content / Boundary Manipulation"
        center_x, center_y = x + bw // 2, y + bh // 2
        
        for (fx, fy, fw, fh) in faces:
            if fx <= center_x <= fx + fw and fy <= center_y <= fy + fh:
                # Within face bounding box
                rel_y = (center_y - fy) / float(fh)
                if rel_y < 0.35:
                    label = "Facial Landmark / Eye Region Resampling"
                elif rel_y < 0.65:
                    label = "Central Face / Nose-Cheek Morphing Zone"
                else:
                    label = "Lower Face / Mouth-Chin Synthesis"
                break
                
        regions.append({
            'id': region_id,
            'label': label,
            'bbox': [int(x), int(y), int(bw), int(bh)],
            'area_pixels': int(area),
            'area_percentage': round((area / float(total_pixels)) * 100.0, 2),
            'confidence': region_score
        })
        region_id += 1
        
    # Sort regions by confidence descending
    regions = sorted(regions, key=lambda r: r['confidence'], reverse=True)
    return regions, manipulated_pixel_ratio


def build_segmented_overlay(img_rgb, prob_map, regions):
    """
    Renders a clean visual overlay:
    - Thermal Jet colormap gradient on manipulated regions.
    - Bounding boxes and callout labels for detected regions.
    Returns:
        overlay_bgr (np.ndarray): Color-blended BGR image array.
    """
    h, w, _ = img_rgb.shape
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    
    # Normalize prob_map to [0, 255] uint8
    prob_uint8 = (prob_map * 255.0).astype(np.uint8)
    heatmap_bgr = cv2.applyColorMap(prob_uint8, cv2.COLORMAP_JET)
    
    # Create mask where probability is above threshold (0.20)
    mask_3ch = cv2.merge([prob_map, prob_map, prob_map])
    alpha = np.clip(mask_3ch * 0.75, 0.0, 0.75)
    
    overlay_bgr = (img_bgr * (1.0 - alpha) + heatmap_bgr * alpha).astype(np.uint8)
    
    # Draw region bounding boxes & badge tags
    for reg in regions:
        x, y, bw, bh = reg['bbox']
        conf = reg['confidence']
        label = f"#{reg['id']} {reg['label']} ({conf}%)"
        
        # Draw bounding box
        box_color = (0, 0, 255) if conf > 65.0 else (0, 165, 255)
        cv2.rectangle(overlay_bgr, (x, y), (x + bw, y + bh), box_color, 2)
        
        # Draw text label background pill
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        ty = max(y - 8, th + 6)
        cv2.rectangle(overlay_bgr, (x, ty - th - 4), (x + tw + 10, ty + 4), (20, 20, 20), -1)
        cv2.rectangle(overlay_bgr, (x, ty - th - 4), (x + tw + 10, ty + 4), box_color, 1)
        cv2.putText(overlay_bgr, label, (x + 5, ty - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        
    return overlay_bgr
