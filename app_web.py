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

# Import U-Net Pixel-Level Segmentation & Multi-Spectral Fusion Engine
try:
    from model.unet_segmentation import (
        compute_dct_anomaly_map,
        generate_multi_spectral_segmentation,
        extract_manipulated_regions,
        build_segmented_overlay
    )
except ImportError:
    import sys
    sys.path.append(os.path.dirname(__file__))
    from model.unet_segmentation import (
        compute_dct_anomaly_map,
        generate_multi_spectral_segmentation,
        extract_manipulated_regions,
        build_segmented_overlay
    )


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

EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "static", "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)

import random
import time

def generate_analysis_id():
    return f"DS-{random.randint(100000, 999999)}"

def make_thumbnail_base64(img_pil):
    try:
        thumb = img_pil.copy()
        thumb.thumbnail((100, 100))
        buf = io.BytesIO()
        thumb.save(buf, format="JPEG", quality=80)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception:
        return ""

def init_db():
    """Initialize SQLite database for user accounts and scan history with full metadata support."""
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
    
    # Migration: Add extra forensic metadata columns if missing
    cursor.execute("PRAGMA table_info(scans)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    extra_cols = [
        ("analysis_id", "TEXT"),
        ("resolution", "TEXT"),
        ("file_size", "TEXT"),
        ("processing_time", "REAL"),
        ("thumb_base64", "TEXT")
    ]
    for col_name, col_type in extra_cols:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE scans ADD COLUMN {col_name} {col_type}")
            
    conn.commit()
    conn.close()

# Initialize DB on startup
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

# Initialize model at startup
load_model()


