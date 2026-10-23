import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import LoadingSkeleton from '../common/LoadingSkeleton';
import EmptyState from '../common/EmptyState';
import ConfirmModal from '../shell/ConfirmModal';
import { ShieldCheck, CheckCircle2, XCircle, Edit3, ArrowRight, Clock, AlertTriangle } from 'lucide-react';

export default function ApprovalsView({ creatorId, showToast }) {
  const [loading, setLoading] = useState(true);
  const [approvals, setApprovals] = useState([]);
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [statusFilter, setStatusFilter] = useState('pending'); // 'pending' | 'approved' | 'rejected' | ''
  const [rejectModalItem, setRejectModalItem] = useState(null);

  const fetchApprovals = () => {
    setLoading(true);
    Promise.all([
      api.listApprovals({ creator_id: creatorId, status: statusFilter || undefined }),
      api.getApprovalStats(creatorId).catch(() => null),
      api.getOrchestratorHistory(creatorId).catch(() => []),
    ]).then(([list, st, hist]) => {
      setApprovals(list || []);
      setStats(st);
      setHistory(Array.isArray(hist) ? hist : []);
    }).catch(() => setApprovals([]))
    .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchApprovals();
  }, [creatorId, statusFilter]);

  const handleDecision = async (approvalId, decision, reason = '') => {
    try {
      await api.decideApproval(approvalId, decision, `Decision submitted via web dashboard`, reason);
      showToast(`Item marked as ${decision}!`, 'success');
      setApprovals(prev => prev.filter(item => item.id !== approvalId));
      if (stats) {
        setStats(prev => ({ ...prev, pending_count: Math.max(0, (prev?.pending_count || 1) - 1) }));
      }
    } catch (err) {
      showToast(`Action failed: ${err.message}`, 'error');
    }
  };

  if (loading && approvals.length === 0) {
    return <LoadingSkeleton rows={4} height="h-28" />;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
              Human-in-the-Loop Review Gate
            </span>
            <span className="text-xs text-slate-400">&bull;</span>
            <span className="text-xs text-slate-500 font-semibold">{creatorId}</span>
          </div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">Review Queue & Workflow History</h2>
          <p className="text-xs text-slate-500 mt-1">
            Zero AI draft is finalized without explicit creator approval. Rejections are safely archived for audit history.
          </p>
        </div>

        {/* Status filter tabs */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg text-xs font-bold">
          {['pending', 'approved', 'rejected', ''].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1 rounded-md transition capitalize ${
                statusFilter === st ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600'
              }`}
            >
              {st || 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Summary Strip */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Awaiting Decision</span>
            <div className="text-2xl font-black text-amber-600 font-mono mt-1">{stats.pending_count || 0}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Approved Items</span>
            <div className="text-2xl font-black text-emerald-600 font-mono mt-1">{stats.approved_count || 0}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Archived Rejections</span>
            <div className="text-2xl font-black text-slate-500 font-mono mt-1">{stats.rejected_count || 0}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Approval Rate</span>
            <div className="text-2xl font-black text-indigo-700 font-mono mt-1">{(stats.approval_rate_pct || 0).toFixed(0)}%</div>
          </div>
        </div>
      )}

      {/* Approvals List */}
      {approvals.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="Review Queue is Clean"
          description="There are currently no items awaiting human review in this category."
        />
      ) : (
        <div className="space-y-4">
          {approvals.map((item) => {
            const p = item.payload_snapshot || {};
            const isDraft = item.item_type === 'content_draft';

            return (
              <div key={item.id} className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-4">
                <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700">
                        {item.item_type.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">Risk: {item.risk_level || 'low'}</span>
                    </div>
                    <h3 className="text-base font-bold text-slate-900">{item.summary}</h3>
                  </div>

                  {item.status === 'pending' && (
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleDecision(item.id, 'approved')}
                        className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-xs transition"
                      >
                        ✓ Approve
                      </button>
                      <button
                        onClick={() => setRejectModalItem(item)}
                        className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-bold rounded-lg transition"
                      >
                        ✕ Reject
                      </button>
                    </div>
                  )}
                </div>

                {/* Content Payload Preview */}
                {isDraft ? (
                  <div className="space-y-2 text-xs">
                    {p.hook && (
                      <div className="p-3 rounded-lg bg-indigo-50/70 border-l-2 border-indigo-500 italic text-indigo-950">
                        "{p.hook}"
                      </div>
                    )}
                    {p.body && (
                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 whitespace-pre-wrap">
                        {p.body}
                      </div>
                    )}
                  </div>
                ) : (
                  <pre className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-[11px] font-mono text-slate-700 overflow-x-auto">
                    {JSON.stringify(p, null, 2)}
                  </pre>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Rejection Modal */}
      <ConfirmModal
        isOpen={Boolean(rejectModalItem)}
        title="Reject & Archive Review Item"
        message="Please provide an optional reason for rejecting this item. Rejections are safely preserved in audit logs."
        confirmLabel="Confirm Rejection"
        isDestructive={true}
        requiresInput={true}
        inputLabel="Reason for Rejection"
        inputPlaceholder="e.g. Tone too promotional, adjust format mix..."
        onConfirm={(reason) => {
          if (rejectModalItem) {
            handleDecision(rejectModalItem.id, 'rejected', reason);
            setRejectModalItem(null);
          }
        }}
        onCancel={() => setRejectModalItem(null)}
      />
    </div>
  );
}
