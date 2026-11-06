import React, { useEffect, useState } from 'react';
import { Gauge, MessageSquareText, ClipboardCheck, Star, RefreshCw } from 'lucide-react';
import { api } from '../../api/client';

const rubricFields = [
  ['task_completion', 'Task completion'],
  ['workflow_efficiency', 'Workflow efficiency'],
  ['learnability', 'Learnability'],
  ['accessibility', 'Accessibility'],
  ['interface_clarity', 'Interface clarity'],
];
const blankRubric = Object.fromEntries(rubricFields.map(([key]) => [key, 80]));

export default function UXQualityView({ showToast }) {
  const [data, setData] = useState(null);
  const [rubric, setRubric] = useState(blankRubric);
  const [notes, setNotes] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = () => api.getUxDashboard().then((value) => { setData(value); setError(''); }).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);
  const saveRubric = async (event) => {
    event.preventDefault(); setBusy(true);
    try {
      await api.saveUxRubric({ ...rubric, notes: notes.trim() || null });
      showToast('Usability review saved.', 'success'); setNotes(''); await load();
    } catch (e) { showToast(`Could not save review: ${e.message}`, 'error'); }
    finally { setBusy(false); }
  };

  if (error) return <div className="rounded-xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700">Unable to load the quality dashboard: {error}</div>;
  if (!data) return <div className="flex items-center gap-2 text-sm text-slate-500"><RefreshCw className="w-4 h-4 animate-spin" />Loading quality data…</div>;

  const dimensions = data.rubric?.dimensions;
  const combinedMessage = data.score_status === 'ready'
    ? data.score_formula
    : data.score_status === 'missing_rubric'
      ? 'Add an expert rubric review. The combined score remains unavailable until both sources are present.'
      : data.score_status === 'stale_rubric'
        ? `The latest rubric is outside the ${data.feedback_window_days}-day window. Record a current assessment before comparing it with recent feedback.`
        : `Needs ${data.minimum_unique_respondents_for_combined_score - data.feedback.unique_respondents} more distinct recent respondents to reduce small-sample noise.`;
  return <div className="space-y-6">
    <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-bold uppercase tracking-wider text-indigo-600">Administration · UX operations</p><h2 className="mt-1 text-2xl font-black tracking-tight">Experience Quality</h2><p className="mt-1 text-sm text-slate-500">Review usability against a consistent rubric and learn from creator feedback.</p></div><button onClick={load} className="inline-flex items-center gap-2 self-start rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold hover:bg-slate-50"><RefreshCw className="w-4 h-4" />Refresh</button></div>
    <p className="rounded-lg bg-indigo-50 px-4 py-3 text-xs text-indigo-900">Feedback scope: {data.feedback_scope === 'all_workspaces' ? 'all workspaces' : `workspace ${data.feedback_scope}`} · Rubric: product-wide · Feedback and score use the last {data.feedback_window_days} days. Ratings are opt-in and may not represent every user.</p>
    <div className="grid gap-4 sm:grid-cols-3">
      <div className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex items-center gap-2 text-sm font-semibold text-slate-500"><Gauge className="w-4 h-4 text-indigo-600" />Combined score</div><div className="mt-3 text-4xl font-black">{data.combined_score ?? '—'}<span className="text-lg text-slate-400">/100</span></div><p className="mt-2 text-xs text-slate-500">{combinedMessage}</p></div>
      <div className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex items-center gap-2 text-sm font-semibold text-slate-500"><ClipboardCheck className="w-4 h-4 text-emerald-600" />Usability rubric</div><div className="mt-3 text-4xl font-black">{data.rubric?.score ?? '—'}<span className="text-lg text-slate-400">/100</span></div><p className="mt-2 text-xs text-slate-500">Latest expert assessment across five dimensions.</p></div>
      <div className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex items-center gap-2 text-sm font-semibold text-slate-500"><Star className="w-4 h-4 text-amber-500" />Creator feedback · {data.feedback_window_days} days</div><div className="mt-3 text-4xl font-black">{data.feedback.average_rating ?? '—'}<span className="text-lg text-slate-400">/5</span></div><p className="mt-2 text-xs text-slate-500">{data.feedback.window_count} responses from {data.feedback.unique_respondents} people · {data.feedback.count} lifetime responses</p><p className="mt-1 text-xs text-slate-500">Mapped user score: {data.feedback.average_rating == null ? '—' : (((data.feedback.average_rating - 1) / 4) * 100).toFixed(1)} / 100</p></div>
    </div>
    {dimensions && <section className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="font-bold">Latest rubric breakdown</h3><p className="mt-1 text-xs text-slate-500">Five equally weighted dimensions · score range 0–100</p><div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">{rubricFields.map(([key, label]) => <div key={key}><div className="flex justify-between text-xs font-semibold"><span>{label}</span><span>{dimensions[key]}</span></div><div className="mt-2 h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-indigo-600" style={{ width: `${dimensions[key]}%` }} /></div></div>)}</div>{data.rubric.notes && <p className="mt-4 whitespace-pre-wrap text-sm text-slate-700">{data.rubric.notes}</p>}<p className="mt-2 text-xs text-slate-500">Evaluated by {data.rubric.evaluator_id} · {new Date(data.rubric.created_at).toLocaleString()}</p></section>}
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
      {data.can_edit_rubric ? <form onSubmit={saveRubric} className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex items-center gap-2"><ClipboardCheck className="w-4 h-4 text-indigo-600" /><h3 className="font-bold">Record a usability review</h3></div><p className="mt-1 text-xs text-slate-500">Score each dimension from 0 to 100. All five dimensions are equally weighted.</p><div className="mt-4 space-y-3">{rubricFields.map(([key, label]) => <label key={key} className="grid grid-cols-[1fr_100px] items-center gap-3 text-sm font-medium">{label}<input type="number" min="0" max="100" value={rubric[key]} onChange={(e) => setRubric((old) => ({ ...old, [key]: Number(e.target.value) }))} className="rounded-lg border border-slate-300 px-3 py-2" /></label>)}</div><textarea value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={1000} rows={2} placeholder="Optional review notes" className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /><button disabled={busy} className="mt-3 w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">{busy ? 'Saving…' : 'Save review'}</button></form> : <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-600">Rubric editing is limited to system administrators. Workspace administrators can review their workspace feedback and the product-wide rubric.</div>}
      <section className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex items-center gap-2"><MessageSquareText className="w-4 h-4 text-indigo-600" /><h3 className="font-bold">Creator feedback</h3></div><p className="mt-1 text-xs text-slate-500">Identified submissions are visible to administrators. Showing the latest 100 responses.</p><div className="mt-4 max-h-[440px] space-y-3 overflow-y-auto">{data.feedback.rows.length === 0 ? <p className="rounded-lg bg-slate-50 p-4 text-sm text-slate-500">No feedback yet. Creators can submit it from the top bar.</p> : data.feedback.rows.map((item) => <article key={item.id} className="rounded-xl border border-slate-200 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><div className="font-semibold">{item.user_id} <span className="font-normal text-slate-400">· {item.workspace_id}</span></div><div className="text-sm font-bold text-amber-600">{item.rating}/5</div></div><div className="mt-1 text-xs text-slate-500">{item.workflow} · {new Date(item.created_at).toLocaleString()}</div>{item.comment && <p className="mt-3 whitespace-pre-wrap text-sm text-slate-700">{item.comment}</p>}</article>)}</div></section>
    </div>
    {data.feedback.workflow_breakdown.length > 0 && <section className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="font-bold">Ratings by workflow</h3><p className="mt-1 text-xs text-slate-500">Recent 1–5 ratings with response counts; small groups are less stable.</p><div className="mt-4 grid gap-4 sm:grid-cols-2">{data.feedback.workflow_breakdown.map((item) => <div key={item.workflow}><div className="flex justify-between gap-3 text-sm"><span className="font-medium">{item.workflow}</span><span className="shrink-0 text-slate-500">{item.average_rating}/5 · n={item.count}</span></div><div className="mt-2 h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-amber-400" style={{ width: `${Math.max(3, item.average_rating / 5 * 100)}%` }} /></div></div>)}</div></section>}
    {data.feedback.trend.length > 0 && <section className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="font-bold">Creator rating trend</h3><p className="mt-1 text-xs text-slate-500">Daily averages · most recent 30 active dates within {data.feedback_window_days} days · {data.feedback.window_count} responses from {data.feedback.unique_respondents} people. Bars use a 0–5 scale.</p><div className="mt-4 flex h-36 items-end gap-1 overflow-x-auto">{data.feedback.trend.slice(-30).map((item) => <div key={item.date} title={`${item.date}: ${item.average_rating}/5 (${item.count} responses from ${item.respondents} people)`} className="flex min-w-5 flex-1 flex-col items-center justify-end gap-1"><div className="w-full max-w-8 rounded-t bg-amber-400" style={{ height: `${Math.max(4, item.average_rating / 5 * 100)}%` }} /><span className="text-[9px] text-slate-400">{item.date.slice(5)}</span></div>)}</div></section>}
    {data.rubric_history.length > 0 && <section className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="font-bold">Rubric score history</h3><p className="mt-1 text-xs text-slate-500">Latest {data.rubric_history.length} assessments · each score averages five equally weighted dimensions.</p><div className="mt-3 flex flex-wrap gap-2">{data.rubric_history.map((item, index) => <div key={`${item.created_at}-${index}`} className="rounded-lg bg-slate-50 px-3 py-2 text-xs"><strong>{item.score}/100</strong><span className="ml-2 text-slate-500">{new Date(item.created_at).toLocaleDateString()}</span></div>)}</div></section>}
  </div>;
}
