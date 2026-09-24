import os
import io
import gc
import cv2
import base64
import sqlite3
import hashlib
import tempfile
import traceback
import numpy as np
from PIL import Image
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect

# Detect environment and load TFLite interpreter
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import tensorflow.lite as tflite
    except ImportError:
        tflite = None

app = Flask(__name__)
app.secret_key = "deepshield_sec_key_2026_super_secret"
DB_PATH = "deepshield.db"

@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        return response

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

# Load Face Detection Cascade safely
try:
    if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    else:
        face_cascade = None
except Exception:
    face_cascade = None

# Global interpreter and details
interpreter = None
input_details = None
output_details = None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            verdict TEXT NOT NULL,
            confidence REAL NOT NULL,
            authentic_score REAL NOT NULL,
            manipulated_score REAL NOT NULL,
            ela_score REAL NOT NULL,
            reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def load_model():
    global interpreter, input_details, output_details
    if interpreter is not None:
        return interpreter, input_details, output_details
        
    test_paths = ["model/deepfake_model.tflite", "deepfake_model.tflite"]
    model_path = None
    
    for p in test_paths:
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            model_path = p
            break
            
    if model_path and tflite:
        try:
            size_mb = os.path.getsize(model_path) / (1024 * 1024)
            print(f"Loading TFLite model from {model_path} ({size_mb:.2f} MB)...")
            with open(model_path, 'rb') as f:
                model_content = f.read()
                
            interpreter = tflite.Interpreter(model_content=model_content)
            interpreter.allocate_tensors()
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            print("[OK] TFLite model loaded successfully.")
        except Exception as e:
            print(f"[WARNING] Model initialization error: {e}")
            interpreter = None
    else:
        print("[NOTE] TFLite model file not found or runtime unavailable. ELA & Texture engines active.")

    return interpreter, input_details, output_details

load_model()


