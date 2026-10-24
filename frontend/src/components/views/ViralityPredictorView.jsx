import React, { useState } from 'react';
import { api } from '../../api/client';
import {
  Sparkles,
  Zap,
  TrendingUp,
  Clock,
  Bookmark,
  Radio,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  Send
} from 'lucide-react';

export default function ViralityPredictorView({ creatorId, showToast, onSendToDraft }) {
  const [hook, setHook] = useState('3 secret mistakes why most creators fail to scale on Instagram');
  const [contentType, setContentType] = useState('REEL');
  const [caption, setCaption] = useState(
    'Here are the exact 3 frameworks to double your retention:\n1. Hook in the first 2 seconds.\n2. Cut every piece of dead air.\n3. Clear saveable CTA.\n\n👉 Save this post for your next content batch!'
  );
  const [scheduledTime, setScheduledTime] = useState('');
  const [hashtags, setHashtags] = useState('#growth #contentcreator #reelsstrategy');
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);

  const wordCount = hook.trim() ? hook.trim().split(/\s+/).length : 0;

  const handlePredict = async (e) => {
    if (e) e.preventDefault();
    if (!hook.trim() && !caption.trim()) {
      showToast('Please enter a hook or caption to evaluate.', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const parsedTags = hashtags
        .split(/[,\s]+/)
        .map((t) => t.trim())
        .filter((t) => t.startsWith('#'));

      const payload = {
        creator_id: creatorId,
        hook: hook.trim(),
        caption: caption.trim(),
        content_type: contentType,
        scheduled_time: scheduledTime ? new Date(scheduledTime).toISOString() : null,
        hashtags: parsedTags,
      };

      const res = await api.predictVirality(payload);
      setPrediction(res);
      showToast('Virality prediction generated!', 'success');
    } catch (err) {
      showToast(`Prediction failed: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 85) return 'text-emerald-600 bg-emerald-50 border-emerald-200';
    if (score >= 70) return 'text-indigo-600 bg-indigo-50 border-indigo-200';
    if (score >= 50) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-rose-600 bg-rose-50 border-rose-200';
  };

  const getMeterColor = (score, max) => {
    const pct = (score / max) * 100;
    if (pct >= 80) return 'bg-emerald-500';
    if (pct >= 60) return 'bg-indigo-500';
    if (pct >= 40) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Virality ML Layer</h1>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-violet-100 text-violet-800 border border-violet-200">
              Predictive AI
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Evaluate hook retention, format affinity, algorithmic peak timing, and save/share momentum before publishing.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Form Column */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              Content Scoring Parameters
            </h2>
            <span className="text-xs text-slate-400">Workspace: {creatorId}</span>
          </div>

          <form onSubmit={handlePredict} className="space-y-4">
            {/* Hook copy */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold text-slate-700">
                  Primary Hook (First 3 Seconds / Headline)
                </label>
                <span
                  className={`text-[11px] font-bold px-1.5 py-0.5 rounded ${
                    wordCount >= 5 && wordCount <= 11
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'bg-amber-50 text-amber-700'
                  }`}
                >
                  {wordCount} words {wordCount >= 5 && wordCount <= 11 ? '(Sweet spot)' : ''}
                </span>
              </div>
              <input
                type="text"
                value={hook}
                onChange={(e) => setHook(e.target.value)}
                placeholder="e.g. 3 secret mistakes why most creators fail to scale on Instagram"
                className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Aim for 5-11 words with strong curiosity gap or specific number.
              </p>
            </div>

            {/* Format & Scheduled Time */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Format Type</label>
                <select
                  value={contentType}
                  onChange={(e) => setContentType(e.target.value)}
                  className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                >
                  <option value="REEL">Reel (Highest reach)</option>
                  <option value="CAROUSEL">Carousel (High retention)</option>
                  <option value="IMAGE">Single Image / Photo</option>
                  <option value="VIDEO">In-feed Video</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Planned Date/Time</label>
                <input
                  type="datetime-local"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  className="w-full text-xs px-2.5 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>
            </div>

            {/* Caption */}
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Body Caption & Call-To-Action
              </label>
              <textarea
                rows={5}
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                placeholder="Include structured value delivery and an explicit Save/Share prompt..."
                className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            {/* Hashtags */}
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Target Hashtags</label>
              <input
                type="text"
                value={hashtags}
                onChange={(e) => setHashtags(e.target.value)}
                placeholder="#growth #marketing #reels"
                className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold text-sm rounded-lg shadow-sm flex items-center justify-center gap-2 transition-colors"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Calculating ML Virality Potential...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 text-amber-300" />
                  Predict Virality Potential
                </>
              )}
            </button>
          </form>
        </div>

        {/* Prediction Results Column */}
        <div className="lg:col-span-7 space-y-6">
          {prediction ? (
            <>
              {/* Scorecard Hero */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-6">
                <div className="flex items-center gap-5">
                  <div className={`w-24 h-24 rounded-2xl flex flex-col items-center justify-center border-2 shadow-inner ${getScoreColor(prediction.virality_score)}`}>
                    <span className="text-3xl font-black">{prediction.virality_score}</span>
                    <span className="text-[11px] font-bold tracking-wider uppercase">Score</span>
                  </div>
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Classified Tier</span>
                    <h3 className="text-xl font-bold text-slate-900 mt-0.5">{prediction.tier}</h3>
                    <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                      Predicted Reach Multiplier:{' '}
                      <span className="font-bold text-slate-900">{prediction.predicted_reach_multiplier}x</span> average reach
                    </p>
                  </div>
                </div>

                {/* Reach Range Box */}
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-center sm:text-right w-full sm:w-auto">
                  <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Projected Reach Range</div>
                  <div className="text-base font-extrabold text-slate-900 mt-0.5">
                    {prediction.predicted_reach_range.min_reach.toLocaleString()} – {prediction.predicted_reach_range.max_reach.toLocaleString()}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Median: ~{prediction.predicted_reach_range.median_reach.toLocaleString()} reach
                  </div>
                </div>
              </div>

              {/* 5 Factor Breakdown Bars */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-2">
                  <Zap className="w-4 h-4 text-indigo-600" />
                  Factor Score Breakdown
                </h3>

                <div className="space-y-3.5">
                  {/* Hook Strength */}
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-slate-700 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-violet-500" /> Hook Strength & Triggers
                      </span>
                      <span className="text-slate-900">{prediction.category_scores.hook_strength.score} / 25</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getMeterColor(prediction.category_scores.hook_strength.score, 25)}`}
                        style={{ width: `${(prediction.category_scores.hook_strength.score / 25) * 100}%` }}
                      />
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">{prediction.category_scores.hook_strength.feedback}</p>
                  </div>

                  {/* Format Affinity */}
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-slate-700 flex items-center gap-1.5">
                        <TrendingUp className="w-3.5 h-3.5 text-blue-500" /> Format Discovery Affinity
                      </span>
                      <span className="text-slate-900">{prediction.category_scores.format_affinity.score} / 20</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getMeterColor(prediction.category_scores.format_affinity.score, 20)}`}
                        style={{ width: `${(prediction.category_scores.format_affinity.score / 20) * 100}%` }}
                      />
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">{prediction.category_scores.format_affinity.feedback}</p>
                  </div>

                  {/* Peak Window Timing */}
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-slate-700 flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-amber-500" /> Peak Window Alignment
                      </span>
                      <span className="text-slate-900">{prediction.category_scores.timing_alignment.score} / 20</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getMeterColor(prediction.category_scores.timing_alignment.score, 20)}`}
                        style={{ width: `${(prediction.category_scores.timing_alignment.score / 20) * 100}%` }}
                      />
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">{prediction.category_scores.timing_alignment.feedback}</p>
                  </div>

                  {/* Save & Share Friction */}
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-slate-700 flex items-center gap-1.5">
                        <Bookmark className="w-3.5 h-3.5 text-emerald-500" /> Save/Share Friction & CTA
                      </span>
                      <span className="text-slate-900">{prediction.category_scores.save_share_potential.score} / 20</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getMeterColor(prediction.category_scores.save_share_potential.score, 20)}`}
                        style={{ width: `${(prediction.category_scores.save_share_potential.score / 20) * 100}%` }}
                      />
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">{prediction.category_scores.save_share_potential.feedback}</p>
                  </div>

                  {/* Viral Trend Radar */}
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-slate-700 flex items-center gap-1.5">
                        <Radio className="w-3.5 h-3.5 text-rose-500" /> Trend Radar Velocity Overlap
                      </span>
                      <span className="text-slate-900">{prediction.category_scores.trend_alignment.score} / 15</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getMeterColor(prediction.category_scores.trend_alignment.score, 15)}`}
                        style={{ width: `${(prediction.category_scores.trend_alignment.score / 15) * 100}%` }}
                      />
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">{prediction.category_scores.trend_alignment.feedback}</p>
                  </div>
                </div>
              </div>

              {/* Actionable Recommendations */}
              {prediction.actionable_recommendations?.length > 0 && (
                <div className="bg-indigo-50/70 border border-indigo-100 rounded-xl p-5 shadow-sm space-y-3">
                  <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                    High-Impact Optimization Recommendations
                  </h4>
                  <ul className="space-y-2">
                    {prediction.actionable_recommendations.map((rec, idx) => (
                      <li key={idx} className="text-xs text-indigo-950 flex items-start gap-2 bg-white/80 p-2.5 rounded-lg border border-indigo-100">
                        <span className="font-bold text-indigo-600">•</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            /* Empty State */
            <div className="bg-white border border-slate-200 border-dashed rounded-xl p-12 text-center shadow-sm">
              <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Run Virality Potential Analysis</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-5">
                Input your candidate hook, format, and caption on the left to compute the 5-factor Virality Potential Score and predicted reach multipliers.
              </p>
              <button
                onClick={handlePredict}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm inline-flex items-center gap-1.5"
              >
                Analyze Sample Post
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
