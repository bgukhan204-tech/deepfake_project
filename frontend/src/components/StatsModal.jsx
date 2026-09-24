import React, { useState, useEffect } from 'react';
import { X, BarChart2, CheckCircle2, AlertTriangle, Shield, Activity, RefreshCw } from 'lucide-react';

export default function StatsModal({ onClose }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="glass-panel w-full max-w-xl rounded-2xl border border-slate-800 p-6 space-y-6 shadow-2xl">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              <BarChart2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white font-['Outfit'] font-extrabold">DeepShield Platform Analytics</h3>
              <p className="text-xs text-slate-400">Global detection metrics and system verification stats</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-400 text-xs flex justify-center items-center space-x-2">
            <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
            <span>Calculating forensic metrics...</span>
          </div>
        ) : (
          <div className="space-y-6">
            
            {/* Stat Counters */}
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-center space-y-1">
                <span className="text-xs text-slate-400 font-semibold uppercase">Total Scans</span>
                <p className="text-2xl font-black text-white font-['Outfit']">{stats?.total_scans || 0}</p>
              </div>

              <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-center space-y-1">
                <span className="text-xs text-emerald-300 font-semibold uppercase">Authentic</span>
                <p className="text-2xl font-black text-emerald-400 font-['Outfit']">{stats?.real_scans || 0}</p>
              </div>

              <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-500/30 text-center space-y-1">
                <span className="text-xs text-rose-300 font-semibold uppercase font-bold">Deepfakes</span>
                <p className="text-2xl font-black text-rose-400 font-['Outfit']">{stats?.manipulated_scans || 0}</p>
              </div>
            </div>

            {/* Platform Metrics */}
            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-3">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Engine Specifications</h4>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex justify-between p-2 rounded bg-slate-950/80">
                  <span className="text-slate-400">Neural Model</span>
                  <span className="text-cyan-400 font-semibold">TFLite MobileNetV2</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950/80">
                  <span className="text-slate-400">ELA Compression</span>
                  <span className="text-cyan-400 font-semibold">JET Heatmap Engine</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950/80">
                  <span className="text-slate-400">Face Detection</span>
                  <span className="text-cyan-400 font-semibold">OpenCV Cascade</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950/80">
                  <span className="text-slate-400">Ensemble Weight</span>
                  <span className="text-cyan-400 font-semibold">50% Model / 35% ELA</span>
                </div>
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
