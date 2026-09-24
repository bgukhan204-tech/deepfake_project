import io
import cv2
import base64
import numpy as np
from PIL import Image

def compute_ela_score_and_heatmap(img_pil, quality=90):
    """
    Performs Error Level Analysis (ELA) to inspect pixel compression anomalies.
    Returns: ela_score, mean_diff, heatmap_base64, diff_gray
    """
    buffer = io.BytesIO()
    img_rgb = img_pil.convert('RGB')
    img_rgb.save(buffer, format='JPEG', quality=quality)
    buffer.seek(0)
    ela_img = Image.open(buffer).convert('RGB')

    orig = np.array(img_rgb, dtype=np.float32)
    ela = np.array(ela_img, dtype=np.float32)
    diff = np.abs(orig - ela)

    mean_diff = float(np.mean(diff))
    max_diff = float(np.percentile(diff, 98))
    std_diff = float(np.std(diff))

    ela_manipulation_score = min(100.0, (mean_diff * 4.0) + (std_diff * 3.2) + (max_diff * 0.35))

    diff_gray = cv2.cvtColor(diff.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    diff_amplified = cv2.normalize(diff_gray, None, 0, 255, cv2.NORM_MINMAX)
    heatmap_bgr = cv2.applyColorMap(diff_amplified, cv2.COLORMAP_JET)

    orig_bgr = cv2.cvtColor(np.array(img_rgb), cv2.COLOR_RGB2BGR)
    overlay_bgr = cv2.addWeighted(orig_bgr, 0.40, heatmap_bgr, 0.60, 0)

    _, heatmap_encoded = cv2.imencode('.jpg', overlay_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    heatmap_base64 = "data:image/jpeg;base64," + base64.b64encode(heatmap_encoded).decode('utf-8')

    return round(ela_manipulation_score, 2), round(mean_diff, 4), heatmap_base64, diff_gray

def compute_texture_analysis(img_array):
    """
    Measures High-Frequency Sensor Noise & Blur/Smoothing Artifacts via Laplacian variance.
    Returns: smoothing_score, laplacian_variance
    """
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if lap_var < 45.0:
        smoothing_score = min(100.0, (45.0 - lap_var) * 2.2)
    else:
        smoothing_score = 0.0

    return round(smoothing_score, 2), round(lap_var, 2)
