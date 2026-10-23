import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import LoadingSkeleton from '../common/LoadingSkeleton';
import EmptyState from '../common/EmptyState';
import { Calendar, RefreshCw, ArrowRight, Clock, Film, Layers, Image, CheckCircle2 } from 'lucide-react';

export default function CalendarView({ creatorId, onNavigateToDrafts, showToast }) {
  const [loading, setLoading] = useState(true);
  const [plan, setPlan] = useState(null);
  const [isReplanning, setIsReplanning] = useState(false);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'

  const fetchPlan = () => {
    setLoading(true);
    api.getContentPlan(creatorId)
      .then((data) => setPlan(data))
      .catch(() => setPlan(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchPlan();
  }, [creatorId]);

  const handleReplan = async () => {
    setIsReplanning(true);
    try {
      const res = await api.generateContentPlan(creatorId, 1);
      setPlan(res);
      showToast('Fresh 7-day schedule generated successfully!', 'success');
    } catch (err) {
      showToast(`Failed to generate schedule: ${err.message}`, 'error');
    } finally {
      setIsReplanning(false);
    }
  };

  if (loading) {
    return <LoadingSkeleton rows={4} height="h-32" />;
  }

  const items = plan?.scheduled_items || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
              Week {plan?.week_number || 1} Content Blueprint
            </span>
            <span className="text-xs text-slate-400">&bull;</span>
            <span className="text-xs text-slate-500 font-semibold">{items.length} Planned Slots</span>
          </div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">7-Day Content Calendar</h2>
          <p className="text-xs text-slate-500 mt-1">
            High-converting schedule matching creator format allocations and peak historical windows.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <div className="flex items-center bg-slate-100 p-1 rounded-lg text-xs font-bold">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1 rounded-md transition ${viewMode === 'grid' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600'}`}
            >
              Day Cards
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1 rounded-md transition ${viewMode === 'list' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600'}`}
            >
              Table List
            </button>
          </div>

          <button
            onClick={handleReplan}
            disabled={isReplanning}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-xs transition flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isReplanning ? 'animate-spin' : ''}`} />
            <span>{isReplanning ? 'Re-planning...' : 'Re-plan 7-Day Week'}</span>
          </button>
        </div>
      </div>

      {/* Calendar Grid / List */}
      {items.length === 0 ? (
        <EmptyState
          icon={Calendar}
          title="No Scheduled Items Formulated"
          description="Click 'Re-plan 7-Day Week' to run the Content Planning Agent and construct your schedule."
          actionLabel="Generate Schedule Now"
          onAction={handleReplan}
        />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((slot, idx) => {
            const fmt = (slot.content_type || 'reel').toLowerCase();
            const Icon = fmt === 'reel' ? Film : fmt === 'carousel' ? Layers : Image;

            return (
              <div
                key={idx}
                className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs hover:border-indigo-300 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-extrabold text-sm text-indigo-900">{slot.day || `Day ${idx + 1}`}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700 flex items-center gap-1">
                      <Icon className="w-3 h-3 text-indigo-600" />
                      {fmt}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-slate-900 mb-1 leading-snug">
                    {slot.concept_theme || slot.title || 'Growth Topic Strategy'}
                  </h4>

                  <p className="text-xs text-slate-500 mb-3 leading-relaxed">
                    {slot.concept_angle || 'Tactical breakdown tailored to creator authority pillar.'}
                  </p>

                  {slot.hook_quote && (
                    <div className="p-3 rounded-lg bg-indigo-50/60 border-l-2 border-indigo-500 text-xs italic text-indigo-950 mb-4">
                      "{slot.hook_quote}"
                    </div>
                  )}
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-slate-500 font-mono text-[11px]">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>{slot.scheduled_time || '18:00 UTC'}</span>
                  </div>

                  <button
                    onClick={() => onNavigateToDrafts(slot.content_draft_id || '')}
                    className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                  >
                    <span>Inspect Draft</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200/90 overflow-hidden shadow-xs">
          <table className="w-full text-xs text-left border-collapse">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4">Day</th>
                <th className="py-3 px-4">Time</th>
                <th className="py-3 px-4">Format</th>
                <th className="py-3 px-4">Concept Angle</th>
                <th className="py-3 px-4">Hook</th>
                <th className="py-3 px-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {items.map((slot, idx) => (
                <tr key={idx} className="hover:bg-slate-50/70">
                  <td className="py-3 px-4 font-bold text-indigo-900">{slot.day || `Day ${idx + 1}`}</td>
                  <td className="py-3 px-4 font-mono text-slate-500">{slot.scheduled_time || '18:00 UTC'}</td>
                  <td className="py-3 px-4 capitalize font-semibold text-slate-700">{slot.content_type || 'reel'}</td>
                  <td className="py-3 px-4 text-slate-900 max-w-xs">{slot.concept_theme || slot.concept_angle}</td>
                  <td className="py-3 px-4 text-slate-500 italic max-w-sm truncate">"{slot.hook_quote || '—'}"</td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => onNavigateToDrafts(slot.content_draft_id || '')}
                      className="text-xs font-bold text-indigo-600 hover:text-indigo-800"
                    >
                      Draft &rarr;
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
