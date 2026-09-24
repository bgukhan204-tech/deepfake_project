import React, { useState, useEffect } from 'react';
import { X, History, RefreshCw, CheckCircle2, AlertTriangle, Filter } from 'lucide-react';

export default function HistoryModal({ onClose }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL'); // 'ALL', 'REAL', 'MANIPULATED'

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/history', { credentials: 'include' });
      const data = await res.json();
      if (data.history) {
        setHistory(data.history);
      }
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const filteredHistory = history.filter(item => {
    if (filter === 'ALL') return true;
    return item.verdict === filter;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="glass-panel w-full max-w-4xl rounded-2xl border border-slate-800 p-6 space-y-6 max-h-[85vh] flex flex-col shadow-2xl">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white font-['Outfit']">Forensic Scan History Log</h3>
              <p className="text-xs text-slate-400">Recorded scan results saved to DeepShield database</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={fetchHistory}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-400">Filter:</span>
          {['ALL', 'REAL', 'MANIPULATED'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                filter === f
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-slate-800/80 text-slate-400 hover:text-slate-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Table Content */}
        <div className="flex-1 overflow-y-auto pr-2">
          {loading ? (
            <div className="py-12 text-center text-slate-400 text-xs flex justify-center items-center space-x-2">
              <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
              <span>Fetching scan records...</span>
            </div>
          ) : filteredHistory.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-sm">
              No scan history records found.
            </div>
          ) : (
            <div className="space-y-2">
              {filteredHistory.map((item) => (
                <div
                  key={item.id}
                  className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs ${
                    item.verdict === 'REAL'
                      ? 'bg-emerald-950/20 border-emerald-500/20'
                      : 'bg-rose-950/20 border-rose-500/20'
                  }`}
                >
                  <div className="flex items-center space-x-3 truncate">
                    {item.verdict === 'REAL' ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
                    )}
                    <div className="truncate">
                      <p className="font-semibold text-slate-200 truncate">{item.filename}</p>
                      <p className="text-[11px] text-slate-400">{item.timestamp} • Type: {item.file_type}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 self-end sm:self-center">
                    <span className="text-slate-400">ELA: <b className="text-slate-200">{item.ela_score}%</b></span>
                    <span className={`px-2.5 py-1 rounded-full font-bold ${
                      item.verdict === 'REAL' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                    }`}>
                      {item.verdict} ({item.confidence}%)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
