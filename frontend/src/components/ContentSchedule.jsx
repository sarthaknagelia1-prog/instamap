import React from 'react';
import { Calendar, RefreshCw, Clock, Target } from 'lucide-react';

export default function ContentSchedule({ plan, onReplan, isReplanning }) {
  const items = plan?.scheduled_items || [];

  return (
    <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-6">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-sky-400" />
            What to Post This Week (Actionable 7-Day Plan)
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Data-backed blueprint formulated from your highest-converting formats and peak posting window.
          </p>
        </div>
        <button
          onClick={onReplan}
          disabled={isReplanning}
          className="flex items-center gap-2 bg-[#1e293b] hover:bg-[#334155] text-white text-xs font-semibold px-3 py-2 rounded-lg border border-[#334155] transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isReplanning ? 'animate-spin' : ''}`} />
          <span>{isReplanning ? 'Re-planning...' : 'Re-plan Week'}</span>
        </button>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          <Calendar className="w-10 h-10 mx-auto text-slate-600 mb-2" />
          <p className="font-semibold text-white">No active plan found</p>
          <p className="text-xs mt-1">Click "Re-plan Week" to generate a fresh 7-day schedule.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item, idx) => (
            <div
              key={idx}
              className="bg-[#1e293b] border border-[#334155] rounded-xl p-4 flex flex-col gap-2.5 transition hover:border-sky-400/50"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-sky-400">{item.day}</span>
                <span
                  className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                    item.content_type === 'reel'
                      ? 'bg-purple-500/15 text-purple-300'
                      : item.content_type === 'carousel'
                      ? 'bg-sky-500/15 text-sky-300'
                      : 'bg-emerald-500/15 text-emerald-300'
                  }`}
                >
                  {item.content_type}
                </span>
              </div>
              <div className="font-bold text-sm text-white">{item.theme}</div>
              <div className="text-xs text-slate-400 leading-relaxed">{item.concept_angle}</div>
              {item.hook_preview && (
                <div className="bg-[#090d16]/70 border-l-2 border-pink-500 px-3 py-2 rounded text-xs italic text-slate-300 mt-1">
                  "{item.hook_preview}"
                </div>
              )}
              <div className="mt-auto pt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-[#334155]/60">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3 text-sky-400" />
                  {item.scheduled_time || 'Optimal'}
                </span>
                <span className="flex items-center gap-1">
                  <Target className="w-3 h-3 text-emerald-400" />
                  {item.target_metric || 'engagement'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
