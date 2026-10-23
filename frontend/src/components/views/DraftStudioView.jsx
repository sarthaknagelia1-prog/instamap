import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import LoadingSkeleton from '../common/LoadingSkeleton';
import EmptyState from '../common/EmptyState';
import ConfirmModal from '../shell/ConfirmModal';
import {
  PenTool,
  Copy,
  CheckCircle2,
  ExternalLink,
  Film,
  Layers,
  Image,
  Clock,
  Sparkles,
  Share2,
  Bookmark
} from 'lucide-react';

export default function DraftStudioView({ creatorId, showToast }) {
  const [loading, setLoading] = useState(true);
  const [drafts, setDrafts] = useState([]);
  const [statusFilter, setStatusFilter] = useState(''); // '' | 'draft' | 'approved' | 'published'
  const [selectedDraft, setSelectedDraft] = useState(null);
  const [publishModalDraft, setPublishModalDraft] = useState(null);

  const fetchDrafts = () => {
    setLoading(true);
    api.listContentDrafts({
      creator_id: creatorId,
      status: statusFilter || undefined,
    }).then((data) => {
      setDrafts(data || []);
      if (data && data.length > 0 && !selectedDraft) {
        setSelectedDraft(data[0]);
      }
    }).catch(() => setDrafts([]))
    .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDrafts();
  }, [creatorId, statusFilter]);

  const handleCopy = (text, label) => {
    navigator.clipboard.writeText(text);
    showToast(`Copied ${label} to clipboard!`, 'success');
  };

  const handleUpdateStatus = async (draftId, newStatus) => {
    try {
      const updated = await api.updateDraftStatus(draftId, newStatus);
      showToast(`Draft status updated to ${newStatus}!`, 'success');
      setDrafts(prev => prev.map(d => d.id === draftId ? { ...d, status: updated.status } : d));
      if (selectedDraft?.id === draftId) {
        setSelectedDraft(prev => ({ ...prev, status: updated.status }));
      }
    } catch (err) {
      showToast(`Failed to update status: ${err.message}`, 'error');
    }
  };

  const handleConfirmPublish = async (postUrlOrId) => {
    if (!publishModalDraft) return;
    try {
      const res = await api.markDraftPublished(publishModalDraft.id, postUrlOrId);
      showToast(`Draft confirmed as published! External ID recorded.`, 'success');
      setDrafts(prev => prev.map(d => d.id === publishModalDraft.id ? { ...d, status: 'published', published_post_id: postUrlOrId } : d));
      if (selectedDraft?.id === publishModalDraft.id) {
        setSelectedDraft(prev => ({ ...prev, status: 'published', published_post_id: postUrlOrId }));
      }
    } catch (err) {
      showToast(`Error recording publication: ${err.message}`, 'error');
    } finally {
      setPublishModalDraft(null);
    }
  };

  if (loading && drafts.length === 0) {
    return <LoadingSkeleton rows={5} height="h-24" />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">Draft Studio & Publishing Packages</h2>
          <p className="text-xs text-slate-500 mt-1">
            Complete creator assets: Hook &rarr; Value Body &rarr; CTA, ranked hashtags, visual notes, and manual publishing confirmation.
          </p>
        </div>

        {/* Status filters */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg text-xs font-bold">
          {['', 'draft', 'approved', 'published'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1 rounded-md transition capitalize ${
                statusFilter === st ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600'
              }`}
            >
              {st || 'All Drafts'}
            </button>
          ))}
        </div>
      </div>

      {drafts.length === 0 ? (
        <EmptyState
          icon={PenTool}
          title="No Publishing Drafts in this Queue"
          description="Drafts are automatically synthesized when running an autonomous growth cycle."
          actionLabel="View Calendar"
          onAction={() => {}}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Draft List (5 cols) */}
          <div className="lg:col-span-5 space-y-3 max-h-[750px] overflow-y-auto pr-1">
            {drafts.map((d) => {
              const isSelected = selectedDraft?.id === d.id;
              const fmt = (d.content_type || 'reel').toLowerCase();

              return (
                <div
                  key={d.id}
                  onClick={() => setSelectedDraft(d)}
                  className={`
                    bg-white rounded-xl border p-4 shadow-xs cursor-pointer transition text-left
                    ${isSelected ? 'border-indigo-600 ring-2 ring-indigo-500/10' : 'border-slate-200 hover:border-slate-300'}
                  `}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      {fmt}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold capitalize ${
                      d.status === 'published' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                      d.status === 'approved' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' :
                      'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}>
                      {d.status}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-slate-900 mb-1 line-clamp-1">{d.title}</h4>
                  <p className="text-[11px] text-slate-500 italic line-clamp-2 mb-2">"{d.hook}"</p>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono pt-2 border-t border-slate-100">
                    <span>{d.recommended_time || 'Peak Window'}</span>
                    <span>ID: {d.id.substring(0, 8)}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right Selected Draft Full Inspection Package (7 cols) */}
          <div className="lg:col-span-7">
            {selectedDraft ? (
              <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-5">
                {/* Package Header */}
                <div className="flex items-start justify-between border-b border-slate-200 pb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {selectedDraft.content_type}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">Slot: {selectedDraft.recommended_time || '18:00 UTC'}</span>
                    </div>
                    <h3 className="text-base font-extrabold text-slate-900">{selectedDraft.title}</h3>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    {selectedDraft.status !== 'approved' && selectedDraft.status !== 'published' && (
                      <button
                        onClick={() => handleUpdateStatus(selectedDraft.id, 'approved')}
                        className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                      >
                        ✓ Approve
                      </button>
                    )}
                    {selectedDraft.status === 'approved' && (
                      <button
                        onClick={() => setPublishModalDraft(selectedDraft)}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-xs transition flex items-center gap-1"
                      >
                        <Share2 className="w-3.5 h-3.5" />
                        <span>Confirm Manual Publication</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* 1. 3-Second Retention Hook */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                      <span>3-Second Hook (Scroll-Stopper)</span>
                    </span>
                    <button
                      onClick={() => handleCopy(selectedDraft.hook, 'Hook')}
                      className="text-[11px] text-indigo-600 hover:text-indigo-800 font-bold flex items-center gap-1"
                    >
                      <Copy className="w-3 h-3" /> Copy
                    </button>
                  </div>
                  <div className="p-3.5 rounded-xl bg-indigo-50/70 border border-indigo-100 text-xs font-medium text-indigo-950 leading-relaxed italic">
                    "{selectedDraft.hook}"
                  </div>
                </div>

                {/* 2. Tactical Body Copy */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-slate-700">Body Copy & Value Narrative</span>
                    <button
                      onClick={() => handleCopy(selectedDraft.body, 'Body Copy')}
                      className="text-[11px] text-indigo-600 hover:text-indigo-800 font-bold flex items-center gap-1"
                    >
                      <Copy className="w-3 h-3" /> Copy
                    </button>
                  </div>
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 leading-relaxed whitespace-pre-wrap">
                    {selectedDraft.body}
                  </div>
                </div>

                {/* 3. Call to Action (CTA) */}
                <div>
                  <span className="text-xs font-bold text-slate-700 block mb-1.5">Call to Action (CTA)</span>
                  <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 font-semibold">
                    {selectedDraft.call_to_action || 'Save this post for later reference!'}
                  </div>
                </div>

                {/* 4. Ranked Hashtags */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-slate-700">Niche Ranked Hashtags</span>
                    <button
                      onClick={() => handleCopy((selectedDraft.hashtags || []).map(t => '#' + t).join(' '), 'Hashtags')}
                      className="text-[11px] text-indigo-600 hover:text-indigo-800 font-bold flex items-center gap-1"
                    >
                      <Copy className="w-3 h-3" /> Copy All
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {(selectedDraft.hashtags || []).map((t, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-100 text-slate-600 border border-slate-200">
                        #{t}
                      </span>
                    ))}
                  </div>
                </div>

                {/* 5. Visual Notes & Audio Suggestions */}
                <div className="grid grid-cols-2 gap-4 pt-3 border-t border-slate-100 text-xs">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="font-bold text-slate-700 block mb-1">Visual Camera Notes</span>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      {selectedDraft.visual_direction || 'Face-to-camera with high-contrast text overlay in first 3 seconds.'}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="font-bold text-slate-700 block mb-1">Audio Suggestion</span>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      {selectedDraft.audio_suggestion || 'Trending upbeat lo-fi instrumental rhythm.'}
                    </p>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Manual Publishing Confirmation Dialog */}
      <ConfirmModal
        isOpen={Boolean(publishModalDraft)}
        title="Confirm Manual Publication on Instagram"
        message="Enter the Instagram post ID or URL link to track this published post in your historical performance dataset."
        confirmLabel="Confirm & Record Publication"
        requiresInput={true}
        inputLabel="Instagram Post ID or Permalink URL"
        inputPlaceholder="e.g. C_9xYz123 or https://instagram.com/p/..."
        onConfirm={handleConfirmPublish}
        onCancel={() => setPublishModalDraft(null)}
      />
    </div>
  );
}
