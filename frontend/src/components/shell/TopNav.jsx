import React from 'react';
import {
  Menu,
  Sparkles,
  Bot,
  Play,
  FileText,
  ChevronDown,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export default function TopNav({
  creators = [],
  selectedCreator,
  onSelectCreator,
  activeViewTitle = 'Overview',
  onOpenAdvisor,
  onOpenBriefing,
  onRunCycle,
  isCycleRunning = false,
  isOnline = true,
  onToggleMobile
}) {
  return (
    <header className="h-16 bg-white border-b border-slate-200 sticky top-0 z-30 flex items-center justify-between px-4 lg:px-8">
      {/* Left title & mobile trigger */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobile}
          className="p-2 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100 lg:hidden"
          aria-label="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight leading-tight">
            {activeViewTitle}
          </h1>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-2.5 sm:gap-3">
        {/* Connection status beacon */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 text-[11px] font-semibold text-slate-600">
          <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-500' : 'bg-rose-500'}`} />
          <span>{isOnline ? 'Backend Online' : 'Connecting...'}</span>
        </div>

        {/* Creator selector */}
        <div className="relative flex items-center">
          <label htmlFor="creator-select" className="sr-only">Select Creator</label>
          <select
            id="creator-select"
            value={selectedCreator}
            onChange={(e) => onSelectCreator(e.target.value)}
            className="appearance-none bg-slate-50 border border-slate-300 hover:border-slate-400 text-slate-800 text-xs font-bold rounded-lg pl-3 pr-8 py-2 outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer transition"
          >
            {creators.length === 0 ? (
              <option value="creator_sarthak">creator_sarthak</option>
            ) : (
              creators.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} ({c.total_posts || 0} posts)
                </option>
              ))
            )}
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 pointer-events-none" />
        </div>

        {/* Run Autonomous Cycle */}
        <button
          onClick={onRunCycle}
          disabled={isCycleRunning}
          title="Executes LangGraph state machine (analyze -> decide -> strategy -> 7-day plan -> drafts)"
          className={`
            inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold text-white transition shadow-xs cursor-pointer
            ${isCycleRunning ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 active:scale-95'}
          `}
        >
          <Play className={`w-3.5 h-3.5 fill-current ${isCycleRunning ? 'animate-spin' : ''}`} />
          <span className="hidden md:inline">{isCycleRunning ? 'Running Cycle...' : 'Run Cycle'}</span>
        </button>

        {/* AI Advisor Button */}
        <button
          onClick={onOpenAdvisor}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 transition shadow-xs"
        >
          <Bot className="w-3.5 h-3.5 text-purple-600" />
          <span className="hidden sm:inline">AI Advisor</span>
        </button>

        {/* Weekly Report Briefing */}
        <button
          onClick={onOpenBriefing}
          className="hidden lg:inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold bg-slate-50 text-slate-700 border border-slate-300 hover:bg-slate-100 transition"
        >
          <FileText className="w-3.5 h-3.5 text-slate-500" />
          <span>Printable Briefing</span>
        </button>
      </div>
    </header>
  );
}
