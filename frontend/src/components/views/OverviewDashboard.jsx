import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import StatCard from '../common/StatCard';
import EmptyState from '../common/EmptyState';
import LoadingSkeleton from '../common/LoadingSkeleton';
import {
  TrendingUp,
  Users,
  Film,
  Clock,
  Inbox,
  AlertTriangle,
  Play,
  ArrowRight,
  Sparkles,
  BarChart2,
  Calendar,
  CheckCircle2,
  UploadCloud
} from 'lucide-react';

export default function OverviewDashboard({
  creatorId,
  onNavigate,
  onOpenAdvisor,
  onRunCycle,
  isCycleRunning
}) {
  const [loading, setLoading] = useState(true);
  const [perfData, setPerfData] = useState(null);
  const [timeSeries, setTimeSeries] = useState([]);
  const [history, setHistory] = useState([]);
  const [strategy, setStrategy] = useState(null);
  const [chartMetric, setChartMetric] = useState('engagement_rate');

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getAnalyticsPerformance(creatorId).catch(() => null),
      api.getAnalyticsTimeSeries(creatorId, 15).catch(() => ({ series: [] })),
      api.getOrchestratorHistory(creatorId).catch(() => []),
      api.getStrategy(creatorId).catch(() => null),
    ]).then(([perf, ts, hist, strat]) => {
      if (!isMounted) return;
      setPerfData(perf);
      setTimeSeries(ts?.series || []);
      setHistory(Array.isArray(hist) ? hist : []);
      setStrategy(strat);
      setLoading(false);
    });

    return () => { isMounted = false; };
  }, [creatorId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton height="h-28" rows={1} />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <LoadingSkeleton height="h-32" rows={1} />
          <LoadingSkeleton height="h-32" rows={1} />
          <LoadingSkeleton height="h-32" rows={1} />
          <LoadingSkeleton height="h-32" rows={1} />
          <LoadingSkeleton height="h-32" rows={1} />
        </div>
        <LoadingSkeleton height="h-72" rows={1} />
      </div>
    );
  }

  const totalPosts = perfData?.metrics?.total_posts || perfData?.total_posts || 0;

  if (totalPosts === 0) {
    return (
      <EmptyState
        icon={UploadCloud}
        title={`No Post Data Found for ${creatorId}`}
        description="To unlock algorithmic sweet spots, week-over-week trends, and autonomous content schedules, import your creator-owned export file or paste metrics."
        actionLabel="Go to Data Import & Readiness"
        onAction={() => onNavigate('import')}
      />
    );
  }

  const er = perfData?.average_engagement_rate || perfData?.metrics?.average_engagement_rate || 0;
  const reach = perfData?.total_reach || perfData?.metrics?.total_reach || 0;
  const topFormat = perfData?.top_content_type || perfData?.metrics?.top_content_type || 'reel';
  const bestWindow = perfData?.best_posting_window || 'Calculating...';
  const wow = perfData?.trends?.week_over_week_delta_pct || perfData?.week_over_week_delta_pct || 0;

  // Chart coordinate calculations
  const chartPoints = timeSeries.filter(p => p.timestamp);
  const values = chartPoints.map(p => Number(p[chartMetric] || 0));
  const maxVal = Math.max(...values, 1);
  const minVal = Math.min(...values, 0);
  const range = maxVal - minVal || 1;

  return (
    <div className="space-y-6">
      {/* Overview Top Hero Banner */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
              Active Strategy Engine
            </span>
            <span className="text-xs text-slate-400">&bull;</span>
            <span className="text-xs text-slate-500 font-semibold">{totalPosts} Historical Posts Ingested</span>
          </div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">
            Performance & Strategy Command Center
          </h2>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
            Deterministic zero-API analytics engine running offline-first in PostgreSQL. Showing real momentum signals and peak conversion windows.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => onNavigate('calendar')}
            className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-lg transition flex items-center gap-1.5"
          >
            <Calendar className="w-3.5 h-3.5" />
            <span>Weekly Calendar</span>
          </button>
          <button
            onClick={onRunCycle}
            disabled={isCycleRunning}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-xs transition flex items-center gap-1.5"
          >
            <Play className={`w-3.5 h-3.5 fill-current ${isCycleRunning ? 'animate-spin' : ''}`} />
            <span>{isCycleRunning ? 'Running Cycle...' : 'Run Cycle'}</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Avg Engagement Rate"
          value={`${Number(er).toFixed(2)}%`}
          trendDelta={wow}
          trendLabel="WoW Trajectory"
          icon={TrendingUp}
        />
        <StatCard
          title="Total Analyzed Reach"
          value={Number(reach).toLocaleString()}
          subtitle="All ingested posts"
          icon={Users}
        />
        <StatCard
          title="Top Performing Format"
          value={<span className="capitalize">{topFormat}</span>}
          subtitle="Highest distribution score"
          icon={Film}
        />
        <StatCard
          title="Algorithmic Window"
          value={<span className="text-sm font-extrabold text-indigo-950 block">{bestWindow}</span>}
          subtitle="Peak audience density"
          icon={Clock}
        />
        <div
          onClick={() => onNavigate('approvals')}
          className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs hover:border-indigo-300 cursor-pointer transition flex flex-col justify-between"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Review Queue</span>
            <Inbox className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2">
            Action Studio
          </div>
          <div className="text-xs text-indigo-600 font-bold flex items-center gap-1 mt-1">
            <span>Inspect Pending Drafts</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </div>
      </div>

      {/* Performance Time-Series Visual Chart */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">Performance Timeline</h3>
            <p className="text-xs text-slate-500">Historical post engagement velocity over chronological posts.</p>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg">
            <button
              onClick={() => setChartMetric('engagement_rate')}
              className={`px-2.5 py-1 text-xs font-bold rounded-md transition ${
                chartMetric === 'engagement_rate' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Engagement Rate (%)
            </button>
            <button
              onClick={() => setChartMetric('reach')}
              className={`px-2.5 py-1 text-xs font-bold rounded-md transition ${
                chartMetric === 'reach' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Reach
            </button>
            <button
              onClick={() => setChartMetric('likes_count')}
              className={`px-2.5 py-1 text-xs font-bold rounded-md transition ${
                chartMetric === 'likes_count' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Likes
            </button>
          </div>
        </div>

        {/* Responsive SVG Chart */}
        {chartPoints.length > 1 ? (
          <div className="w-full h-56 relative flex flex-col justify-end">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 800 200" preserveAspectRatio="none">
              {/* Grid lines */}
              <line x1="0" y1="20" x2="800" y2="20" stroke="#f1f5f9" strokeWidth="1" strokeDasharray="4 4" />
              <line x1="0" y1="100" x2="800" y2="100" stroke="#f1f5f9" strokeWidth="1" strokeDasharray="4 4" />
              <line x1="0" y1="180" x2="800" y2="180" stroke="#f1f5f9" strokeWidth="1" />

              {/* Area fill */}
              <polygon
                points={`0,180 ${chartPoints.map((p, idx) => {
                  const x = (idx / (chartPoints.length - 1)) * 800;
                  const y = 180 - (((p[chartMetric] || 0) - minVal) / range) * 160;
                  return `${x},${y}`;
                }).join(' ')} 800,180`}
                fill="url(#indigoGradient)"
                opacity="0.15"
              />

              {/* Gradient definition */}
              <defs>
                <linearGradient id="indigoGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4f46e5" />
                  <stop offset="100%" stopColor="#ffffff" />
                </linearGradient>
              </defs>

              {/* Connecting line */}
              <polyline
                fill="none"
                stroke="#4f46e5"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={chartPoints.map((p, idx) => {
                  const x = (idx / (chartPoints.length - 1)) * 800;
                  const y = 180 - (((p[chartMetric] || 0) - minVal) / range) * 160;
                  return `${x},${y}`;
                }).join(' ')}
              />

              {/* Data points */}
              {chartPoints.map((p, idx) => {
                const x = (idx / (chartPoints.length - 1)) * 800;
                const y = 180 - (((p[chartMetric] || 0) - minVal) / range) * 160;
                return (
                  <g key={idx}>
                    <circle cx={x} cy={y} r="4.5" fill="#ffffff" stroke="#4f46e5" strokeWidth="2.5" />
                  </g>
                );
              })}
            </svg>

            {/* X-axis date labels */}
            <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-3 pt-2 border-t border-slate-100">
              <span>{chartPoints[0]?.timestamp ? new Date(chartPoints[0].timestamp).toLocaleDateString() : 'Start'}</span>
              <span>{chartPoints[Math.floor(chartPoints.length / 2)]?.timestamp ? new Date(chartPoints[Math.floor(chartPoints.length / 2)].timestamp).toLocaleDateString() : 'Mid'}</span>
              <span>{chartPoints[chartPoints.length - 1]?.timestamp ? new Date(chartPoints[chartPoints.length - 1].timestamp).toLocaleDateString() : 'Recent'}</span>
            </div>
          </div>
        ) : (
          <div className="h-44 flex items-center justify-center text-xs text-slate-400 border border-slate-100 rounded-xl bg-slate-50">
            More post data points needed to plot a rolling line chart.
          </div>
        )}
      </div>

      {/* Two Column Section: Strategy Summary + Orchestrator Run History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Strategy Snapshot */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">Active Strategy Mix</h3>
              <button
                onClick={() => onNavigate('strategy')}
                className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
              >
                <span>View Full Strategy</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Pillars and format distribution calculated by the Strategy Agent.
            </p>

            {strategy ? (
              <div className="space-y-4">
                {/* Format allocation visual bar */}
                <div>
                  <div className="flex justify-between text-xs font-bold text-slate-700 mb-1.5">
                    <span>Format Distribution</span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      Reel {strategy.format_allocation?.reel || 60}% / Carousel {strategy.format_allocation?.carousel || 30}% / Image {strategy.format_allocation?.image || 10}%
                    </span>
                  </div>
                  <div className="w-full h-3 rounded-full bg-slate-100 overflow-hidden flex">
                    <div style={{ width: `${strategy.format_allocation?.reel || 60}%` }} className="bg-indigo-600 h-full" title="Reels" />
                    <div style={{ width: `${strategy.format_allocation?.carousel || 30}%` }} className="bg-purple-500 h-full" title="Carousels" />
                    <div style={{ width: `${strategy.format_allocation?.image || 10}%` }} className="bg-pink-400 h-full" title="Images" />
                  </div>
                </div>

                {/* Core Pillars */}
                <div className="pt-2">
                  <span className="text-xs font-bold text-slate-700 block mb-2">Core Content Pillars</span>
                  <div className="flex flex-wrap gap-2">
                    {(strategy.core_pillars || ['Educational Teardowns', 'Behind the Scenes', 'Actionable Frameworks', 'Trend Commentary']).map((pillar, idx) => (
                      <span key={idx} className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-50 border border-slate-200 text-slate-700">
                        {pillar}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-6 text-center bg-slate-50 rounded-xl">
                No active strategy saved. Click "Run Cycle" to generate one.
              </div>
            )}
          </div>
        </div>

        {/* Recent Orchestrator Runs */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">Workflow Run History</h3>
              <button
                onClick={() => onNavigate('approvals')}
                className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
              >
                <span>Full Audit Logs</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Audit trail of LangGraph state machine autonomous decisions.
            </p>

            {history.length > 0 ? (
              <div className="space-y-2.5">
                {history.slice(0, 4).map((run) => (
                  <div key={run.job_id} className="p-3 rounded-xl border border-slate-100 bg-slate-50/70 flex items-center justify-between text-xs">
                    <div>
                      <div className="font-bold text-slate-800">
                        Decision: <span className="capitalize text-indigo-700">{run.decision || 'Completed'}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                        Trigger: {run.trigger} &bull; {new Date(run.created_at).toLocaleTimeString()}
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      run.status === 'completed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-200 text-slate-700'
                    }`}>
                      {run.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-6 text-center bg-slate-50 rounded-xl">
                No previous orchestrator runs. Click "Run Cycle" to execute.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
