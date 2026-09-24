# DeepShield AI - Advanced Deepfake & Media Forensic Engine

DeepShield AI is a production-ready, multi-engine AI deepfake and facial manipulation detection platform. It combines PyTorch Vision Transformers (GenConViT), TensorFlow Lite fallback models, Error Level Analysis (ELA), Laplacian texture frequency analysis, and OpenCV temporal frame breakdown.

---

## 🏗️ System Architecture

```
┌───────────────────────────────────────────────────────────────┐
│              React + Vite Frontend (Port 5173 / 5000)          │
│   Image Scanner • Video Timeline • Live Webcam • Batch Scan    │
└───────────────────────────────┬───────────────────────────────┘
                                │ REST API (CORS Enabled)
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                     Flask Backend (app_web.py)                │
├───────────────────────────────────────────────────────────────┤
│  • Engine 1: GenConViT Neural Transformer (PyTorch)           │
│  • Engine 2: Fallback CNN Classifier (TensorFlow Lite)        │
│  • Engine 3: Forensic ELA & Pixel-by-Pixel Heatmap Generator  │
│  • Engine 4: High-Frequency Laplacian Texture Analysis        │
│  • Engine 5: Temporal Inconsistency & Delta Spike Scoring     │
│  • Engine 6: U-Net Multi-Spectral Spatial Pixel Segmentation  │
└───────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 2. Backend Setup & Run

Activate virtual environment and launch Flask API server:

```powershell
# Navigate to workspace
cd d:\deepfake_detection

# Run Flask Backend Application
python app_web.py
```
The Flask backend runs on `http://localhost:5000`.

### 3. Frontend Setup & Run (React + Vite)

```powershell
cd d:\deepfake_detection\frontend

# Install dependencies (if needed)
npm install

# Start Vite Development Server
npm run dev
```
The React frontend dashboard opens on `http://localhost:5173`.

To build static frontend production assets served directly by Flask:
```powershell
cd d:\deepfake_detection\frontend
npm run build
```

---

## 📡 REST API Documentation

### `GET /api/health`
Returns system health, model loading status, and active compute device (CPU/CUDA).

### `POST /api/analyze/image` (or `/predict`)
- **Payload**: `file` (multipart/form-data)
- **Response**:
  - `authentic_score`: % Authentic probability
  - `manipulated_score`: % Manipulation probability
  - `confidence`: Confidence score
  - `ela_score`: Error Level Analysis compression variance
  - `heatmap_base64`: Colorized ELA overlay data URI
  - `pixel_segmentation`: U-Net spatial pixel breakdown

### `POST /api/analyze/video` (or `/predict_video`)
- **Payload**: `file` (MP4, AVI, MOV, WEBM)
- **Response**:
  - `temporal_score`: Frame-to-frame score variance and feature jitter score
  - `frame_results`: Full timeline frame breakdown with timestamp chips
  - `suspicious_frames`: Top suspicious frame thumbnails sorted by deepfake risk

---

## 🧪 Running Automated Tests

Run backend automated verification:
```powershell
python test_endpoints.py
```

---

## 🛡️ License
© 2026 DeepShield AI Forensic Technologies. All Rights Reserved.
