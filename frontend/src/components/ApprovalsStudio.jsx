import React from 'react';
import { ShieldCheck, Check, Edit2, X, RefreshCw } from 'lucide-react';

export default function ApprovalsStudio({ approvals, onDecide, onRefresh }) {
  const pending = approvals.filter((a) => a.status === 'pending');

  return (
    <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-6">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-sky-400" />
            Human-in-the-Loop Review Queue
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Every AI-generated post draft or strategy pivot requires your explicit blessing before publishing.
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="flex items-center gap-2 bg-[#1e293b] hover:bg-[#334155] text-white text-xs font-semibold px-3 py-2 rounded-lg border border-[#334155] transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Queue</span>
        </button>
      </div>

      {pending.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          <ShieldCheck className="w-10 h-10 mx-auto text-emerald-400 mb-2" />
          <p className="font-semibold text-white">Review Queue is Clean</p>
          <p className="text-xs mt-1">No pending drafts or strategy changes awaiting your approval.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {pending.map((item) => {
            const p = item.payload || {};
            return (
              <div
                key={item.approval_id}
                className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-5 items-start"
              >
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-sky-500/15 text-sky-400">
                      {item.item_type.replace('_', ' ')}
                    </span>
                    <h4 className="font-bold text-sm text-white">
                      {p.title || 'Draft Ready for Review'}
                    </h4>
                  </div>
                  <div className="text-xs text-slate-400">
                    ID: <code className="text-sky-400 font-mono">{item.item_id.substring(0, 8)}...</code> &bull; Priority: <strong>{item.priority}</strong> &bull; Reason: {item.reason}
                  </div>

                  {item.item_type === 'content_draft' ? (
                    <div className="bg-[#090d16] border border-[#1f293d] rounded-lg p-4 space-y-2 text-xs">
                      {p.hook && (
                        <div className="text-pink-400 font-semibold italic">
                          Hook: "{p.hook}"
                        </div>
                      )}
                      <div className="text-slate-300 whitespace-pre-wrap leading-relaxed">
                        {p.body}
                      </div>
                      {p.call_to_action && (
                        <div className="text-slate-400">
                          <strong className="text-white">CTA:</strong> {p.call_to_action}
                        </div>
                      )}
                      {p.hashtags && p.hashtags.length > 0 && (
                        <div className="text-sky-400 font-mono text-[11px]">
                          {p.hashtags.map((t) => '#' + t).join(' ')}
                        </div>
                      )}
                    </div>
                  ) : (
                    <pre className="bg-[#090d16] border border-[#1f293d] rounded-lg p-3 text-[11px] font-mono text-slate-300 overflow-x-auto">
                      {JSON.stringify(p, null, 2)}
                    </pre>
                  )}
                </div>

                <div className="flex flex-col gap-2 min-w-[140px]">
                  <button
                    onClick={() => onDecide(item.approval_id, 'approved')}
                    className="flex items-center justify-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs py-2 px-3 rounded-lg transition"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Approve</span>
                  </button>
                  <button
                    onClick={() => onDecide(item.approval_id, 'revision_requested')}
                    className="flex items-center justify-center gap-1.5 bg-[#334155] hover:bg-[#475569] text-white font-semibold text-xs py-2 px-3 rounded-lg transition"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                    <span>Request Edit</span>
                  </button>
                  <button
                    onClick={() => onDecide(item.approval_id, 'rejected')}
                    className="flex items-center justify-center gap-1.5 bg-rose-900/60 hover:bg-rose-800 text-rose-200 font-semibold text-xs py-2 px-3 rounded-lg transition"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Reject</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
