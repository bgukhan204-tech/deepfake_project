import os
import io
import gc
import cv2
import math
import tempfile
import traceback
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify, render_template
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import tensorflow.lite as tflite
    except ImportError:
        tflite = None

app = Flask(__name__)

# Face detection cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# TFLite Model setup
MODEL_PATH = "model/deepfake_model.tflite"
interpreter = None
input_details = None
output_details = None

if os.path.exists(MODEL_PATH):
    try:
        if tflite:
            # Load from buffer to avoid mmap issues on some systems
            with open(MODEL_PATH, 'rb') as f:
                model_content = f.read()
            interpreter = tflite.Interpreter(model_content=model_content)
            interpreter.allocate_tensors()
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            print(f"✅ TFLite model loaded from {MODEL_PATH}")
        else:
            print("⚠️ tflite-runtime or tensorflow not installed.")
    except Exception as e:
        print(f"⚠️ Model load failed: {e}")
else:
    print(f"⚠️ Model not found at: {MODEL_PATH}")


# ─────────────────────────────────────────────────────────
#  ELA — Error Level Analysis
#  Detects pixel manipulation & AI-generated image artifacts
# ─────────────────────────────────────────────────────────
def compute_ela_score(img_pil, quality=90):
    """
    Resaves the image at a given JPEG quality and measures difference.
    Untouched regions compress cleanly → small diff.
    Edited / AI-generated regions have inconsistent compression → large diff.
    Returns: (manipulation_score 0-100, raw_mean_diff float)
    """
    buffer = io.BytesIO()
    img_rgb = img_pil.convert('RGB')
    img_rgb.save(buffer, format='JPEG', quality=quality)
    buffer.seek(0)
    ela_img = Image.open(buffer).convert('RGB')

    orig = np.array(img_rgb, dtype=np.float32)
    ela  = np.array(ela_img, dtype=np.float32)
    diff = np.abs(orig - ela)

    mean_diff = float(np.mean(diff))
    # Empirical calibration: typical real photo = 1–5, AI/edited = 6–20+
    # Cap at 100
    manipulation_score = min(100.0, (mean_diff / 18.0) * 100)
    return round(manipulation_score, 2), round(mean_diff, 4)


# ─────────────────────────────────────────────────────────
#  Model inference on an RGB numpy frame
# ─────────────────────────────────────────────────────────
def run_model(img_array):
    """
    Detects face, crops if found, resizes to 224×224, runs TFLite model.
    Returns raw prediction float (0=fake, 1=real), or None if no model.
    """
    if interpreter is None:
        return None

    gray  = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=4, minSize=(50, 50))

    if len(faces) > 0:
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        px, py = int(w * 0.3), int(h * 0.3)
        y1, y2 = max(0, y - py), min(img_array.shape[0], y + h + py)
        x1, x2 = max(0, x - px), min(img_array.shape[1], x + w + px)
        crop = img_array[y1:y2, x1:x2]
    else:
        crop = img_array

    inp_img = cv2.resize(crop, (224, 224)).astype(np.float32) / 255.0
    inp_img = np.expand_dims(inp_img, axis=0)
    
    # TFLite Inference
    interpreter.set_tensor(input_details[0]['index'], inp_img)
    interpreter.invoke()
    pred = float(interpreter.get_tensor(output_details[0]['index'])[0][0])
    
    return pred


