import React from 'react';
import { Shield, BarChart2, History, FileText, User, LogOut } from 'lucide-react';

export default function Navbar({ 
  systemStatus, 
  user, 
  onOpenAuth, 
  onLogout, 
  onOpenHistory, 
  onOpenStats 
}) {
  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo - DeepShield */}
        <div className="flex items-center space-x-3 cursor-pointer">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-500 shadow-lg shadow-blue-500/25 border border-blue-400/30">
            <Shield className="w-5 h-5 text-white" />
            <div className="absolute inset-0 rounded-xl bg-cyan-400 opacity-20 blur-md animate-pulse"></div>
          </div>
          <div>
            <span className="font-extrabold text-2xl tracking-tight text-white font-['Outfit']">
              DeepShield
            </span>
          </div>
        </div>

        {/* Right side controls & AI + ELA Active badge */}
        <div className="flex items-center space-x-3 sm:space-x-4">
          
          {/* Top Right Green Badge from video: AI + ELA Active */}
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-bold shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>AI + ELA Active</span>
          </div>

          <div className="h-4 w-[1px] bg-slate-800"></div>

          <button
            onClick={onOpenStats}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-xs font-medium transition-all"
            title="Global Analytics"
          >
            <BarChart2 className="w-4 h-4 text-cyan-400" />
            <span className="hidden sm:inline">Stats</span>
          </button>

          <button
            onClick={onOpenHistory}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-xs font-medium transition-all"
            title="Scan History Log"
          >
            <History className="w-4 h-4 text-indigo-400" />
            <span className="hidden sm:inline">History</span>
          </button>

          {user ? (
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-indigo-950/50 border border-indigo-500/30 text-xs text-indigo-200">
                <User className="w-3.5 h-3.5 text-indigo-400" />
                <span className="font-semibold">{user.username}</span>
              </div>
              <button
                onClick={onLogout}
                className="p-1.5 rounded-lg bg-slate-900/80 hover:bg-rose-950/50 text-slate-400 hover:text-rose-400 border border-slate-800 transition-all"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-500/20 transition-all"
            >
              <User className="w-3.5 h-3.5" />
              <span>Login</span>
            </button>
          )}
        </div>

      </div>
    </header>
  );
}

