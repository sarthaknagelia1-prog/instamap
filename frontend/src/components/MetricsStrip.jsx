import React from 'react';
import { TrendingUp, Users, Film, Clock, Inbox } from 'lucide-react';

export default function MetricsStrip({ metrics, trends, bestWindow, pendingApprovalsCount }) {
  const er = (metrics?.average_engagement_rate || 0).toFixed(2);
  const reach = (metrics?.total_reach || 0).toLocaleString();
  const topFormat = metrics?.top_content_type || 'Reel';
  const wow = trends?.week_over_week_delta_pct || 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      {/* Average ER */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-4.5 transition hover:border-[#334155]">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <span>Avg Engagement</span>
          <TrendingUp className="w-4 h-4 text-sky-400" />
        </div>
        <div className="text-2xl font-black text-white mt-1.5">{er}%</div>
        <div className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${wow >= 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'}`}>
            {wow >= 0 ? '+' : ''}{wow.toFixed(1)}% WoW
          </span>
          <span>Trajectory</span>
        </div>
      </div>

      {/* Total Reach */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-4.5 transition hover:border-[#334155]">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <span>Total Reach</span>
          <Users className="w-4 h-4 text-purple-400" />
        </div>
        <div className="text-2xl font-black text-white mt-1.5">{reach}</div>
        <div className="text-xs text-slate-400 mt-1">Analyzed posts</div>
      </div>

      {/* Top Format */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-4.5 transition hover:border-[#334155]">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <span>Top Format</span>
          <Film className="w-4 h-4 text-pink-400" />
        </div>
        <div className="text-2xl font-black text-white mt-1.5 capitalize">{topFormat}</div>
        <div className="text-xs text-slate-400 mt-1">Optimal distribution</div>
      </div>

      {/* Algorithmic Window */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-4.5 transition hover:border-[#334155]">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <span>Sweet Spot Window</span>
          <Clock className="w-4 h-4 text-amber-400" />
        </div>
        <div className="text-sm font-extrabold text-white mt-2 leading-tight">
          {bestWindow || 'Calculating...'}
        </div>
        <div className="text-xs text-slate-400 mt-1">Peak audience cluster</div>
      </div>

      {/* Approval Queue */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-4.5 transition hover:border-[#334155]">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <span>Review Queue</span>
          <Inbox className="w-4 h-4 text-sky-400" />
        </div>
        <div className="text-2xl font-black text-amber-400 mt-1.5">{pendingApprovalsCount}</div>
        <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
          <span>Pending human review</span>
        </div>
      </div>
    </div>
  );
}
