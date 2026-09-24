import React, { useState } from 'react';
import { X, Layers, Target, Grid, Sparkles } from 'lucide-react';

export default function ElaHeatmapModal({ result, heatmapUrl, originalPreview, onClose }) {
  const [viewMode, setViewMode] = useState('unet'); // 'unet', 'ela', 'dct', 'sideBySide'

  const pixelSeg = result?.pixel_segmentation || {};
  const unetOverlay = pixelSeg.segmentation_mask_base64;
  const dctMap = pixelSeg.dct_heatmap_base64;
  const elaMap = result?.heatmap_base64 || heatmapUrl;

  const currentMapUrl = viewMode === 'unet' ? (unetOverlay || elaMap) : viewMode === 'dct' ? (dctMap || elaMap) : elaMap;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="glass-panel w-full max-w-4xl rounded-2xl border border-slate-800 p-6 space-y-6 max-h-[90vh] overflow-y-auto shadow-2xl">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white font-['Outfit']">Spatial Pixel Manipulation Visualizer</h3>
              <p className="text-xs text-slate-400">Pixel-level localization, U-Net region masks & multi-spectral heatmaps</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* View Mode Tabs */}
        <div className="flex flex-wrap justify-center gap-1.5 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800 max-w-xl mx-auto text-xs font-semibold">
          {unetOverlay && (
            <button
              onClick={() => setViewMode('unet')}
              className={`flex-1 py-1.5 px-3 rounded-lg transition-all flex items-center justify-center space-x-1.5 ${
                viewMode === 'unet' ? 'bg-rose-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Target className="w-3.5 h-3.5" />
              <span>U-Net Regions</span>
            </button>
          )}

          <button
            onClick={() => setViewMode('ela')}
            className={`flex-1 py-1.5 px-3 rounded-lg transition-all flex items-center justify-center space-x-1.5 ${
              viewMode === 'ela' ? 'bg-cyan-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>ELA Heatmap</span>
          </button>

          {dctMap && (
            <button
              onClick={() => setViewMode('dct')}
              className={`flex-1 py-1.5 px-3 rounded-lg transition-all flex items-center justify-center space-x-1.5 ${
                viewMode === 'dct' ? 'bg-amber-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Grid className="w-3.5 h-3.5" />
              <span>DCT Frequency</span>
            </button>
          )}

          <button
            onClick={() => setViewMode('sideBySide')}
            className={`flex-1 py-1.5 px-3 rounded-lg transition-all ${
              viewMode === 'sideBySide' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Side-by-Side
          </button>
        </div>

        {/* Heatmap Display Box */}
        <div className="flex justify-center items-center bg-black/80 rounded-xl p-4 border border-slate-800 min-h-[320px]">
          {viewMode !== 'sideBySide' && (
            <img src={currentMapUrl} alt="Spatial Forensic Heatmap" className="max-h-[480px] object-contain rounded-lg shadow-xl border border-slate-800" />
          )}

          {viewMode === 'sideBySide' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
              {originalPreview && (
                <div className="space-y-2 text-center">
                  <span className="text-xs font-semibold text-slate-300">Original Content</span>
                  <img src={originalPreview} alt="Original" className="max-h-[380px] w-full object-contain rounded-lg border border-slate-800" />
                </div>
              )}
              <div className="space-y-2 text-center">
                <span className="text-xs font-semibold text-rose-400">U-Net Spatial Pixel Mask & Bounding Boxes</span>
                <img src={unetOverlay || elaMap} alt="Overlay" className="max-h-[380px] w-full object-contain rounded-lg border border-rose-500/30" />
              </div>
            </div>
          )}
        </div>

        {/* Educational Info */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs text-slate-400 space-y-1">
          <span className="font-semibold text-cyan-300 flex items-center space-x-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Forensic Signal Visualizer Guide:</span>
          </span>
          <p>
            <strong>U-Net Regions</strong> highlights exact manipulated pixels with localized red bounding box callouts. 
            <strong> ELA Heatmap</strong> identifies compression rate anomalies. 
            <strong> DCT Frequency</strong> reveals 8x8 block high-frequency energy discontinuities across facial boundaries.
          </p>
        </div>

      </div>
    </div>
  );
}

