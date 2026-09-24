import os
import cv2
import io
import base64
import numpy as np
from PIL import Image
from services.model_service import model_service
from services.forensic_analyzer import compute_ela_score_and_heatmap
from services.temporal_analyzer import compute_temporal_analysis

DEFAULT_MAX_SAMPLES = 12

def analyze_video_file(video_path, max_samples=DEFAULT_MAX_SAMPLES):
    """
    Analyzes video using configurable frame sampling, GenConViT frame inference,
    temporal inconsistency scoring, and top suspicious frames extraction.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open video file for processing")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    duration = round(total_frames / fps, 1) if fps > 0 else 0.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    resolution = f"{width} x {height} px" if width > 0 else "1080p Standard"

    step = max(1, total_frames // max_samples) if total_frames > 0 else 1

    frame_results = []
    suspicious_candidates = []

    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    for frame_idx in range(0, max(1, total_frames), step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        timestamp = round(frame_idx / fps, 1) if fps > 0 else 0.0

        # Face detection check per frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
        has_face = len(faces) > 0

        # GenConViT / Model prediction per frame
        pred_res = model_service.predict_image(img_rgb)
        fake_pct = round(pred_res['fake_score'] * 100.0, 1)

        # ELA score per frame
        ela_score, _, _, _ = compute_ela_score_and_heatmap(img_pil)

        frame_data = {
            'frame_number': frame_idx,
            'timestamp': timestamp,
            'deepfake_score': round(fake_pct / 100.0, 2),
            'fake_score': fake_pct,
            'classification': "fake" if fake_pct > 50.0 else "authentic",
            'is_fake': fake_pct > 50.0,
            'face_detected': has_face,
            'ela_score': ela_score
        }
        frame_results.append(frame_data)

        # Thumbnail extraction for suspicious frames
        thumb = img_pil.copy()
        thumb.thumbnail((160, 120))
        buf = io.BytesIO()
        thumb.save(buf, format="JPEG", quality=75)
        thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')

        suspicious_candidates.append({
            'frame_number': frame_idx,
            'timestamp': timestamp,
            'score': round(fake_pct, 1),
            'thumbnail': thumb_b64
        })

        if len(frame_results) >= max_samples:
            break

    cap.release()

    if not frame_results:
        raise ValueError("Could not extract valid frames from video")

    # Temporal Inconsistency Analysis
    temporal_score, temporal_details = compute_temporal_analysis(frame_results)

    # Average Scores
    avg_fake = float(np.mean([f['fake_score'] for f in frame_results]))
    avg_ela = float(np.mean([f['ela_score'] for f in frame_results]))

    ai_detection_score = round(avg_fake, 1)
    forensic_score = round(avg_ela, 1)

    # Combined Video Score (AI + Temporal + Forensic)
    manipulated_score = round(min(100.0, (ai_detection_score * 0.55) + (temporal_score * 0.25) + (forensic_score * 0.20)), 1)
    authentic_score = round(100.0 - manipulated_score, 1)
    confidence = round(max(authentic_score, manipulated_score), 1)

    classification = "LIKELY_FAKE" if manipulated_score > 50.0 else "AUTHENTIC"
    verdict = "Manipulated Video" if manipulated_score > 50.0 else "Authentic Video"

    # Top Suspicious Frames sorted by score descending
    sorted_suspicious = sorted(suspicious_candidates, key=lambda x: x['score'], reverse=True)[:5]

    return {
        'success': True,
        'media_type': 'video',
        'classification': classification,
        'verdict': verdict,
        'confidence': confidence,
        'authentic_score': authentic_score,
        'manipulated_score': manipulated_score,
        'ai_detection_score': ai_detection_score,
        'temporal_score': temporal_score,
        'forensic_score': forensic_score,
        'ela_score': round(avg_ela, 1),
        'duration': duration,
        'total_frames': total_frames,
        'frames_analyzed': len(frame_results),
        'resolution': resolution,
        'temporal_details': temporal_details,
        'frame_results': frame_results,
        'suspicious_frames': sorted_suspicious
    }
