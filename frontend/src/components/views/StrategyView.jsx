import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import LoadingSkeleton from '../common/LoadingSkeleton';
import EmptyState from '../common/EmptyState';
import { Compass, RefreshCw, Sparkles, CheckCircle2, ArrowRight, Layers, Target, Clock } from 'lucide-react';

export default function StrategyView({ creatorId, showToast }) {
  const [loading, setLoading] = useState(true);
  const [strategy, setStrategy] = useState(null);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [customNiche, setCustomNiche] = useState('');
  const [customAudience, setCustomAudience] = useState('');

  const fetchStrategy = () => {
    setLoading(true);
    api.getStrategy(creatorId)
      .then((data) => {
        setStrategy(data);
        setCustomNiche(data?.target_audience || '');
      })
      .catch(() => setStrategy(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchStrategy();
  }, [creatorId]);

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    try {
      const res = await api.generateStrategy({
        creator_id: creatorId,
        niche: customNiche || undefined,
        audience: customAudience || undefined,
        use_llm: false,
      });
      setStrategy(res);
      showToast('Growth strategy generated successfully!', 'success');
    } catch (err) {
      showToast(`Failed to generate strategy: ${err.message}`, 'error');
    } finally {
      setIsRegenerating(false);
    }
  };

  if (loading) {
    return <LoadingSkeleton rows={5} height="h-28" />;
  }

  const alloc = strategy?.format_allocation || { reel: 60, carousel: 30, image: 10 };
  const pillars = strategy?.core_pillars || ['Educational Breakdowns', 'Actionable Frameworks', 'Behind the Scenes', 'Industry Debates'];
  const priorities = strategy?.strategic_priorities || [
    'Prioritize 3-second hook retention to maximize Reel recommendation velocity',
    'Structure Carousels as 7-slide actionable checklists to generate high save rates',
    'Schedule publishing strictly during peak algorithmic cluster windows',
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
              Active Strategy Engine
            </span>
            <span className="text-xs text-slate-400">&bull;</span>
            <span className="text-xs text-slate-500 font-semibold">{creatorId}</span>
          </div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">Autonomous Growth Strategy</h2>
          <p className="text-xs text-slate-500 mt-1">
            Deterministic allocation algorithm deriving optimal formats and pillars from historical engagement.
          </p>
        </div>

        <button
          onClick={handleRegenerate}
          disabled={isRegenerating}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-xs transition flex items-center gap-1.5 shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />
          <span>{isRegenerating ? 'Formulating Strategy...' : 'Regenerate Strategy'}</span>
        </button>
      </div>

      {/* Format Allocation */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight mb-2">
          Recommended Content Format Allocation
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Allocates publishing frequency based on distribution conversion rates.
        </p>

        {/* Visual Bar */}
        <div className="w-full h-4 rounded-full bg-slate-100 overflow-hidden flex mb-4">
          <div style={{ width: `${alloc.reel || 60}%` }} className="bg-indigo-600 h-full" title="Reels" />
          <div style={{ width: `${alloc.carousel || 30}%` }} className="bg-purple-500 h-full" title="Carousels" />
          <div style={{ width: `${alloc.image || 10}%` }} className="bg-pink-400 h-full" title="Static Images" />
        </div>

        <div className="grid grid-cols-3 gap-4 text-xs">
          <div className="p-3 rounded-xl border border-indigo-100 bg-indigo-50/50">
            <span className="text-indigo-900 font-bold block">Reels (Discovery)</span>
            <span className="text-2xl font-black text-indigo-700 font-mono mt-1 block">{alloc.reel || 60}%</span>
            <span className="text-[11px] text-slate-500 mt-0.5 block">High reach & non-follower acquisition</span>
          </div>
          <div className="p-3 rounded-xl border border-purple-100 bg-purple-50/50">
            <span className="text-purple-900 font-bold block">Carousels (Retention)</span>
            <span className="text-2xl font-black text-purple-700 font-mono mt-1 block">{alloc.carousel || 30}%</span>
            <span className="text-[11px] text-slate-500 mt-0.5 block">Deep saves & multi-slide watch time</span>
          </div>
          <div className="p-3 rounded-xl border border-pink-100 bg-pink-50/50">
            <span className="text-pink-900 font-bold block">Images / Quotes (Community)</span>
            <span className="text-2xl font-black text-pink-700 font-mono mt-1 block">{alloc.image || 10}%</span>
            <span className="text-[11px] text-slate-500 mt-0.5 block">Lightweight discussion & commentary</span>
          </div>
        </div>
      </div>

      {/* Pillars & Cadence Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Core Pillars */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900">Core Content Pillars</h3>
          </div>
          <p className="text-xs text-slate-500 mb-4">
            The 4 content themes that maximize creator authority and audience retention.
          </p>

          <div className="space-y-2.5">
            {pillars.map((pillar, idx) => (
              <div key={idx} className="p-3 rounded-xl border border-slate-100 bg-slate-50 flex items-center gap-3">
                <span className="w-6 h-6 rounded-lg bg-indigo-100 text-indigo-700 font-black text-xs flex items-center justify-center shrink-0">
                  {idx + 1}
                </span>
                <span className="text-xs font-bold text-slate-800">{pillar}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Posting Cadence & Priorities */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-4 h-4 text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">Recommended Posting Cadence</h3>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 mb-4">
              <span className="text-xs font-semibold text-slate-400 uppercase">Target Publishing Rhythm</span>
              <div className="text-base font-extrabold text-slate-900 mt-1">
                {strategy?.target_cadence || '4-5 posts per week'}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Aligned with peak Friday/Sunday algorithmic velocity windows.
              </span>
            </div>

            <span className="text-xs font-bold text-slate-700 block mb-2">Strategic Directives</span>
            <ul className="space-y-2 text-xs text-slate-600">
              {priorities.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
