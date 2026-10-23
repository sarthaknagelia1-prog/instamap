import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import LoadingSkeleton from '../common/LoadingSkeleton';
import EmptyState from '../common/EmptyState';
import { Radio, RefreshCw, Flame, ExternalLink, Sparkles, Film, ArrowRight } from 'lucide-react';

export default function TrendRadarView({ onDraftFromTrend, showToast }) {
  const [niche, setNiche] = useState('Tech & AI');
  const [loading, setLoading] = useState(true);
  const [signals, setSignals] = useState([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchTrends = (targetNiche = niche) => {
    setLoading(true);
    api.sniffTrends(targetNiche, 6)
      .then((data) => setSignals(data || []))
      .catch(() => setSignals([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchTrends(niche);
  }, [niche]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const data = await api.sniffTrends(niche, 6);
      setSignals(data || []);
      showToast(`Sniffed ${data.length} fresh trending discussions!`, 'success');
    } catch (err) {
      showToast(`Failed to refresh trends: ${err.message}`, 'error');
    } finally {
      setIsRefreshing(false);
    }
  };

  const niches = [
    'Tech & AI',
    'Personal Finance',
    'Fitness & Health',
    'Fashion & Beauty',
    'Creator Economy',
    'Food & Cooking'
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs text-slate-500 font-semibold">Live Community Signals</span>
          </div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">Real-Time Trend Sniffing Radar</h2>
          <p className="text-xs text-slate-500 mt-1">
            Scans rising debates on Reddit and Google Trends to synthesize viral Instagram hooks before saturation.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <select
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            className="text-xs font-bold bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {niches.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>

          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-xs transition flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Sniffing...' : 'Scan Feeds'}</span>
          </button>
        </div>
      </div>

      {loading && signals.length === 0 ? (
        <LoadingSkeleton rows={4} height="h-36" />
      ) : signals.length === 0 ? (
        <EmptyState
          icon={Radio}
          title="No Trending Signals Found for this Niche"
          description="Click 'Scan Feeds' to query live public discussions and RSS trend feeds."
          actionLabel="Scan Feeds Now"
          onAction={handleRefresh}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {signals.map((sig, idx) => (
            <div
              key={idx}
              className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs hover:border-indigo-300 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700">
                    {sig.source}
                  </span>
                  <div className="flex items-center gap-1 text-[11px] font-bold text-amber-600">
                    <Flame className="w-3.5 h-3.5 fill-current" />
                    <span>Velocity: {Number(sig.velocity_score || 75).toFixed(0)}</span>
                  </div>
                </div>

                <h4 className="text-sm font-bold text-slate-900 mb-2 leading-snug">
                  {sig.topic}
                </h4>

                <p className="text-xs text-slate-500 mb-3 leading-relaxed">
                  {sig.suggested_angle || 'Leverage contrast framing to challenge popular orthodoxy on this topic.'}
                </p>

                {sig.suggested_hook && (
                  <div className="p-3 rounded-lg bg-indigo-50/70 border-l-2 border-indigo-500 text-xs italic text-indigo-950 mb-4">
                    "{sig.suggested_hook}"
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase text-slate-400">
                  Format: {sig.recommended_format || 'Reel'}
                </span>
                <button
                  onClick={() => onDraftFromTrend(sig.topic)}
                  className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                >
                  <span>Convert to Draft</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