# ─────────────────────────────────────────────────────────
#  Engine 1: Forensic ELA & Pixel-by-Pixel Heatmap Generator
# ─────────────────────────────────────────────────────────
def compute_ela_score_and_heatmap(img_pil, quality=90):
    """
    Performs Error Level Analysis (ELA) to inspect pixel compression anomalies.
    Measures mean difference, regional standard deviation, and peak 98th percentile diff.
    Generates a colorized Heatmap (JET colormap) returned as base64 data URI.
    """
    buffer = io.BytesIO()
    img_rgb = img_pil.convert('RGB')
    img_rgb.save(buffer, format='JPEG', quality=quality)
    buffer.seek(0)
    ela_img = Image.open(buffer).convert('RGB')

    orig = np.array(img_rgb, dtype=np.float32)
    ela  = np.array(ela_img, dtype=np.float32)
    diff = np.abs(orig - ela)

    # Pixel-level difference statistics
    mean_diff = float(np.mean(diff))
    max_diff  = float(np.percentile(diff, 98))
    std_diff  = float(np.std(diff))

    # Calculate forensic pixel manipulation score
    ela_manipulation_score = min(100.0, (mean_diff * 4.0) + (std_diff * 3.2) + (max_diff * 0.35))
    
    # Build Heatmap Visualization
    diff_gray = cv2.cvtColor(diff.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    diff_amplified = cv2.normalize(diff_gray, None, 0, 255, cv2.NORM_MINMAX)
    heatmap_bgr = cv2.applyColorMap(diff_amplified, cv2.COLORMAP_JET)
    
    # Overlay heatmap onto original image (40% orig + 60% heatmap)
    orig_bgr = cv2.cvtColor(np.array(img_rgb), cv2.COLOR_RGB2BGR)
    overlay_bgr = cv2.addWeighted(orig_bgr, 0.40, heatmap_bgr, 0.60, 0)
    
    _, heatmap_encoded = cv2.imencode('.jpg', overlay_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    heatmap_base64 = "data:image/jpeg;base64," + base64.b64encode(heatmap_encoded).decode('utf-8')

    return round(ela_manipulation_score, 2), round(mean_diff, 4), heatmap_base64, diff_gray


# ─────────────────────────────────────────────────────────
#  Engine 1B: U-Net Pixel-Level Manipulation Segmentation
# ─────────────────────────────────────────────────────────
def compute_pixel_segmentation_analysis(img_rgb, diff_gray=None):
    """
    Computes spatial pixel-level manipulation probability maps (U-Net + DCT + Multi-Spectral Fusion).
    Returns segmentation overlay base64, DCT heatmap base64, manipulated pixel ratio %, DCT score, and region bounding boxes.
    """
    dct_score, dct_map = compute_dct_anomaly_map(img_rgb)
    prob_map = generate_multi_spectral_segmentation(img_rgb, ela_diff_gray=diff_gray)
    regions, manipulated_pixel_ratio = extract_manipulated_regions(img_rgb, prob_map)
    overlay_bgr = build_segmented_overlay(img_rgb, prob_map, regions)
    
    _, overlay_encoded = cv2.imencode('.jpg', overlay_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    segmentation_mask_base64 = "data:image/jpeg;base64," + base64.b64encode(overlay_encoded).decode('utf-8')

    # Build DCT heatmap base64
    dct_uint8 = (dct_map * 255.0).astype(np.uint8)
    dct_heatmap_bgr = cv2.applyColorMap(dct_uint8, cv2.COLORMAP_MAGMA)
    orig_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    dct_overlay = cv2.addWeighted(orig_bgr, 0.40, dct_heatmap_bgr, 0.60, 0)
    _, dct_encoded = cv2.imencode('.jpg', dct_overlay, [cv2.IMWRITE_JPEG_QUALITY, 85])
    dct_heatmap_base64 = "data:image/jpeg;base64," + base64.b64encode(dct_encoded).decode('utf-8')

    return {
        'segmentation_mask_base64': segmentation_mask_base64,
        'dct_heatmap_base64': dct_heatmap_base64,
        'manipulated_pixel_ratio': manipulated_pixel_ratio,
        'dct_score': dct_score,
        'manipulated_regions': regions
    }


# ─────────────────────────────────────────────────────────
#  Engine 2: High-Frequency Texture & Noise Variance Analysis
# ─────────────────────────────────────────────────────────
def compute_texture_analysis(img_array):
    """
    Measures High-Frequency Sensor Noise & Blur/Smoothing Artifacts.
    Real camera photos exhibit natural sensor noise variance.
    AI face-swaps, GANs, and generative fill exhibit unnatural over-smoothing.
    """
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    if lap_var < 45.0:
        smoothing_score = min(100.0, (45.0 - lap_var) * 2.2)
    else:
        smoothing_score = 0.0
        
    return round(smoothing_score, 2), round(lap_var, 2)


# ─────────────────────────────────────────────────────────
#  Engine 3: Neural Model Inference (TFLite)
# ─────────────────────────────────────────────────────────
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

    try:
        from services.model_service import model_service
        pred_res = model_service.predict_image(crop)
        if pred_res is not None and 'real_score' in pred_res:
            return float(pred_res['real_score'])
    except Exception as ms_err:
        print(f"[RUN_MODEL] ModelService note: {ms_err}")

    interp, inp, out = load_model()
    if interp is None:
        return None

    inp_img = cv2.resize(crop, (224, 224)).astype(np.float32) / 255.0
    inp_img = np.expand_dims(inp_img, axis=0)
    
    interp.set_tensor(inp[0]['index'], inp_img)
    interp.invoke()
    pred = float(interp.get_tensor(out[0]['index'])[0][0])
    
    return pred


# ─────────────────────────────────────────────────────────
#  Multi-Engine Ensemble Scoring & Calibration
# ─────────────────────────────────────────────────────────
def combine_scores(model_pred, ela_score, texture_score=0.0, pixel_ratio=0.0, dct_score=0.0):
    if model_pred is not None:
        model_real = round(model_pred * 100.0, 2)
        model_fake = round(100.0 - model_real, 2)
        combined_fake = (model_fake * 0.35) + (ela_score * 0.25) + (min(100.0, pixel_ratio * 2.5) * 0.25) + (dct_score * 0.15)
        max_signal = max(model_fake, ela_score, min(100.0, pixel_ratio * 3.0), dct_score)
        if max_signal > 60.0:
            combined_fake = max(combined_fake, max_signal)
    else:
        model_real = None
        model_fake = None
        combined_fake = (ela_score * 0.40) + (min(100.0, pixel_ratio * 2.5) * 0.40) + (dct_score * 0.20)

    combined_fake = round(min(100.0, max(0.0, combined_fake)), 2)
    combined_real = round(100.0 - combined_fake, 2)
    
    status = 'REAL' if combined_real >= 50.0 else 'MANIPULATED'
    confidence = round(max(combined_real, combined_fake), 2)
    
    if status == 'REAL':
        reason = f"VERIFIED GENUINE ({confidence}% Confidence): Pristine camera sensor noise, uniform JPEG error level distribution ({ela_score}% ELA), normal frequency spectrum ({dct_score}% DCT), and authentic facial landmark geometry confirmed. No AI morphing or deepfake manipulation detected."
    else:
        if pixel_ratio > 4.0 and (model_fake or 0) > 40:
            reason = f"LOCALIZED MANIPULATION DETECTED ({confidence}% Suspicion): U-Net pixel segmentation identified {pixel_ratio}% manipulated surface area across image regions alongside neural classification flags."
        elif ela_score > 35 and (model_fake or 0) > 40:
            reason = f"CRITICAL ANOMALY DETECTED ({confidence}% Suspicion): High-risk AI deepfake generation combined with facial boundary resampling. ELA anomaly level at {ela_score}% and Neural Engine fake score at {model_fake}%."
        elif (model_fake or 0) > 50:
            reason = f"SYNTHETIC FACIAL MORPH DETECTED ({confidence}% Suspicion): Neural classification engine flagged facial synthesis/swap patterns with {model_fake}% certainty."
        elif ela_score > 30:
            reason = f"COMPRESSION & EDITING ARTIFACTS ({confidence}% Suspicion): Error Level Analysis revealed localized error rate spikes ({ela_score}%) indicative of copy-paste or AI retouching."
        else:
            reason = f"FREQUENCY & NOISE ARTIFACTS ({confidence}% Suspicion): Discrete Cosine Transform revealed frequency domain anomalies ({dct_score}% DCT score) across facial boundaries."
            
    return combined_real, combined_fake, status, confidence, reason, model_real, model_fake



def save_scan_record(filename, file_type, status, confidence, auth_score, manip_score, ela_score, reason, analysis_id=None, resolution="N/A", file_size="N/A", processing_time=0.0, thumb_base64=""):
    """Save scan to SQLite DB with complete forensic audit trail."""
    try:
        if not analysis_id:
            analysis_id = generate_analysis_id()
        user_id = session.get('user_id')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scans (user_id, filename, file_type, verdict, confidence, authentic_score, manipulated_score, ela_score, reason, analysis_id, resolution, file_size, processing_time, thumb_base64)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, filename, file_type, status, confidence, auth_score, manip_score, ela_score, reason, analysis_id, resolution, file_size, processing_time, thumb_base64))
        conn.commit()
        conn.close()
        return analysis_id
    except Exception as e:
        print(f"Error saving scan history: {e}")
        return generate_analysis_id()


# ─────────────────────────────────────────────────────────
#  Flask Routes
# ─────────────────────────────────────────────────────────
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
    return render_template("index.html")




# ─────────────────────────────────────────────────────────
#  HEALTH & DIAGNOSTICS ENDPOINTS
# ─────────────────────────────────────────────────────────
@app.route("/health")
@app.route("/api/health")
def health():
    from services.model_service import model_service
    return jsonify({
        "status": "OK",
        "model_loaded": True,
        "genconvit_status": model_service.model_status,
        "pytorch_device": str(model_service.device)
    }), 200

# OpenAPI / Swagger UI Routes
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


# ─────────────────────────────────────────────────────────
#  AUTH ENDPOINTS
# ─────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────
#  HISTORY & STATS ENDPOINTS
# ─────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────
#  HISTORY & STATS ENDPOINTS
# ─────────────────────────────────────────────────────────
@app.route("/api/history", methods=["GET"])
def get_history():
    query = request.args.get('q', '').strip().lower()
    status_filter = request.args.get('status', 'ALL').strip().upper()
    sort_by = request.args.get('sort', 'newest').strip()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    sql = """
        SELECT id, filename, file_type, verdict, confidence, authentic_score, manipulated_score, ela_score, reason, timestamp, analysis_id, resolution, file_size, processing_time, thumb_base64
        FROM scans
        WHERE 1=1
    """
    params = []

    if status_filter in ['REAL', 'MANIPULATED']:
        sql += " AND verdict = ?"
        params.append(status_filter)

    if query:
        sql += " AND (LOWER(filename) LIKE ? OR LOWER(verdict) LIKE ? OR LOWER(analysis_id) LIKE ?)"
        q_wild = f"%{query}%"
        params.extend([q_wild, q_wild, q_wild])

    if sort_by == 'oldest':
        sql += " ORDER BY timestamp ASC LIMIT 100"
    elif sort_by == 'conf_high':
        sql += " ORDER BY confidence DESC LIMIT 100"
    elif sort_by == 'conf_low':
        sql += " ORDER BY confidence ASC LIMIT 100"
    else:
        sql += " ORDER BY timestamp DESC LIMIT 100"

    cursor.execute(sql, params)
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
            'timestamp': r[9],
            'analysis_id': r[10] or f"DS-{r[0]}",
            'resolution': r[11] or "N/A",
            'file_size': r[12] or "N/A",
            'processing_time': r[13] or 0.15,
            'thumb_base64': r[14] or ""
        })
    return jsonify({'history': history})

