import cv2
import numpy as np
from PIL import Image
from services.model_service import model_service
from services.forensic_analyzer import compute_ela_score_and_heatmap, compute_texture_analysis

def analyze_image_bytes(raw_bytes, filename="image.jpg"):
    """
    Executes image preprocessing, face detection, GenConViT + Fallback inference,
    Error Level Analysis, and texture analysis.
    Returns structured JSON result dictionary.
    """
    np_arr = np.frombuffer(raw_bytes, np.uint8)
    img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        raise ValueError("Invalid or corrupt image format")

    height, width, _ = img_bgr.shape
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)

    # 1. Face Detection
    face_detected = False
    face_count = 0
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
        face_count = len(faces)
        face_detected = face_count > 0
    except Exception:
        face_detected = False

    # 2. GenConViT + Model Inference
    pred_res = model_service.predict_image(img_rgb)
    model_real = pred_res['real_score']
    model_fake = pred_res['fake_score']
    model_name = pred_res['model_used']

    # 3. Forensic Analysis (ELA & Texture)
    ela_score, ela_mean, heatmap_base64, _ = compute_ela_score_and_heatmap(img_pil)
    smoothing_score, lap_var = compute_texture_analysis(img_rgb)

    # 4. Score Aggregation
    ai_detection_score = round(model_fake * 100.0, 1)
    forensic_score = round(min(100.0, (ela_score * 0.6) + (smoothing_score * 0.4)), 1)
    
    # Combined Confidence Calculation
    manipulated_score = round(min(100.0, (ai_detection_score * 0.65) + (forensic_score * 0.35)), 1)
    authentic_score = round(100.0 - manipulated_score, 1)
    
    confidence = round(max(authentic_score, manipulated_score), 1)
    classification = "LIKELY_FAKE" if manipulated_score > 50.0 else "AUTHENTIC"
    verdict = "Manipulated Image" if manipulated_score > 50.0 else "Authentic Image"

    file_size_mb = len(raw_bytes) / (1024 * 1024)
    file_size_str = f"{file_size_mb:.2f} MB" if file_size_mb >= 1.0 else f"{round(len(raw_bytes)/1024, 1)} KB"

    return {
        'success': True,
        'classification': classification,
        'verdict': verdict,
        'confidence': confidence,
        'authentic_score': authentic_score,
        'manipulated_score': manipulated_score,
        'ai_detection_score': ai_detection_score,
        'forensic_score': forensic_score,
        'ela_score': ela_score,
        'texture_score': smoothing_score,
        'laplacian_var': lap_var,
        'heatmap_base64': heatmap_base64,
        'model_used': model_name,
        'resolution': f"{width} x {height} px",
        'file_size': file_size_str,
        'face_detection': {
            'face_detected': face_detected,
            'face_count': face_count
        }
    }