def compute_ela_score_and_heatmap(img_pil, quality=90):
    buffer = io.BytesIO()
    img_rgb = img_pil.convert('RGB')
    img_rgb.save(buffer, format='JPEG', quality=quality)
    buffer.seek(0)
    ela_img = Image.open(buffer).convert('RGB')

    orig = np.array(img_rgb, dtype=np.float32)
    ela  = np.array(ela_img, dtype=np.float32)
    diff = np.abs(orig - ela)

    mean_diff = float(np.mean(diff))
    max_diff  = float(np.percentile(diff, 98))
    std_diff  = float(np.std(diff))

    ela_manipulation_score = min(100.0, (mean_diff * 4.0) + (std_diff * 3.2) + (max_diff * 0.35))
    
    diff_gray = cv2.cvtColor(diff.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    diff_amplified = cv2.normalize(diff_gray, None, 0, 255, cv2.NORM_MINMAX)
    heatmap_bgr = cv2.applyColorMap(diff_amplified, cv2.COLORMAP_JET)
    
    orig_bgr = cv2.cvtColor(np.array(img_rgb), cv2.COLOR_RGB2BGR)
    overlay_bgr = cv2.addWeighted(orig_bgr, 0.40, heatmap_bgr, 0.60, 0)
    
    _, heatmap_encoded = cv2.imencode('.jpg', overlay_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    heatmap_base64 = "data:image/jpeg;base64," + base64.b64encode(heatmap_encoded).decode('utf-8')

    return round(ela_manipulation_score, 2), round(mean_diff, 4), heatmap_base64


def compute_texture_analysis(img_array):
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    if lap_var < 45.0:
        smoothing_score = min(100.0, (45.0 - lap_var) * 2.2)
    else:
        smoothing_score = 0.0
        
    return round(smoothing_score, 2), round(lap_var, 2)


def run_model(img_array):
    interp, inp, out = load_model()
    if interp is None:
        return None

    h_img, w_img, _ = img_array.shape
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    gray_eq = cv2.equalizeHist(gray)
    
    faces = ()
    if face_cascade is not None:
        try:
            faces = face_cascade.detectMultiScale(gray_eq, scaleFactor=1.08, minNeighbors=3, minSize=(40, 40))
            if len(faces) == 0:
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=3, minSize=(40, 40))
        except Exception:
            faces = ()

    if len(faces) > 0:
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        center_x, center_y = x + w // 2, y + h // 2
        side = int(max(w, h) * 1.4)
        
        y1 = max(0, center_y - side // 2)
        y2 = min(h_img, center_y + side // 2)
        x1 = max(0, center_x - side // 2)
        x2 = min(w_img, center_x + side // 2)
        crop = img_array[y1:y2, x1:x2]
    else:
        min_side = min(h_img, w_img)
        cy, cx = h_img // 2, w_img // 2
        y1 = max(0, cy - min_side // 2)
        y2 = min(h_img, cy + min_side // 2)
        x1 = max(0, cx - min_side // 2)
        x2 = min(w_img, cx + min_side // 2)
        crop = img_array[y1:y2, x1:x2]

    inp_img = cv2.resize(crop, (224, 224)).astype(np.float32) / 255.0
    inp_img = np.expand_dims(inp_img, axis=0)
    
    interp.set_tensor(inp[0]['index'], inp_img)
    interp.invoke()
    pred = float(interp.get_tensor(out[0]['index'])[0][0])
    
    return pred


def combine_scores(model_pred, ela_score, texture_score=0.0):
    if model_pred is not None:
        model_real = round(model_pred * 100.0, 2)
        model_fake = round(100.0 - model_real, 2)
        
        combined_fake = (model_fake * 0.50) + (ela_score * 0.35) + (texture_score * 0.15)
        
        max_signal = max(model_fake, ela_score, texture_score)
        if max_signal > 60.0:
            combined_fake = max(combined_fake, max_signal)
    else:
        model_real = None
        model_fake = None
        combined_fake = (ela_score * 0.70) + (texture_score * 0.30)

    combined_fake = round(min(100.0, max(0.0, combined_fake)), 2)
    combined_real = round(100.0 - combined_fake, 2)
    
    status = 'REAL' if combined_real >= 50.0 else 'MANIPULATED'
    confidence = round(max(combined_real, combined_fake), 2)
    
    if status == 'REAL':
        reason = "Pristine sensor noise, clean frequency compression, and consistent facial geometry detected. Content is genuine."
    else:
        if ela_score > 35 and (model_fake or 0) > 40:
            reason = "High Risk: AI generation / facial morphing combined with pixel compression edits detected."
        elif (model_fake or 0) > 50:
            reason = "AI Deepfake / Facial Morphing anomalies detected by Neural Engine."
        elif ela_score > 30:
            reason = "Pixel-level manipulation & AI editing artifacts detected by Error Level Analysis."
        else:
            reason = "Artificial smoothing or frequency noise inconsistencies detected."
            
    return combined_real, combined_fake, status, confidence, reason, model_real, model_fake


def save_scan_record(filename, file_type, status, confidence, auth_score, manip_score, ela_score, reason):
    try:
        user_id = session.get('user_id')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scans (user_id, filename, file_type, verdict, confidence, authentic_score, manipulated_score, ela_score, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, filename, file_type, status, confidence, auth_score, manip_score, ela_score, reason))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving scan history: {e}")


from flask import send_from_directory

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    # Do not capture API routes or documentation
    if path.startswith("api/") or path.startswith("predict") or path == "health":
        return jsonify({'error': 'Not found'}), 404
        
    dist_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
    if path != "" and os.path.exists(os.path.join(dist_dir, path)):
        return send_from_directory(dist_dir, path)
    elif os.path.exists(os.path.join(dist_dir, "index.html")):
        return send_from_directory(dist_dir, "index.html")
    else:
        return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "OK", "model_loaded": interpreter is not None}), 200

@app.route("/api/docs")
def api_docs():
    return render_template("swagger.html")

@app.route("/api/v1/openapi.json")
def openapi_spec():
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "DeepShield AI Forensic REST API",
            "version": "1.0.0",
            "description": "API endpoints for Deepfake facial manipulation detection, Error Level Analysis (ELA), video frame timeline breakdown, and batch scan processing."
        },
        "paths": {
            "/predict": {
                "post": {
                    "summary": "Analyze single image or webcam snapshot for deepfake anomalies",
                    "requestBody": {
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {"type": "string", "format": "binary"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Successful detection output with ELA heatmap and confidence score."}
                    }
                }
            },
            "/predict_video": {
                "post": {
                    "summary": "Analyze video file for frame-by-frame deepfake timeline",
                    "requestBody": {
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {"type": "string", "format": "binary"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Video frame timeline analysis output."}
                    }
                }
            }
        }
    }
    return jsonify(spec)

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pwd_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        session['user_id'] = user_id
        session['username'] = username
        return jsonify({'success': True, 'username': username})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE username = ? AND password_hash = ?", (username, pwd_hash))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_id'] = user[0]
        session['username'] = user[1]
        return jsonify({'success': True, 'username': user[1]})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    session.clear()
    return jsonify({'success': True})

@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'username': session.get('username')})
    return jsonify({'authenticated': False})

@app.route("/api/history", methods=["GET"])
def get_history():
    user_id = session.get('user_id')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if user_id:
        cursor.execute("SELECT id, filename, file_type, verdict, confidence, authentic_score, manipulated_score, ela_score, reason, timestamp FROM scans WHERE user_id = ? ORDER BY timestamp DESC LIMIT 50", (user_id,))
    else:
        cursor.execute("SELECT id, filename, file_type, verdict, confidence, authentic_score, manipulated_score, ela_score, reason, timestamp FROM scans ORDER BY timestamp DESC LIMIT 50")

    rows = cursor.fetchall()
    conn.close()

    history = []
    for r in rows:
        history.append({
            'id': r[0],
            'filename': r[1],
            'file_type': r[2],
            'verdict': r[3],
            'confidence': r[4],
            'authentic_score': r[5],
            'manipulated_score': r[6],
            'ela_score': r[7],
            'reason': r[8],
            'timestamp': r[9]
        })
    return jsonify({'history': history})

@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM scans")
    total_scans = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scans WHERE verdict = 'REAL'")
    real_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scans WHERE verdict = 'MANIPULATED'")
    fake_count = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(confidence) FROM scans")
    avg_conf = cursor.fetchone()[0] or 0.0

    conn.close()

    return jsonify({
        'total_scans': total_scans,
        'real_scans': real_count,
        'fake_scans': fake_count,
        'avg_confidence': round(avg_conf, 2)
    })

@app.route("/predict", methods=["POST"])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    try:
        raw = file.read()
        np_arr  = np.frombuffer(raw, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            return jsonify({'error': 'Invalid image file'}), 400

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)

        ela_score, ela_raw, heatmap_base64 = compute_ela_score_and_heatmap(img_pil)
        texture_score, lap_var = compute_texture_analysis(img_rgb)
        model_pred = run_model(img_rgb)

        auth, manip, status, conf, reason, model_real, model_fake = combine_scores(model_pred, ela_score, texture_score)
        save_scan_record(file.filename, 'image', status, conf, auth, manip, ela_score, reason)

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
            'heatmap_base64': heatmap_base64,
            'texture_score': texture_score,
            'laplacian_var': lap_var,
            'model_real_score': model_real,
            'model_fake_score': model_fake,
            'model_available': interpreter is not None
        })

    except Exception as e:
        return jsonify({'error': f'Image analysis failed: {str(e)}', 'trace': traceback.format_exc()}), 500

@app.route("/predict_batch", methods=["POST"])
@app.route("/api/batch_predict", methods=["POST"])
def batch_predict():
    files = request.files.getlist('files')
    if not files or len(files) == 0:
        return jsonify({'error': 'No files uploaded'}), 400

    results = []
    for file in files:
        if not file.filename:
            continue
        try:
            raw = file.read()
            np_arr  = np.frombuffer(raw, np.uint8)
            img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img_bgr is None:
                continue

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)

            ela_score, ela_raw, heatmap_base64 = compute_ela_score_and_heatmap(img_pil)
            texture_score, lap_var = compute_texture_analysis(img_rgb)
            model_pred = run_model(img_rgb)

            auth, manip, status, conf, reason, model_real, model_fake = combine_scores(model_pred, ela_score, texture_score)
            save_scan_record(file.filename, 'batch_image', status, conf, auth, manip, ela_score, reason)

            results.append({
                'filename': file.filename,
                'status': status,
                'confidence': conf,
                'authentic_score': auth,
                'manipulated_score': manip,
                'ela_score': ela_score,
                'heatmap_base64': heatmap_base64
            })
        except Exception:
            pass

    gc.collect()
    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route("/predict_video", methods=["POST"])
def predict_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No video file uploaded'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        return jsonify({'error': 'Unsupported video format. Use MP4, MOV, AVI, or WEBM.'}), 400

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        cap          = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps          = cap.get(cv2.CAP_PROP_FPS) or 25
        duration     = round(total_frames / fps, 1) if fps > 0 else 0

        MAX_SAMPLES = 12
        step = max(1, total_frames // MAX_SAMPLES) if total_frames > 0 else 1

        frame_results = []
        ela_list, model_list = [], []

        for frame_idx in range(0, max(1, total_frames), step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue

            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)

            ela_score, _, _ = compute_ela_score_and_heatmap(img_pil)
            model_pred      = run_model(img_rgb)

            ela_list.append(ela_score)
            if model_pred is not None:
                model_list.append(model_pred)

            frame_fake_pct = round((1.0 - model_pred) * 100.0, 1) if model_pred is not None else ela_score

            frame_results.append({
                'timestamp': round(frame_idx / fps, 1) if fps > 0 else 0,
                'ela_score': round(ela_score, 1),
                'fake_score': frame_fake_pct,
                'is_fake': frame_fake_pct > 50.0
            })

            if len(frame_results) >= MAX_SAMPLES:
                break

        cap.release()

        if not ela_list:
            return jsonify({'error': 'Could not extract frames from video.'}), 400

        avg_ela        = round(sum(ela_list) / len(ela_list), 2)
        avg_model_pred = sum(model_list) / len(model_list) if model_list else None

        auth, manip, status, conf, reason, model_real, model_fake = combine_scores(avg_model_pred, avg_ela, 0.0)
        save_scan_record(file.filename, 'video', status, conf, auth, manip, avg_ela, reason)

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
        return jsonify({'error': f'Video analysis failed: {str(e)}', 'trace': traceback.format_exc()}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=port)
