import React, { useState, useRef } from 'react';
import { Upload, Image as ImageIcon, Search, RefreshCw, X, Loader2 } from 'lucide-react';

export default function ImageScanner({ onAnalyze, isLoading }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (file) => {
    setValidationError(null);
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setValidationError('Please select a valid image file (JPG, PNG, WEBP).');
      return;
    }
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = () => {
      setPreviewUrl(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setValidationError(null);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleSubmit = () => {
    if (!selectedFile) {
      setValidationError('Please choose an image file before analyzing.');
      return;
    }
    onAnalyze(selectedFile);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setValidationError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="space-y-6">
      {!previewUrl ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-slate-800 hover:border-blue-500/80 rounded-2xl p-10 sm:p-14 text-center bg-slate-900/50 hover:bg-slate-900/80 cursor-pointer transition-all duration-300 group relative overflow-hidden shadow-xl"
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFileChange(e.target.files[0])}
            accept="image/*"
            className="hidden"
          />
          <div className="relative z-10 flex flex-col items-center space-y-4">
            
            {/* Cloud Upload Icon */}
            <div className="w-16 h-16 rounded-2xl bg-blue-950/40 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:scale-110 shadow-lg shadow-blue-500/10 transition-all">
              <Upload className="w-7 h-7" />
            </div>

            <div className="space-y-1">
              <h3 className="text-base font-bold text-white tracking-wide">
                Drop Image here
              </h3>
              <p className="text-xs text-slate-400">
                PNG, JPG, WEBP • Detect AI images, deepfakes & edits
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
                fileInputRef.current?.click();
              }}
              className="mt-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-lg shadow-blue-500/25 transition-all flex items-center space-x-2"
            >
              <Upload className="w-4 h-4" />
              <span>Choose Image</span>
            </button>

          </div>
        </div>
      ) : (
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-5 shadow-2xl">
          
          {/* Preview Header / Change & Remove */}
          <div className="relative rounded-xl overflow-hidden bg-black/80 border border-slate-800 flex justify-center max-h-[420px]">
            <img
              src={previewUrl}
              alt="Selected Preview"
              className="object-contain max-h-[420px] rounded-lg"
            />
            {isLoading && (
              <div className="absolute inset-0 bg-slate-950/85 backdrop-blur-sm flex flex-col items-center justify-center space-y-3">
                <Loader2 className="w-10 h-10 text-blue-400 animate-spin" />
                <p className="text-xs font-medium text-slate-200 animate-pulse">Analyzing...</p>
              </div>
            )}
          </div>

          <div className="flex items-center justify-center space-x-3">
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors flex items-center space-x-1.5 border border-slate-700"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Change</span>
            </button>
            <button
              onClick={handleClear}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 text-xs font-semibold border border-rose-500/30 transition-colors flex items-center space-x-1.5"
            >
              <X className="w-3.5 h-3.5" />
              <span>Remove</span>
            </button>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFileChange(e.target.files[0])}
            accept="image/*"
            className="hidden"
          />

          <button
            onClick={handleSubmit}
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

