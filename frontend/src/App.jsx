import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ImageScanner from './components/ImageScanner';
import WebcamScanner from './components/WebcamScanner';
import VideoScanner from './components/VideoScanner';
import BatchScanner from './components/BatchScanner';
import HistoryDashboard from './components/HistoryDashboard';
import ResultsDisplay from './components/ResultsDisplay';
import ElaHeatmapModal from './components/ElaHeatmapModal';
import HistoryModal from './components/HistoryModal';
import AuthModal from './components/AuthModal';
import StatsModal from './components/StatsModal';

import { Image as ImageIcon, Camera, Video, Sparkles, UserCheck, XCircle, Film } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('image'); // 'image', 'camera', 'video', 'batch', 'dashboard'
  const [systemStatus, setSystemStatus] = useState(null);
  const [user, setUser] = useState(null);

  // Scan state
  const [isLoading, setIsLoading] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [originalPreview, setOriginalPreview] = useState(null);
  const [videoResults, setVideoResults] = useState(null);
  const [batchResults, setBatchResults] = useState(null);

  // Modals state
  const [showElaModal, setShowElaModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showStatsModal, setShowStatsModal] = useState(false);

  // Fetch initial health & session user
  useEffect(() => {
    fetch('/health')
      .then(res => res.json())
      .then(data => setSystemStatus(data))
      .catch(err => console.error('Health check failed:', err));

    fetch('/api/auth/me', { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (data.authenticated) {
          setUser({ username: data.username });
        }
      })
      .catch(err => console.error('Auth check error:', err));
  }, []);

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    setUser(null);
  };

  // Image & Webcam Analysis
  const handleAnalyzeImage = async (file) => {
    setIsLoading(true);
    setScanResult(null);
    setVideoResults(null);
    setBatchResults(null);

    const objectUrl = URL.createObjectURL(file);
    setOriginalPreview(objectUrl);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/analyze/image', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok && (data.success || data.classification)) {
        setScanResult({
          status: data.status || (data.classification === 'LIKELY_FAKE' ? 'MANIPULATED' : 'REAL'),
          classification: data.classification,
          confidence: data.confidence,
          authentic_score: data.authentic_score,
          manipulated_score: data.manipulated_score,
          ai_detection_score: data.ai_detection_score || data.model_fake_score,
          forensic_score: data.forensic_score || data.ela_score,
          ela_score: data.ela_score,
          reason: data.reason,
          heatmap_url: data.heatmap_base64 || data.heatmap_url,
          heatmap_base64: data.heatmap_base64,
          pixel_segmentation: data.pixel_segmentation,
          model_available: data.model_available
        });
      } else {
        alert(data.error || 'Forensic image analysis failed.');
      }
    } catch (err) {
      alert('Network error: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Video Analysis
  const handleAnalyzeVideo = async (file) => {
    setIsLoading(true);
    setScanResult(null);
    setVideoResults(null);
    setBatchResults(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/analyze/video', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok && (data.success || data.classification)) {
        setScanResult({
          type: 'video',
          status: data.status || (data.classification === 'LIKELY_FAKE' ? 'MANIPULATED' : 'REAL'),
          classification: data.classification,
          confidence: data.confidence,
          authentic_score: data.authentic_score,
          manipulated_score: data.manipulated_score,
          ai_detection_score: data.ai_detection_score || data.model_fake_score,
          temporal_score: data.temporal_score,
          forensic_score: data.forensic_score || data.ela_score,
          ela_score: data.ela_score,
          duration: data.duration,
          total_frames: data.total_frames,
          frames_analyzed: data.frames_analyzed,
          frame_results: data.frame_results,
          suspicious_frames: data.suspicious_frames,
          reason: data.reason,
          heatmap_url: data.pixel_segmentation?.segmentation_mask_base64 || data.heatmap_base64,
          heatmap_base64: data.heatmap_base64,
          pixel_segmentation: data.pixel_segmentation,
          model_available: data.model_available
        });
        setVideoResults(data);
      } else {
        alert(data.error || 'Video forensic analysis failed.');
      }
    } catch (err) {
      alert('Network error: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Batch Analysis
  const handleAnalyzeBatch = async (files) => {
    setIsLoading(true);
    setScanResult(null);
    setVideoResults(null);
    setBatchResults(null);

    const formData = new FormData();
    Array.from(files).forEach(f => formData.append('files', f));

    try {
      const res = await fetch('/predict_batch', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok && data.results) {
        setBatchResults(data);
      } else {
        alert(data.error || 'Batch analysis failed.');
      }
    } catch (err) {
      alert('Network error: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Select historical item to display
  const handleSelectHistoryItem = (item) => {
    setScanResult({
      status: item.verdict,
      confidence: item.confidence,
      authentic_score: item.authentic_score || (item.verdict === 'REAL' ? item.confidence : 100 - item.confidence),
      manipulated_score: item.manipulated_score || (item.verdict === 'MANIPULATED' ? item.confidence : 100 - item.confidence),
      ela_score: item.ela_score || 0,
      reason: item.reason,
      heatmap_base64: item.thumb_base64
    });
  };

  const activePanel = {
    image: <ImageScanner onAnalyze={handleAnalyzeImage} isLoading={isLoading} />,
    camera: <WebcamScanner onAnalyze={handleAnalyzeImage} isLoading={isLoading} />,
    webcam: <WebcamScanner onAnalyze={handleAnalyzeImage} isLoading={isLoading} />,
    video: (
      <VideoScanner
        onAnalyzeVideo={handleAnalyzeVideo}
        isLoading={isLoading}
        videoResults={videoResults}
      />
    ),
    batch: (
      <BatchScanner
        onAnalyzeBatch={handleAnalyzeBatch}
        isLoading={isLoading}
        batchResults={batchResults}
      />
    ),
    dashboard: <HistoryDashboard onSelectHistoryItem={handleSelectHistoryItem} />,
    history: <HistoryDashboard onSelectHistoryItem={handleSelectHistoryItem} />,
  }[activeTab] || (
    <div className="glass-panel rounded-2xl border border-rose-500/40 bg-rose-950/20 p-6 text-center text-sm text-rose-200">
      This analysis mode is unavailable. Please choose one of the tabs above.
    </div>
  );

  return (
    <div className="min-h-screen flex flex-col font-sans bg-[#080c14] text-slate-100 selection:bg-cyan-500 selection:text-white">
      
      {/* Top Navbar */}
      <Navbar
        systemStatus={systemStatus}
        user={user}
        onOpenAuth={() => setShowAuthModal(true)}
        onLogout={handleLogout}
        onOpenHistory={() => setShowHistoryModal(true)}
        onOpenStats={() => setShowStatsModal(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Hero Section (Matching deepfake.mp4) */}
        <section className="text-center space-y-4 py-2">
          
          {/* Subtitle Pill Badge: MULTI-MODAL DETECTION ENGINE */}
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-cyan-950/70 border border-cyan-500/30 text-cyan-400 text-[11px] font-bold tracking-wider uppercase">
            <span>MULTI-MODAL DETECTION ENGINE</span>
          </div>

          {/* Main Title: Detect Deepfakes, AI Images & Edits */}
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight font-['Outfit'] text-white">
            Detect Deepfakes, <br className="hidden sm:inline" />
            <span className="text-white">AI Images & Edits</span>
          </h1>

          {/* Subtext Paragraph */}
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Dual-layer analysis: our Deep Learning model detects face-swaps while Error Level Analysis catches AI-generated content and pixel manipulation.
          </p>

          {/* Feature Pills Row */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2 text-xs font-semibold text-slate-300">
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800">
              <ImageIcon className="w-3.5 h-3.5 text-cyan-400" />
              <span>AI-Generated Images</span>
            </div>
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800">
              <UserCheck className="w-3.5 h-3.5 text-indigo-400" />
              <span>Face Swaps</span>
            </div>
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800">
              <XCircle className="w-3.5 h-3.5 text-rose-400" />
              <span>Edited Photos</span>
            </div>
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800">
              <Film className="w-3.5 h-3.5 text-emerald-400" />
              <span>Videos</span>
            </div>
          </div>

        </section>

        {/* 3 Main Mode Selector Tabs (Matching deepfake.mp4) */}
        <div className="flex justify-center pt-2">
          <div className="inline-flex p-1.5 rounded-2xl bg-slate-900/90 border border-slate-800 space-x-2 text-xs sm:text-sm font-semibold shadow-xl">
            
            {/* Tab 1: Image Analysis */}
            <button
              onClick={() => { setActiveTab('image'); setScanResult(null); }}
              className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl transition-all ${
                activeTab === 'image' 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25 border border-blue-400/40' 
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <ImageIcon className="w-4 h-4" />
              <span>Image Analysis</span>
            </button>

            {/* Tab 2: Use Camera */}
            <button
              onClick={() => { setActiveTab('camera'); setScanResult(null); }}
              className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl transition-all ${
                (activeTab === 'camera' || activeTab === 'webcam') 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25 border border-blue-400/40' 
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Camera className="w-4 h-4" />
              <span>Use Camera</span>
            </button>

            {/* Tab 3: Video Analysis */}
            <button
              onClick={() => { setActiveTab('video'); setScanResult(null); }}
              className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl transition-all ${
                activeTab === 'video' 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25 border border-blue-400/40' 
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Video className="w-4 h-4" />
              <span>Video Analysis</span>
            </button>

          </div>
        </div>

        {/* Tab Content Box */}
        <div className="max-w-3xl mx-auto space-y-8">
          {activePanel}

          {/* Forensic Results Dashboard */}
          {scanResult && (
            <ResultsDisplay
              result={scanResult}
              onOpenElaModal={() => setShowElaModal(true)}
            />
          )}
        </div>

      </main>

      {/* Footer (Matching deepfake.mp4) */}
      <footer className="w-full border-t border-slate-800/80 py-6 mt-16 text-center text-xs text-slate-500 space-y-1">
        <p>DeepShield 4.1 • Dual-Engine Detection (ELA + Deep Learning) • For investigative use only</p>
      </footer>

      {/* Modals */}
      {showElaModal && (
        <ElaHeatmapModal
          result={scanResult}
          heatmapUrl={scanResult.heatmap_url}
          originalPreview={originalPreview}
          onClose={() => setShowElaModal(false)}
        />
      )}

      {showHistoryModal && (
        <HistoryModal onClose={() => setShowHistoryModal(false)} />
      )}

      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onAuthSuccess={(userData) => setUser(userData)}
        />
      )}

      {showStatsModal && (
        <StatsModal onClose={() => setShowStatsModal(false)} />
      )}

    </div>
  );
}

