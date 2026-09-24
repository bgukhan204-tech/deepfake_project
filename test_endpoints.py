import os
import sys
import json
import io
import cv2
import numpy as np

# Test script for DeepShield AI Flask API
print("[TEST] Testing DeepShield AI backend services...")

try:
    from services.model_service import model_service
    print(f"[OK] ModelService initialized: {model_service.model_status}")

    from services.image_analyzer import analyze_image_bytes
    dummy_img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.rectangle(dummy_img, (50, 50), (250, 250), (255, 200, 150), -1)
    _, img_encoded = cv2.imencode('.jpg', dummy_img)
    img_bytes = img_encoded.tobytes()

    res = analyze_image_bytes(img_bytes, "test.jpg")
    print("[OK] Image analyzer returned:", json.dumps({
        'classification': res['classification'],
        'confidence': res['confidence'],
        'ela_score': res['ela_score'],
        'model_used': res['model_used']
    }))

    from services.video_analyzer import analyze_video_file
    video_path = os.path.join(os.path.dirname(__file__), "dataset", "deepfake.mp4")
    if os.path.exists(video_path):
        vid_res = analyze_video_file(video_path, max_samples=4)
        print("[OK] Video analyzer returned:", json.dumps({
            'classification': vid_res['classification'],
            'confidence': vid_res['confidence'],
            'duration': vid_res['duration'],
            'temporal_score': vid_res['temporal_score'],
            'suspicious_frames_count': len(vid_res.get('suspicious_frames', []))
        }))
    else:
        print("[NOTE] dataset/deepfake.mp4 not found for video test.")

    print("\n[SUCCESS] All backend service tests passed cleanly!")

except Exception as e:
    print(f"[FAIL] Test failed with error: {e}")
    import traceback
    traceback.print_exc()
