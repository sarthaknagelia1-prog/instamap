import React from 'react';
import { Zap, Play, BookOpen, FileText, Activity } from 'lucide-react';

export default function Navbar({
  creators,
  selectedCreator,
  onSelectCreator,
  onRunCycle,
  isCycleRunning,
  onOpenGuide,
  onOpenBriefing,
  isOnline,
}) {
  return (
    <header className="sticky top-0 z-50 bg-[#111827]/90 backdrop-blur-md border-b border-[#1f293d] px-6 py-3.5 flex items-center justify-between gap-4 flex-wrap">
      {/* Brand */}
      <div className="flex items-center gap-3 font-extrabold text-lg tracking-tight">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-pink-500 via-purple-500 to-sky-400 flex items-center justify-center text-white shadow-md shadow-pink-500/20">
          <Zap className="w-4 h-4" />
        </div>
        <span className="text-white">InstaMap</span>
        <span className="text-[11px] uppercase tracking-wider font-bold bg-sky-500/10 text-sky-400 px-2 py-0.5 rounded-full border border-sky-500/20">
          Growth Engine
        </span>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Connection status */}
        <div className="flex items-center gap-2 text-xs text-slate-400 px-2 py-1">
          <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-500'}`} />
          <span>{isOnline ? 'Engine Online' : 'Engine Offline'}</span>
        </div>

        {/* Creator Picker */}
        <div className="flex items-center gap-2 bg-[#090d16] border border-[#334155] rounded-lg px-3 py-1.5 text-xs">
          <label className="text-slate-400 font-semibold">Creator:</label>
          <select
            value={selectedCreator}
            onChange={(e) => onSelectCreator(e.target.value)}
            className="bg-transparent text-sky-400 font-mono font-bold outline-none cursor-pointer"
          >
            {creators.map((c) => (
              <option key={c.id} value={c.id} className="bg-[#1e293b] text-white">
                {c.id} ({c.total_posts} posts)
              </option>
            ))}
          </select>
        </div>

        {/* Run Cycle Button */}
        <button
          onClick={onRunCycle}
          disabled={isCycleRunning}
          className="flex items-center gap-2 bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white font-semibold text-xs px-3.5 py-2 rounded-lg shadow-md shadow-sky-600/25 transition disabled:opacity-50"
        >
          <Play className={`w-3.5 h-3.5 ${isCycleRunning ? 'animate-spin' : ''}`} />
          <span>{isCycleRunning ? 'Running Cycle...' : 'Run Autonomous Cycle'}</span>
        </button>

        {/* User Guide */}
        <button
          onClick={onOpenGuide}
          className="flex items-center gap-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-200 font-semibold text-xs px-3 py-2 rounded-lg border border-[#334155] transition"
        >
          <BookOpen className="w-3.5 h-3.5 text-sky-400" />
          <span>User Guide</span>
        </button>

        {/* Weekly Briefing */}
        <button
          onClick={onOpenBriefing}
          className="flex items-center gap-1.5 bg-[#1e293b] hover:bg-[#334155] text-slate-200 font-semibold text-xs px-3 py-2 rounded-lg border border-[#334155] transition"
        >
          <FileText className="w-3.5 h-3.5 text-purple-400" />
          <span>Weekly Briefing</span>
        </button>
      </div>
    </header>
  );
}
