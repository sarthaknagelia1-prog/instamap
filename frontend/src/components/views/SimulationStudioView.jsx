import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import {
  Activity,
  TrendingUp,
  BarChart2,
  Calendar,
  Layers,
  Sparkles,
  RefreshCw,
  ArrowRight,
  ShieldAlert,
  CheckCircle2,
  Sliders,
  Zap
} from 'lucide-react';

export default function SimulationStudioView({ creatorId, showToast }) {
  const [activeTab, setActiveTab] = useState('growth'); // 'growth' | 'post'

  // Growth simulation state
  const [horizonDays, setHorizonDays] = useState(60);
  const [isSimulatingGrowth, setIsSimulatingGrowth] = useState(false);
  const [growthResult, setGrowthResult] = useState(null);

  // Single post simulation state
  const [postHook, setPostHook] = useState('How I scaled my Instagram audience in 30 days without paid ads');
  const [postFormat, setPostFormat] = useState('REEL');
  const [postCaption, setPostCaption] = useState('Full step-by-step framework below. Save this post for your next content batch!');
  const [postDraws, setPostDraws] = useState(500);
  const [isSimulatingPost, setIsSimulatingPost] = useState(false);
  const [postResult, setPostResult] = useState(null);

  // Auto-run growth simulation on initial mount or creator change
  useEffect(() => {
    handleRunGrowthSimulation();
  }, [creatorId, horizonDays]);

  const handleRunGrowthSimulation = async () => {
    setIsSimulatingGrowth(true);
    try {
      const res = await api.simulateGrowth({
        creator_id: creatorId,
        days: horizonDays,
        iterations: 100,
      });
      setGrowthResult(res);
    } catch (err) {
      showToast(`Growth simulation error: ${err.message}`, 'error');
    } finally {
      setIsSimulatingGrowth(false);
    }
  };

  const handleRunPostSimulation = async (e) => {
    if (e) e.preventDefault();
    setIsSimulatingPost(true);
    try {
      const res = await api.simulatePost({
        creator_id: creatorId,
        hook: postHook,
        content_type: postFormat,
        caption: postCaption,
        draws: postDraws,
      });
      setPostResult(res);
      showToast('Post reach Monte Carlo simulation complete!', 'success');
    } catch (err) {
      showToast(`Post simulation failed: ${err.message}`, 'error');
    } finally {
      setIsSimulatingPost(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Growth & Content Simulation Studio</h1>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 border border-blue-200">
              Monte Carlo Engine
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Simulate future audience trajectories and calculate stochastic reach distributions across strategic scenarios.
          </p>
        </div>

        {/* Tab switch buttons */}
        <div className="flex items-center bg-slate-200/80 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab('growth')}
            className={`px-3.5 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'growth'
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            Growth Trajectory (30-90 Days)
          </button>
          <button
            onClick={() => setActiveTab('post')}
            className={`px-3.5 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'post'
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" />
            What-If Post Simulator
          </button>
        </div>
      </div>

      {/* ============================================================== */}
      {/* TAB 1: 30 / 60 / 90 DAY GROWTH SIMULATION                      */}
      {/* ============================================================== */}
      {activeTab === 'growth' && (
        <div className="space-y-6">
          {/* Controls Bar */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="text-xs font-bold text-slate-700">Forecast Horizon:</span>
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
                {[30, 60, 90].map((d) => (
                  <button
                    key={d}
                    onClick={() => setHorizonDays(d)}
                    className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
                      horizonDays === d
                        ? 'bg-indigo-600 text-white shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {d} Days
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleRunGrowthSimulation}
              disabled={isSimulatingGrowth}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white text-xs font-semibold rounded-lg shadow-sm inline-flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSimulatingGrowth ? 'animate-spin' : ''}`} />
              {isSimulatingGrowth ? 'Simulating 100 Iterations...' : 'Re-run Monte Carlo Simulation'}
            </button>
          </div>

          {growthResult && growthResult.summary ? (
            <>
              {/* Scenario Comparison Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {/* Baseline Scenario */}
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Scenario 1</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      Baseline
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900">Current Trajectory</h3>
                  <p className="text-xs text-slate-500">Continuing historical average cadence & format distribution.</p>
                  <div className="pt-2 border-t border-slate-100 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Projected Posts:</span>
                      <span className="font-semibold text-slate-900">{growthResult.summary.baseline.projected_posts}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Projected Reach:</span>
                      <span className="font-bold text-slate-900">{growthResult.summary.baseline.projected_reach.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Estimated Followers:</span>
                      <span className="font-semibold text-slate-900">+{growthResult.summary.baseline.projected_followers.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Weekly Cadence:</span>
                      <span className="font-semibold text-slate-900">{growthResult.summary.baseline.cadence_posts_per_week} / week</span>
                    </div>
                  </div>
                </div>

                {/* Recommended Strategy (Highlighted) */}
                <div className="bg-indigo-50/70 border-2 border-indigo-500 rounded-xl p-5 shadow-sm space-y-3 relative overflow-hidden">
                  <div className="absolute top-0 right-0 bg-indigo-600 text-white text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded-bl">
                    Recommended
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider">Scenario 2</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-200 text-indigo-900">
                      +{growthResult.summary.recommended.reach_lift_vs_baseline_pct}% Reach
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-indigo-950">Recommended Strategy</h3>
                  <p className="text-xs text-indigo-800">60/30/10 format mix, peak posting windows, and high-retention hooks.</p>
                  <div className="pt-2 border-t border-indigo-200 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-indigo-800">Projected Posts:</span>
                      <span className="font-bold text-indigo-950">{growthResult.summary.recommended.projected_posts}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-indigo-800">Projected Reach:</span>
                      <span className="font-extrabold text-indigo-950">{growthResult.summary.recommended.projected_reach.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-indigo-800">Estimated Followers:</span>
                      <span className="font-bold text-indigo-950">+{growthResult.summary.recommended.projected_followers.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-indigo-800">Weekly Cadence:</span>
                      <span className="font-bold text-indigo-950">{growthResult.summary.recommended.cadence_posts_per_week} / week</span>
                    </div>
                  </div>
                </div>

                {/* Aggressive Sprint */}
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Scenario 3</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                      Aggressive
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900">Growth Sprint</h3>
                  <p className="text-xs text-slate-500">1.8x cadence, rapid trend radar capitalization, experimental hooks.</p>
                  <div className="pt-2 border-t border-slate-100 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Projected Posts:</span>
                      <span className="font-semibold text-slate-900">{growthResult.summary.aggressive.projected_posts}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Projected Reach:</span>
                      <span className="font-bold text-slate-900">{growthResult.summary.aggressive.projected_reach.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Estimated Followers:</span>
                      <span className="font-semibold text-slate-900">+{growthResult.summary.aggressive.projected_followers.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Weekly Cadence:</span>
                      <span className="font-semibold text-slate-900">{growthResult.summary.aggressive.cadence_posts_per_week} / week</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Strategic Takeaways Box */}
              {growthResult.strategic_takeaways?.length > 0 && (
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <Zap className="w-4 h-4 text-indigo-600" />
                    Strategic Simulation Insights
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {growthResult.strategic_takeaways.map((takeaway, idx) => (
                      <div key={idx} className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs text-slate-700 flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{takeaway}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Trajectory Milestone Preview Table */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-indigo-600" />
                    Trajectory Milestone Projections
                  </h4>
                  <span className="text-[11px] text-slate-400">
                    Confidence interval: 10th – 90th percentile
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                        <th className="py-2.5 px-3">Timeline</th>
                        <th className="py-2.5 px-3">Baseline Reach</th>
                        <th className="py-2.5 px-3">Recommended Reach</th>
                        <th className="py-2.5 px-3">80% Confidence Band (Lower - Upper)</th>
                        <th className="py-2.5 px-3">Est. Follower Delta</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-medium">
                      {growthResult.timeline
                        .filter((_, idx) => (idx + 1) % (horizonDays <= 30 ? 5 : 10) === 0 || idx === horizonDays - 1)
                        .map((pt) => (
                          <tr key={pt.day} className="hover:bg-slate-50/80 transition-colors">
                            <td className="py-2.5 px-3 text-slate-900 font-bold">
                              Day {pt.day} <span className="text-slate-400 text-[11px] font-normal">({pt.date})</span>
                            </td>
                            <td className="py-2.5 px-3 text-slate-600">{pt.baseline_reach.toLocaleString()}</td>
                            <td className="py-2.5 px-3 font-bold text-indigo-600">{pt.recommended_reach.toLocaleString()}</td>
                            <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">
                              [{pt.recommended_lower.toLocaleString()} – {pt.recommended_upper.toLocaleString()}]
                            </td>
                            <td className="py-2.5 px-3 text-emerald-600 font-bold">
                              +{pt.recommended_followers.toLocaleString()}
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
              <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-700">Simulating growth trajectories...</p>
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 2: WHAT-IF POST REACH SIMULATOR                           */}
      {/* ============================================================== */}
      {activeTab === 'post' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Post Simulator Form */}
          <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="border-b border-slate-100 pb-3">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-600" />
                Single-Post What-If Parameters
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Test variations in hook, format, and caption to model probabilistic reach outcomes.
              </p>
            </div>

            <form onSubmit={handleRunPostSimulation} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Hook Text</label>
                <input
                  type="text"
                  value={postHook}
                  onChange={(e) => setPostHook(e.target.value)}
                  className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Format Type</label>
                <select
                  value={postFormat}
                  onChange={(e) => setPostFormat(e.target.value)}
                  className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                >
                  <option value="REEL">Reel (High algorithm distribution)</option>
                  <option value="CAROUSEL">Carousel (High repeat saves)</option>
                  <option value="IMAGE">Single Image</option>
                  <option value="VIDEO">In-feed Video</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Caption & CTA</label>
                <textarea
                  rows={4}
                  value={postCaption}
                  onChange={(e) => setPostCaption(e.target.value)}
                  className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Monte Carlo Stochastic Draws: <span className="font-bold text-indigo-600">{postDraws}</span>
                </label>
                <input
                  type="range"
                  min="100"
                  max="1000"
                  step="100"
                  value={postDraws}
                  onChange={(e) => setPostDraws(Number(e.target.value))}
                  className="w-full"
                />
              </div>

              <button
                type="submit"
                disabled={isSimulatingPost}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold text-sm rounded-lg shadow-sm flex items-center justify-center gap-2 transition-colors"
              >
                {isSimulatingPost ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Simulating {postDraws} Draws...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 text-amber-300" />
                    Simulate Post Distribution
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Post Simulator Results */}
          <div className="lg:col-span-7 space-y-6">
            {postResult ? (
              <>
                {/* Hero Card */}
                <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-6">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Expected Median Reach</span>
                    <h3 className="text-3xl font-black text-slate-900 mt-0.5">
                      {postResult.simulation_stats.percentiles.p50_expected_median.toLocaleString()}
                    </h3>
                    <p className="text-xs text-slate-500 mt-1">
                      Historical account baseline: {postResult.simulation_stats.historical_median_reach.toLocaleString()}
                    </p>
                  </div>

                  {/* Breakout Chance Box */}
                  <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800">Breakout Probability</span>
                    <div className="text-2xl font-black text-emerald-700 mt-0.5">
                      {postResult.simulation_stats.prob_breakout_pct}%
                    </div>
                    <span className="text-[10px] text-emerald-600 font-semibold">
                      Odds of beating top 10% post
                    </span>
                  </div>
                </div>

                {/* Percentiles Table */}
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-indigo-600" />
                    Probabilistic Reach Percentiles
                  </h4>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-center">
                      <div className="text-[10px] font-bold text-slate-400 uppercase">p10 (Conservative)</div>
                      <div className="text-sm font-extrabold text-slate-800 mt-1">
                        {postResult.simulation_stats.percentiles.p10_conservative.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-center">
                      <div className="text-[10px] font-bold text-slate-400 uppercase">p25 (Low Estimate)</div>
                      <div className="text-sm font-extrabold text-slate-800 mt-1">
                        {postResult.simulation_stats.percentiles.p25_moderate_low.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-200 text-center">
                      <div className="text-[10px] font-bold text-indigo-600 uppercase">p50 (Expected Median)</div>
                      <div className="text-sm font-black text-indigo-900 mt-1">
                        {postResult.simulation_stats.percentiles.p50_expected_median.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-center">
                      <div className="text-[10px] font-bold text-slate-400 uppercase">p75 (Optimistic)</div>
                      <div className="text-sm font-extrabold text-slate-800 mt-1">
                        {postResult.simulation_stats.percentiles.p75_moderate_high.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-emerald-50 p-3 rounded-lg border border-emerald-200 text-center">
                      <div className="text-[10px] font-bold text-emerald-600 uppercase">p90 (Viral Upside)</div>
                      <div className="text-sm font-black text-emerald-800 mt-1">
                        {postResult.simulation_stats.percentiles.p90_viral_upside.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-violet-50 p-3 rounded-lg border border-violet-200 text-center">
                      <div className="text-[10px] font-bold text-violet-600 uppercase">p99 (Super Viral)</div>
                      <div className="text-sm font-black text-violet-800 mt-1">
                        {postResult.simulation_stats.percentiles.p99_super_viral.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Distribution Histogram Bars */}
                {postResult.distribution_bins?.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                      <Layers className="w-4 h-4 text-indigo-600" />
                      Stochastic Reach Density Distribution
                    </h4>

                    <div className="space-y-2 pt-2">
                      {postResult.distribution_bins.map((bin, idx) => (
                        <div key={idx} className="space-y-1">
                          <div className="flex justify-between text-[11px] text-slate-600">
                            <span className="font-mono">{bin.range_label} reach</span>
                            <span className="font-bold text-slate-900">{bin.percentage}%</span>
                          </div>
                          <div className="w-full bg-slate-100 rounded-full h-2">
                            <div
                              className="bg-indigo-600 h-2 rounded-full transition-all"
                              style={{ width: `${Math.min(100, bin.percentage * 3)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-white border border-slate-200 border-dashed rounded-xl p-12 text-center shadow-sm">
                <BarChart2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <h3 className="text-base font-bold text-slate-900">Run a What-If Post Reach Simulation</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                  Test your candidate hook and format on the left to run 500 Monte Carlo draws and view the predicted distribution.
                </p>
                <button
                  onClick={handleRunPostSimulation}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm"
                >
                  Simulate Sample Post
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
