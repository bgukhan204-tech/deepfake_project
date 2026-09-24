import React, { useState, useRef, useEffect } from 'react';
import { Camera, Search, RefreshCw, X, Loader2 } from 'lucide-react';

export default function WebcamScanner({ onAnalyze, isLoading }) {
  const [streamActive, setStreamActive] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const startCamera = async () => {
    setCameraError(null);
    try {
      setCapturedImage(null);
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setStreamActive(true);
      }
    } catch (err) {
      setCameraError('Camera access permission was denied or camera hardware is unavailable.');
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setStreamActive(false);
  };

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current || videoRef.current.readyState < 2) {
      return;
    }
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    setCapturedImage(dataUrl);
    stopCamera();
  };

  const handleAnalyzeSnapshot = () => {
    if (!capturedImage) return;
    fetch(capturedImage)
      .then(res => res.blob())
      .then(blob => {
        const file = new File([blob], 'webcam_snapshot.jpg', { type: 'image/jpeg' });
        onAnalyze(file);
      });
  };

  const handleCancelSnapshot = () => {
    setCapturedImage(null);
    startCamera();
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6 shadow-2xl">
      <canvas ref={canvasRef} className="hidden" />

      {cameraError && (
        <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs font-semibold text-center">
          {cameraError}
        </div>
      )}

      {/* Live Video Viewport */}
      {!capturedImage && (
        <div className="space-y-4">
          <div className="relative rounded-2xl overflow-hidden bg-black/90 border border-slate-800 flex justify-center max-h-[440px] shadow-xl">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="w-full max-h-[440px] object-cover"
            />
            {!streamActive && !cameraError && (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-950/90 text-xs text-slate-400">
                Starting Camera...
              </div>
            )}
            
            {/* Overlaid Buttons matching video: Take Photo & Cancel */}
            {streamActive && (
              <div className="absolute bottom-4 inset-x-0 flex items-center justify-center space-x-3">
                <button
                  onClick={captureFrame}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-lg shadow-blue-500/30 transition-all flex items-center space-x-2"
                >
                  <Camera className="w-4 h-4" />
                  <span>Take Photo</span>
                </button>
                <button
                  onClick={stopCamera}
                  className="px-4 py-2.5 rounded-xl bg-slate-800/90 hover:bg-slate-700 text-slate-200 font-semibold text-xs transition-all border border-slate-700"
                >
                  <span>Cancel</span>
                </button>
              </div>
            )}
          </div>
          
          {!streamActive && (
            <button
              onClick={startCamera}
              className="w-full py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all border border-slate-700 flex items-center justify-center space-x-2"
            >
              <Camera className="w-4 h-4 text-blue-400" />
              <span>Restart Camera</span>
            </button>
          )}
        </div>
      )}

      {/* Captured Snapshot View */}
      {capturedImage && (
        <div className="space-y-4">
          <div className="relative rounded-2xl overflow-hidden bg-black/90 border border-slate-800 flex justify-center max-h-[420px]">
            <img src={capturedImage} alt="Captured Preview" className="object-contain max-h-[420px] rounded-lg" />
            {isLoading && (
              <div className="absolute inset-0 bg-slate-950/85 backdrop-blur-sm flex flex-col items-center justify-center space-y-3">
                <Loader2 className="w-10 h-10 text-blue-400 animate-spin" />
                <p className="text-xs font-medium text-slate-200 animate-pulse">Analyzing...</p>
              </div>
            )}
          </div>

          <div className="flex items-center justify-center space-x-3">
            <button
              onClick={handleCancelSnapshot}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors flex items-center space-x-1.5 border border-slate-700"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retake Photo</span>
            </button>
          </div>

          <button
            onClick={handleAnalyzeSnapshot}
            disabled={isLoading}
            className="w-full py-3.5 px-6 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Analyze Image</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

