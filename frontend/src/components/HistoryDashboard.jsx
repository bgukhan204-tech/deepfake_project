import React, { useState, useEffect } from 'react';
import { History, RefreshCw, CheckCircle2, AlertTriangle, Filter, Search, FileText } from 'lucide-react';

export default function HistoryDashboard({ onSelectHistoryItem }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL'); // 'ALL', 'REAL', 'MANIPULATED'
  const [searchQuery, setSearchQuery] = useState('');

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
    const matchesFilter = filter === 'ALL' || item.verdict === filter;
    const matchesSearch = !searchQuery || item.filename.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6 shadow-2xl animate-fade-in">
      
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <div className="p-3 rounded-2xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-extrabold text-white font-['Outfit']">Forensic History Dashboard</h3>
            <p className="text-xs text-slate-400">View and inspect prior deepfake scan logs</p>
          </div>
        </div>
        <button
          onClick={fetchHistory}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center space-x-2 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Logs</span>
        </button>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-400">Filter:</span>
          {['ALL', 'REAL', 'MANIPULATED'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                filter === f
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {f === 'REAL' ? 'Authentic' : f === 'MANIPULATED' ? 'Manipulated' : 'All Scans'}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search filename..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* History Items Grid / List */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs flex justify-center items-center space-x-2">
          <RefreshCw className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Loading historical scan logs...</span>
        </div>
      ) : filteredHistory.length === 0 ? (
        <div className="py-16 text-center space-y-3 bg-slate-900/30 rounded-2xl border border-dashed border-slate-800 p-8">
          <FileText className="w-10 h-10 text-slate-600 mx-auto" />
          <p className="text-sm font-semibold text-slate-300">No analyses yet</p>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Upload an image, video, or camera snapshot to perform your first forensic deepfake inspection.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredHistory.map((item) => {
            const isGenuine = item.verdict === 'REAL';
            return (
              <div
                key={item.id}
                onClick={() => onSelectHistoryItem && onSelectHistoryItem(item)}
                className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs transition-all cursor-pointer ${
                  isGenuine
                    ? 'bg-slate-900/60 border-slate-800 hover:border-emerald-500/50'
                    : 'bg-slate-900/60 border-slate-800 hover:border-rose-500/50'
                }`}
              >
                <div className="flex items-center space-x-3 truncate">
                  {item.thumb_base64 ? (
                    <img src={item.thumb_base64} alt="Thumbnail" className="w-12 h-12 rounded-lg object-cover border border-slate-800 flex-shrink-0" />
                  ) : (
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      isGenuine ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                    }`}>
                      {isGenuine ? <CheckCircle2 className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
                    </div>
                  )}
                  <div className="space-y-1 truncate">
                    <div className="flex items-center space-x-2 truncate">
                      <p className="font-bold text-slate-200 text-sm truncate">{item.filename}</p>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 uppercase font-bold">
                        {item.file_type}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      {item.timestamp} • {item.resolution || 'Standard'} • {item.file_size || 'N/A'}
                    </p>
                    {item.reason && (
                      <p className="text-[11px] text-slate-500 truncate max-w-md">
                        {item.reason}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-3 self-end sm:self-center">
                  <div className="text-right space-y-0.5">
                    <span className={`inline-block px-3 py-1 rounded-full font-black text-xs ${
                      isGenuine ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    }`}>
                      {isGenuine ? 'AUTHENTIC' : 'MANIPULATED'} ({item.confidence}%)
                    </span>
                    <p className="text-[10px] text-slate-500">ELA Residual: {item.ela_score}%</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
