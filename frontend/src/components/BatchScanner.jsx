import React, { useState, useRef } from 'react';
import { Layers, UploadCloud, RefreshCw, Sparkles, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function BatchScanner({ onAnalyzeBatch, isLoading, batchResults }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [validationError, setValidationError] = useState(null);
  const [fileStatuses, setFileStatuses] = useState({}); // filename -> { status, verdict, confidence }
  const [isBatchRunning, setIsBatchRunning] = useState(false);
  const fileInputRef = useRef(null);

  const handleFilesChange = (files) => {
    setValidationError(null);
    if (!files || files.length === 0) return;
    const validFiles = Array.from(files).filter(f => 
      f.type.startsWith('image/') || 
      f.type.startsWith('video/') ||
      ['.mp4', '.mov', '.avi', '.webm', '.jpg', '.jpeg', '.png', '.webp'].some(ext => f.name.toLowerCase().endsWith(ext))
    );

    if (validFiles.length === 0) {
      setValidationError('Please select valid image or video files.');
      return;
    }

    setSelectedFiles(prev => {
      const combined = [...prev, ...validFiles];
      const unique = Array.from(new Map(combined.map(f => [f.name + f.size, f])).values());
      return unique;
    });

    const initialStatuses = {};
    validFiles.forEach(f => {
      initialStatuses[f.name] = { state: 'QUEUED', verdict: null, confidence: null };
    });
    setFileStatuses(prev => ({ ...prev, ...initialStatuses }));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setValidationError(null);
    if (e.dataTransfer.files) {
      handleFilesChange(e.dataTransfer.files);
    }
  };

  const handleSubmit = async () => {
    if (selectedFiles.length === 0) {
      setValidationError('Please select at least one image or video file to analyze.');
      return;
    }

    setIsBatchRunning(true);
    setValidationError(null);

    // Reuse existing single image/video endpoints sequentially for each queued item
    const results = [];
    for (const file of selectedFiles) {
      setFileStatuses(prev => ({
        ...prev,
        [file.name]: { state: 'ANALYZING', verdict: null, confidence: null }
      }));

      const formData = new FormData();
      formData.append('file', file);
      const isVideo = file.type.startsWith('video/') || ['.mp4', '.mov', '.avi', '.webm'].some(ext => file.name.toLowerCase().endsWith(ext));
      const endpoint = isVideo ? '/api/analyze/video' : '/api/analyze/image';

      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          body: formData,
          credentials: 'include'
        });
        const data = await res.json();
        if (res.ok && (data.success || data.classification || data.status)) {
          const verdict = data.status || (data.classification === 'LIKELY_FAKE' ? 'MANIPULATED' : 'REAL');
          const confidence = data.confidence || 95.0;
          setFileStatuses(prev => ({
            ...prev,
            [file.name]: { state: 'DONE', verdict, confidence }
          }));
          results.push({ filename: file.name, status: verdict, confidence });
        } else {
          setFileStatuses(prev => ({
            ...prev,
            [file.name]: { state: 'ERROR', verdict: 'ERROR', confidence: 0 }
          }));
        }
      } catch (err) {
        setFileStatuses(prev => ({
          ...prev,
          [file.name]: { state: 'ERROR', verdict: 'ERROR', confidence: 0 }
        }));
      }
    }

    setIsBatchRunning(false);
    if (onAnalyzeBatch) {
      onAnalyzeBatch(selectedFiles);
    }
  };

  const handleClear = () => {
    setSelectedFiles([]);
    setFileStatuses({});
    setValidationError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const activeLoading = isLoading || isBatchRunning;

  return (
    <div className="space-y-6">
      {selectedFiles.length === 0 ? (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-slate-700/80 hover:border-emerald-500/80 rounded-2xl p-8 sm:p-12 text-center bg-slate-900/40 hover:bg-slate-800/40 cursor-pointer transition-all duration-300 group relative overflow-hidden"
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFilesChange(e.target.files)}
            accept="image/*,video/*,.mp4,.mov,.avi,.webm,.jpg,.jpeg,.png,.webp"
            multiple
            className="hidden"
          />
          <div className="relative z-10 flex flex-col items-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-slate-800/90 border border-slate-700 flex items-center justify-center text-emerald-400 group-hover:scale-110 shadow-xl transition-all">
              <Layers className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white group-hover:text-emerald-300 transition-colors">
                Drop Multiple Images & Videos Here
              </h3>
              <p className="text-sm text-slate-400 mt-1">
                Batch inspect multiple media files in parallel using single-file neural & ELA pipelines
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
              className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-lg shadow-emerald-500/20 transition-all flex items-center space-x-2"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Choose Files for Batch Mode</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Layers className="w-5 h-5 text-emerald-400" />
              <span className="text-sm font-semibold text-slate-200">
                {selectedFiles.length} Media Files Queued
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={activeLoading}
                className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex items-center space-x-1"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                <span>Add More</span>
              </button>
              <button
                onClick={handleClear}
                disabled={activeLoading}
                className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-rose-400 hover:text-rose-300 transition-colors flex items-center space-x-1"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Clear All</span>
              </button>
            </div>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFilesChange(e.target.files)}
            accept="image/*,video/*,.mp4,.mov,.avi,.webm,.jpg,.jpeg,.png,.webp"
            multiple
            className="hidden"
          />

          {validationError && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs font-semibold">
              {validationError}
            </div>
          )}

          {/* Queued Files Grid / List */}
          <div className="max-h-60 overflow-y-auto pr-1 space-y-2">
            {selectedFiles.map((file, idx) => {
              const isVideo = file.type.startsWith('video/') || ['.mp4', '.mov', '.avi', '.webm'].some(ext => file.name.toLowerCase().endsWith(ext));
              const statusInfo = fileStatuses[file.name] || { state: 'QUEUED' };
              const isDone = statusInfo.state === 'DONE';
              const isAnalyzing = statusInfo.state === 'ANALYZING';
              const isReal = statusInfo.verdict === 'REAL';
              const isManip = statusInfo.verdict === 'MANIPULATED';

              return (
                <div
                  key={idx}
                  className={`flex items-center justify-between p-3 rounded-xl border text-xs transition-all ${
                    isDone && isReal
                      ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
                      : isDone && isManip
                      ? 'bg-rose-950/30 border-rose-500/40 text-rose-200'
                      : isAnalyzing
                      ? 'bg-indigo-950/40 border-indigo-500/40 text-indigo-200 animate-pulse'
                      : 'bg-slate-900/70 border-slate-800 text-slate-300'
                  }`}
                >
                  <div className="flex items-center space-x-3 truncate max-w-md">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${isVideo ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'}`}>
                      {isVideo ? 'Video' : 'Image'}
                    </span>
                    <span className="font-medium truncate">{file.name}</span>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className="text-[11px] text-slate-500">{(file.size / 1024).toFixed(1)} KB</span>
                    {isAnalyzing ? (
                      <span className="flex items-center space-x-1 text-indigo-400 font-semibold">
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Analyzing...</span>
                      </span>
                    ) : isDone ? (
                      <div className="flex items-center space-x-2 font-bold">
                        {isReal ? (
                          <span className="flex items-center space-x-1 text-emerald-400">
                            <CheckCircle2 className="w-4 h-4" />
                            <span>AUTHENTIC ({statusInfo.confidence}%)</span>
                          </span>
                        ) : (
                          <span className="flex items-center space-x-1 text-rose-400">
                            <AlertTriangle className="w-4 h-4" />
                            <span>MANIPULATED ({statusInfo.confidence}%)</span>
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-400 px-2 py-0.5 rounded bg-slate-800 text-[10px] font-semibold uppercase">
                        Queued
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <button
            onClick={handleSubmit}
            disabled={activeLoading}
            className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-emerald-600 via-cyan-600 to-emerald-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {activeLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Running Batch Inspection...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Analyze All Queued Media Files</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