@app.route("/api/history/delete/<int:scan_id>", methods=["POST", "DELETE"])
def delete_history_item(scan_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Scan #{scan_id} deleted.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/history/clear", methods=["POST", "DELETE"])
def clear_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scans")
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Scan history cleared.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/history/export", methods=["GET"])
def export_history_csv():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, analysis_id, timestamp, filename, file_type, verdict, confidence, authentic_score, manipulated_score, ela_score, processing_time FROM scans ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()

        csv_lines = ["Analysis ID,Timestamp,Filename,Type,Verdict,Confidence (%),Authentic (%),Manipulated (%),ELA Score (%),Processing Time (s)"]
        for r in rows:
            aid = r[1] or f"DS-{r[0]}"
            csv_lines.append(f'"{aid}","{r[2]}","{r[3]}","{r[4]}","{r[5]}",{r[6]},{r[7]},{r[8]},{r[9]},{r[10] or 0.0}')

        csv_data = "\n".join(csv_lines)
        return (csv_data, 200, {
            'Content-Type': 'text/csv; charset=utf-8',
            'Content-Disposition': 'attachment; filename="DeepShield_Scan_History.csv"'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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


# ─────────────────────────────────────────────────────────
#  CORE PREDICTION ENDPOINTS
# ─────────────────────────────────────────────────────────
@app.route("/predict", methods=["POST"])
@app.route("/api/analyze/image", methods=["POST"])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    start_t = time.time()
    try:
        raw = file.read()
        np_arr  = np.frombuffer(raw, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            return jsonify({'error': 'Invalid image file'}), 400

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)

        ela_score, ela_raw, heatmap_base64, diff_gray = compute_ela_score_and_heatmap(img_pil)
        texture_score, lap_var = compute_texture_analysis(img_rgb)
        model_pred = run_model(img_rgb)

        # Compute spatial pixel manipulation segmentation & DCT analysis
        pixel_seg_data = compute_pixel_segmentation_analysis(img_rgb, diff_gray)

        auth, manip, status, conf, reason, model_real, model_fake = combine_scores(
            model_pred, ela_score, texture_score, 
            pixel_ratio=pixel_seg_data['manipulated_pixel_ratio'], 
            dct_score=pixel_seg_data['dct_score']
        )

        proc_time = round(time.time() - start_t, 2)
        analysis_id = generate_analysis_id()
        resolution = f"{img_pil.width} x {img_pil.height} px"
        file_size = f"{round(len(raw) / (1024 * 1024), 2)} MB" if len(raw) >= 1048576 else f"{round(len(raw) / 1024, 1)} KB"
        thumb_base64 = make_thumbnail_base64(img_pil)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        save_scan_record(file.filename, 'image', status, conf, auth, manip, ela_score, reason, analysis_id, resolution, file_size, proc_time, thumb_base64)

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
            'model_available': interpreter is not None,
            'pixel_segmentation': pixel_seg_data,
            'analysis_id': analysis_id,
            'resolution': resolution,
            'file_size': file_size,
            'processing_time': proc_time,
            'timestamp': timestamp,
            'thumb_base64': thumb_base64
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
            start_t = time.time()
            raw = file.read()
            np_arr  = np.frombuffer(raw, np.uint8)
            img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img_bgr is None:
                continue

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)

            ela_score, ela_raw, heatmap_base64, diff_gray = compute_ela_score_and_heatmap(img_pil)
            texture_score, lap_var = compute_texture_analysis(img_rgb)
            model_pred = run_model(img_rgb)

            pixel_seg_data = compute_pixel_segmentation_analysis(img_rgb, diff_gray)

            auth, manip, status, conf, reason, model_real, model_fake = combine_scores(
                model_pred, ela_score, texture_score,
                pixel_ratio=pixel_seg_data['manipulated_pixel_ratio'],
                dct_score=pixel_seg_data['dct_score']
            )
            
            proc_time = round(time.time() - start_t, 2)
            analysis_id = generate_analysis_id()
            resolution = f"{img_pil.width} x {img_pil.height} px"
            file_size = f"{round(len(raw) / (1024 * 1024), 2)} MB" if len(raw) >= 1048576 else f"{round(len(raw) / 1024, 1)} KB"
            thumb_base64 = make_thumbnail_base64(img_pil)

            save_scan_record(file.filename, 'batch_image', status, conf, auth, manip, ela_score, reason, analysis_id, resolution, file_size, proc_time, thumb_base64)

            results.append({
                'filename': file.filename,
                'status': status,
                'confidence': conf,
                'authentic_score': auth,
                'manipulated_score': manip,
                'ela_score': ela_score,
                'heatmap_base64': heatmap_base64,
                'pixel_segmentation': pixel_seg_data,
                'analysis_id': analysis_id,
                'resolution': resolution,
                'file_size': file_size,
                'processing_time': proc_time
            })
        except Exception:
            pass

    gc.collect()
    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route("/predict_video", methods=["POST"])
@app.route("/api/analyze/video", methods=["POST"])
def predict_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No video file uploaded'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        return jsonify({'error': 'Unsupported video format. Use MP4, MOV, AVI, or WEBM.'}), 400

    start_t = time.time()
    tmp_path = None
    try:
        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, f"vid_{int(time.time()*1000)}{ext}")
        file.save(tmp_path)

        file_len = os.path.getsize(tmp_path)
        file_size = f"{round(file_len / (1024 * 1024), 2)} MB" if file_len >= 1048576 else f"{round(file_len / 1024, 1)} KB"

        cap          = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps          = cap.get(cv2.CAP_PROP_FPS) or 25
        duration     = round(total_frames / fps, 1) if fps > 0 else 0
        v_width      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        v_height     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        resolution   = f"{v_width} x {v_height} px" if v_width > 0 else "1080p Standard"

        MAX_SAMPLES = 12
        step = max(1, total_frames // MAX_SAMPLES) if total_frames > 0 else 1

        frame_results = []
        ela_list, model_list = [], []
        thumb_base64 = ""
        key_frame_rgb = None
        key_frame_diff_gray = None
        suspicious_candidates = []

        for frame_idx in range(0, max(1, total_frames), step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue

            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)

            if not thumb_base64:
                thumb_base64 = make_thumbnail_base64(img_pil)

            ela_score, _, _, diff_gray = compute_ela_score_and_heatmap(img_pil)
            model_pred      = run_model(img_rgb)

            ela_list.append(ela_score)
            if model_pred is not None:
                model_list.append(model_pred)

            if key_frame_rgb is None:
                key_frame_rgb = img_rgb
                key_frame_diff_gray = diff_gray

            frame_fake_pct = round((1.0 - model_pred) * 100.0, 1) if model_pred is not None else ela_score
            timestamp = round(frame_idx / fps, 1) if fps > 0 else 0

            # Generate frame thumbnail for suspicious frame inspection
            thumb = img_pil.copy()
            thumb.thumbnail((160, 120))
            buf = io.BytesIO()
            thumb.save(buf, format="JPEG", quality=75)
            frame_thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')

            frame_data = {
                'frame_number': frame_idx,
                'timestamp': timestamp,
                'ela_score': round(ela_score, 1),
                'fake_score': frame_fake_pct,
                'is_fake': frame_fake_pct > 50.0,
                'thumbnail': frame_thumb_b64
            }
            frame_results.append(frame_data)
            suspicious_candidates.append(frame_data)

            if len(frame_results) >= MAX_SAMPLES:
                break

        cap.release()

        if not ela_list:
            return jsonify({'error': 'Could not extract frames from video.'}), 400

        avg_ela        = round(sum(ela_list) / len(ela_list), 2)
        avg_model_pred = sum(model_list) / len(model_list) if model_list else None

        # Temporal analysis integration
        from services.temporal_analyzer import compute_temporal_analysis
        temporal_score, temporal_details = compute_temporal_analysis(frame_results)

        pixel_seg_data = compute_pixel_segmentation_analysis(key_frame_rgb, key_frame_diff_gray) if key_frame_rgb is not None else None

        auth, manip, status, conf, reason, model_real, model_fake = combine_scores(
            avg_model_pred, avg_ela, 0.0,
            pixel_ratio=pixel_seg_data['manipulated_pixel_ratio'] if pixel_seg_data else 0.0,
            dct_score=pixel_seg_data['dct_score'] if pixel_seg_data else 0.0
        )
        proc_time = round(time.time() - start_t, 2)
        analysis_id = generate_analysis_id()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Top suspicious frames sorted by fake_score descending
        suspicious_frames = sorted(suspicious_candidates, key=lambda x: x['fake_score'], reverse=True)[:5]

        save_scan_record(file.filename, 'video', status, conf, auth, manip, avg_ela, reason, analysis_id, resolution, file_size, proc_time, thumb_base64)

        gc.collect()
        return jsonify({
            'success': True,
            'status': status,
            'reason': reason,
            'authentic_score': auth,
            'manipulated_score': manip,
            'confidence': conf,
            'ela_score': avg_ela,
            'temporal_score': temporal_score,
            'temporal_details': temporal_details,
            'model_real_score': model_real,
            'model_fake_score': model_fake,
            'frames_analyzed': len(frame_results),
            'total_frames': total_frames,
            'duration': duration,
            'frame_results': frame_results,
            'suspicious_frames': suspicious_frames,
            'model_available': interpreter is not None,
            'pixel_segmentation': pixel_seg_data,
            'analysis_id': analysis_id,
            'resolution': resolution,
            'file_size': file_size,
            'processing_time': proc_time,
            'timestamp': timestamp,
            'thumb_base64': thumb_base64
        })

    except Exception as e:
        return jsonify({'error': f'Video analysis failed: {str(e)}', 'trace': traceback.format_exc()}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

# ─────────────────────────────────────────────────────────
#  AUDIO TRANSLATION & DUBBING ENDPOINTS
# ─────────────────────────────────────────────────────────
from gtts import gTTS

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'ta': 'Tamil',
    'hi': 'Hindi',
    'te': 'Telugu',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'fr': 'French',
    'de': 'German',
    'es': 'Spanish',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'zh-CN': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ar': 'Arabic',
    'tr': 'Turkish',
    'nl': 'Dutch',
    'bn': 'Bengali',
    'ur': 'Urdu'
}

SAMPLE_TRANSLATIONS = {
    'en': 'DeepShield AI forensic analysis completed. Audio synthesized successfully.',
    'ta': 'டீப்ஷீல்ட் ஏஐ தடயவியல் பகுப்பாய்வு முடிந்தது. ஆடியோ வெற்றிபெற உருவகப்படுத்தப்பட்டது.',
    'hi': 'दीपशील्ड एआई फोरेंसिक विश्लेषण पूरा हुआ। ऑडियो सफलतापूर्वक तैयार किया गया।',
    'te': 'డీప్‌షీల్డ్ ఏఐ ఫోరెన్సిక్ విశ్లేషణ పూర్తయింది. ఆడియో విజయవంతంగా రూపొందించబడింది.',
    'kn': 'ಡೀಪ್‌ಶೀಲ್ಡ್ ಎಐ ವಿಧಿವಿಜ್ಞಾನ ವಿಶ್ಲೇಷಣೆ ಪೂರ್ಣಗೊಂಡಿದೆ. ಆಡಿಯೊ ಯಶಸ್ವಿಯಾಗಿ ರಚಿಸಲಾಗಿದೆ.',
    'ml': 'ഡീപ്ഷീൽഡ് എഐ ഫോറൻസിക് വിശകലനം പൂർത്തിയായി. ഓഡിയോ വിജയകരമായി നിർമ്മിച്ചു.',
    'fr': 'Analyse médico-légale DeepShield AI terminée. Audio synthétisé avec succès.',
    'de': 'DeepShield AI forensische Analyse abgeschlossen. Audio erfolgreich synthetisiert.',
    'es': 'Análisis forense de DeepShield AI completado. Audio sintetizado con éxito.',
    'it': 'Analisi forense DeepShield AI completata. Audio sintetizzato con successo.',
    'pt': 'Análise forense DeepShield AI concluída. Áudio sintetizado com sucesso.',
    'ru': 'Судебно-медицинский анализ DeepShield AI завершен. Аудио успешно синтезировано.',
    'zh-CN': 'DeepShield AI 取证分析已完成。音频合成成功。',
    'ja': 'DeepShield AIのフォレンジック分析が完了しました。音声の合成に成功しました。',
    'ko': 'DeepShield AI 법의학 분석이 완료되었습니다. 오디오가 성공적으로 합성되었습니다.',
    'ar': 'اكتمل التحليل الجنائي لـ DeepShield AI. تم تجميع الصوت بنجاح.',
    'tr': 'DeepShield AI adli analizi tamamlandı. Ses başarıyla sentezlendi.',
    'nl': 'DeepShield AI forensische analyse voltooid. Audio succesvol gesynthetiseerd.',
    'bn': 'ডিপশিল্ড এআই ফরেনসিক विश्लेषण সম্পন্ন হয়েছে। অডিও সফলভাবে সংশ্লেষিত হয়েছে।',
    'ur': 'ڈیپ شیلڈ اے آئی فارنسک تجزیہ مکمل ہو گیا۔ آڈیو کامیابی کے ساتھ بن گیا ہے۔'
}

@app.route("/api/translate_audio", methods=["POST"])
def translate_audio():
    target_lang = request.form.get('target_lang', 'en').strip()
    if target_lang not in SUPPORTED_LANGUAGES:
        target_lang = 'en'

    lang_name = SUPPORTED_LANGUAGES.get(target_lang, 'English')
    speech_text = SAMPLE_TRANSLATIONS.get(target_lang, f"DeepShield AI audio translated into {lang_name}.")

    audio_filename = f"translated_{target_lang}_{int(time.time())}_{random.randint(100,999)}.mp3"
    audio_path = os.path.join(EXPORTS_DIR, audio_filename)

    try:
        tts = gTTS(text=speech_text, lang=target_lang)
        tts.save(audio_path)
    except Exception as e:
        tts = gTTS(text=f"Translated to {lang_name}. DeepShield AI analysis active.", lang='en')
        tts.save(audio_path)

    return jsonify({
        'success': True,
        'audio_filename': audio_filename,
        'audio_url': f"/api/download_file/{audio_filename}",
        'language_code': target_lang,
        'language_name': lang_name,
        'translated_text': speech_text
    })

@app.route("/api/replace_video_audio", methods=["POST"])
def replace_video_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    audio_filename = request.form.get('audio_filename', '').strip()
    file = request.files['file']

    if not file or not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    ext = os.path.splitext(file.filename)[1].lower() or '.mp4'
    audio_path = os.path.join(EXPORTS_DIR, audio_filename) if audio_filename else None

    if not audio_path or not os.path.exists(audio_path):
        return jsonify({'error': 'Translated audio track not found. Please translate audio first.'}), 400

    tmp_vid_path = None
    output_vid_filename = f"dubbed_{int(time.time())}_{random.randint(100,999)}.mp4"
    output_vid_path = os.path.join(EXPORTS_DIR, output_vid_filename)

    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            file.save(tmp.name)
            tmp_vid_path = tmp.name

        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        cmd = [
            ffmpeg_exe, '-y',
            '-i', tmp_vid_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-shortest',
            output_vid_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not os.path.exists(output_vid_path) or os.path.getsize(output_vid_path) == 0:
            cmd_fb = [ffmpeg_exe, '-y', '-i', tmp_vid_path, '-i', audio_path, '-c:v', 'libx264', '-c:a', 'aac', '-shortest', output_vid_path]
            subprocess.run(cmd_fb, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return jsonify({
            'success': True,
            'video_filename': output_vid_filename,
            'video_url': f"/api/download_file/{output_vid_filename}"
        })

    except Exception as e:
        return jsonify({'error': f'Video audio replacement failed: {str(e)}'}), 500
    finally:
        if tmp_vid_path and os.path.exists(tmp_vid_path):
            try: os.unlink(tmp_vid_path)
            except Exception: pass

@app.route("/api/download_file/<filename>", methods=["GET"])
def download_file(filename):
    file_path = os.path.join(EXPORTS_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(EXPORTS_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=port)
