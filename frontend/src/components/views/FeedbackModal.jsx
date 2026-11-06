import React, { useState } from 'react';
import { X, MessageSquareText } from 'lucide-react';
import { api } from '../../api/client';

export default function FeedbackModal({ onClose, showToast, workflow }) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    try {
      await api.submitUxFeedback({ rating, workflow, comment: comment.trim() || null });
      showToast('Thanks — your feedback was recorded.', 'success');
      onClose();
    } catch (error) {
      showToast(`Could not save feedback: ${error.message}`, 'error');
    } finally { setBusy(false); }
  };

  return <div className="fixed inset-0 z-[60] bg-slate-950/40 grid place-items-center p-4" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <form onSubmit={submit} className="bg-white w-full max-w-md rounded-2xl shadow-xl border border-slate-200 p-6 space-y-4" role="dialog" aria-modal="true" aria-labelledby="feedback-title">
      <div className="flex items-start justify-between">
        <div><div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-700 grid place-items-center mb-3"><MessageSquareText className="w-4 h-4" /></div><h2 id="feedback-title" className="text-lg font-bold">How was this workflow?</h2><p className="text-sm text-slate-500 mt-1">Your feedback is linked to your signed-in account and visible to workspace administrators.</p></div>
        <button type="button" onClick={onClose} aria-label="Close feedback" className="p-2 text-slate-400 hover:text-slate-700"><X className="w-4 h-4" /></button>
      </div>
      <label className="block text-sm font-semibold">Workflow
        <select value={workflow} disabled className="mt-1.5 block w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm"><option>{workflow}</option></select>
      </label>
      <label className="block text-sm font-semibold">Overall rating
        <select value={rating} onChange={(e) => setRating(Number(e.target.value))} className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
          <option value={5}>5 — Excellent</option><option value={4}>4 — Good</option><option value={3}>3 — Okay</option><option value={2}>2 — Difficult</option><option value={1}>1 — Poor</option>
        </select>
      </label>
      <label className="block text-sm font-semibold">Comment <span className="font-normal text-slate-400">(optional)</span>
        <textarea value={comment} onChange={(e) => setComment(e.target.value)} maxLength={1000} rows={4} placeholder="What worked well or slowed you down?" className="mt-1.5 block w-full resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500" />
      </label>
      <button disabled={busy} className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-indigo-700 disabled:opacity-50">{busy ? 'Saving…' : 'Send feedback'}</button>
    </form>
  </div>;
}
