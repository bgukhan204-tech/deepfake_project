import React, { useState, useRef } from 'react';
import { Video, Upload, Play, X, Loader2 } from 'lucide-react';

export default function VideoScanner({ onAnalyzeVideo, isLoading }) {
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const videoInputRef = useRef(null);

  const handleVideoChange = (file) => {
    setValidationError(null);
    if (!file) return;
    const validExtensions = ['.mp4', '.mov', '.avi', '.webm'];
    const hasValidExt = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    if (!file.type.startsWith('video/') && !hasValidExt) {
      setValidationError('Please select a valid video file (MP4, MOV, AVI, WEBM).');
      return;
    }
    setSelectedVideo(file);
    setVideoUrl(URL.createObjectURL(file));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setValidationError(null);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleVideoChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = () => {
    if (!selectedVideo) {
      setValidationError('Please select a video file first before running analysis.');
      return;
    }
    onAnalyzeVideo(selectedVideo);
  };

  const handleClear = () => {
    setSelectedVideo(null);
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    setVideoUrl(null);
    setValidationError(null);
    if (videoInputRef.current) videoInputRef.current.value = '';
  };

  return (
    <div className="space-y-6">
      {!videoUrl ? (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => videoInputRef.current?.click()}
          className="border-2 border-dashed border-slate-800 hover:border-blue-500/80 rounded-2xl p-10 sm:p-14 text-center bg-slate-900/50 hover:bg-slate-900/80 cursor-pointer transition-all duration-300 group relative overflow-hidden shadow-xl"
        >
          <input
            type="file"
            ref={videoInputRef}
            onChange={(e) => handleVideoChange(e.target.files[0])}
            accept="video/*"
            className="hidden"
          />
          <div className="relative z-10 flex flex-col items-center space-y-4">
            
            {/* Video Camera Icon */}
            <div className="w-16 h-16 rounded-2xl bg-blue-950/40 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:scale-110 shadow-lg shadow-blue-500/10 transition-all">
              <Video className="w-7 h-7" />
            </div>

            <div className="space-y-1">
              <h3 className="text-base font-bold text-white tracking-wide">
                Drop video here
              </h3>
              <p className="text-xs text-slate-400">
                MP4, MOV, WEBM • Max 100MB
              </p>
            </div>

            {validationError && (
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs font-semibold max-w-md">
                {validationError}
              </div>
            )}

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                videoInputRef.current?.click();
              }}
              className="mt-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-lg shadow-blue-500/25 transition-all flex items-center space-x-2"
            >
              <Upload className="w-4 h-4" />
              <span>Choose Video</span>
            </button>

          </div>
        </div>
      ) : (
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-5 shadow-2xl">
          
          {/* Selected Video File Card (Matching deepfake.mp4) */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-3.5 truncate">
              <div className="w-10 h-10 rounded-xl bg-indigo-950/60 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                <Video className="w-5 h-5" />
              </div>
              <div className="truncate">
                <p className="text-xs font-bold text-white truncate max-w-xs sm:max-w-md">
                  {selectedVideo?.name}
                </p>
                <p className="text-[11px] text-slate-400">
                  {(selectedVideo?.size / (1024 * 1024)).toFixed(1)} MB
                </p>
              </div>
            </div>

            <button
              onClick={handleClear}
              disabled={isLoading}
              className="px-3 py-1.5 rounded-lg bg-rose-950/50 hover:bg-rose-900/60 text-rose-300 text-xs font-semibold border border-rose-500/30 transition-all flex items-center space-x-1"
            >
              <X className="w-3.5 h-3.5" />
              <span>Remove</span>
            </button>
          </div>

          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="w-full py-3.5 px-6 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing frames...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Analyze Video</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