# ─────────────────────────────────────────────────────────
#  Combined scoring
# ─────────────────────────────────────────────────────────
def combine_scores(model_pred, ela_score):
    """
    model_pred : raw float (0=fake, 1=real) or None
    ela_score  : 0-100 manipulation score
    Returns (authentic_pct, manipulated_pct, status, confidence, reason)
    """
    model_fake = (1.0 - model_pred) * 100 if model_pred is not None else 0
    
    if model_pred is not None:
        # Weighted: 55% model (deepfake), 45% ELA (AI / edit detection)
        combined_fake = (model_fake * 0.55) + (ela_score * 0.45)
    else:
        combined_fake = ela_score

    combined_fake = round(min(100.0, max(0.0, combined_fake)), 2)
    combined_real = round(100.0 - combined_fake, 2)
    
    status = 'REAL' if combined_real > combined_fake else 'MANIPULATED'
    confidence = round(max(combined_real, combined_fake), 2)
    
    # Generate Reason
    if status == 'REAL':
        reason = "No significant facial artifacts or pixel-level manipulation detected. The content appears genuine."
    else:
        if (model_fake > 50 and ela_score > 40):
            reason = "High risk: Facial inconsistencies combined with structural pixel manipulation detected."
        elif model_fake > 50:
            reason = "Facial anomalies and deepfake artifacts detected by the Deep Learning model."
        elif ela_score > 25:
            reason = "Error Level Analysis detected pixel inconsistencies typical of AI-generation or software edits."
        else:
            reason = "Minor anomalies detected that exceed the baseline for authentic content."
            
    return combined_real, combined_fake, status, confidence, reason


# ─────────────────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'})

    try:
        raw = file.read()
        np_arr  = np.frombuffer(raw, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            return jsonify({'error': 'Could not decode image. Please upload a valid image file.'})

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)

        # ELA
        ela_score, ela_raw = compute_ela_score(img_pil)

        # Model
        model_pred = run_model(img_rgb)
        model_real  = round(model_pred * 100, 2)          if model_pred is not None else None
        model_fake  = round((1 - model_pred) * 100, 2)    if model_pred is not None else None

        # Combine
        auth, manip, status, conf, reason = combine_scores(model_pred, ela_score)

        gc.collect()
        return jsonify({
            'success': True,
            'status': status,
            'reason': reason,
            'authentic_score': auth,
            'manipulated_score': manip,
            'confidence': conf,
            'ela_score': ela_score,
            'ela_raw': ela_raw,
            'model_real_score': model_real,
            'model_fake_score': model_fake,
            'model_available': interpreter is not None
        })

    except Exception as e:
        return jsonify({'error': f'Image analysis failed: {str(e)}', 'trace': traceback.format_exc()})


@app.route("/predict_video", methods=["POST"])
def predict_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'})

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        return jsonify({'error': 'Unsupported format. Upload MP4, AVI, MOV, MKV or WEBM.'})

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        cap         = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps          = cap.get(cv2.CAP_PROP_FPS) or 25
        duration     = round(total_frames / fps, 1)

        # Sample evenly up to 12 frames
        MAX_SAMPLES = 12
        step = max(1, total_frames // MAX_SAMPLES)

        frame_results = []
        ela_list, model_list = [], []

        for frame_idx in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue

            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)

            ela_score, _ = compute_ela_score(img_pil)
            model_pred    = run_model(img_rgb)

            ela_list.append(ela_score)
            if model_pred is not None:
                model_list.append(model_pred)

            frame_results.append({
                'timestamp': round(frame_idx / fps, 1),
                'ela_score': round(ela_score, 1),
                'model_fake_score': round((1 - model_pred) * 100, 1) if model_pred is not None else None
            })

            if len(frame_results) >= MAX_SAMPLES:
                break

        cap.release()

        if not ela_list:
            return jsonify({'error': 'Could not extract frames from video.'})

        avg_ela        = round(sum(ela_list) / len(ela_list), 2)
        avg_model_pred = sum(model_list) / len(model_list) if model_list else None
        model_real     = round(avg_model_pred * 100, 2)           if avg_model_pred is not None else None
        model_fake     = round((1 - avg_model_pred) * 100, 2)     if avg_model_pred is not None else None

        auth, manip, status, conf, reason = combine_scores(avg_model_pred, avg_ela)

        gc.collect()
        return jsonify({
            'success': True,
            'status': status,
            'reason': reason,
            'authentic_score': auth,
            'manipulated_score': manip,
            'confidence': conf,
            'ela_score': avg_ela,
            'model_real_score': model_real,
            'model_fake_score': model_fake,
            'frames_analyzed': len(frame_results),
            'total_frames': total_frames,
            'duration': duration,
            'frame_results': frame_results,
            'model_available': interpreter is not None
        })

    except Exception as e:
        return jsonify({'error': f'Video analysis failed: {str(e)}', 'trace': traceback.format_exc()})

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
