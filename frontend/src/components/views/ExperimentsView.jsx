import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import LoadingSkeleton from '../common/LoadingSkeleton';
import EmptyState from '../common/EmptyState';
import { FlaskConical, Sparkles, CheckCircle2, AlertTriangle, Play, RefreshCw, Award } from 'lucide-react';

export default function ExperimentsView({ creatorId, showToast }) {
  const [loading, setLoading] = useState(true);
  const [experiments, setExperiments] = useState([]);
  const [isProposing, setIsProposing] = useState(false);
  const [evaluatingId, setEvaluatingId] = useState(null);

  const fetchExperiments = () => {
    setLoading(true);
    api.listExperiments(creatorId)
      .then((data) => setExperiments(data || []))
      .catch(() => setExperiments([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchExperiments();
  }, [creatorId]);

  const handlePropose = async () => {
    setIsProposing(true);
    try {
      const res = await api.proposeExperiment(creatorId, 'Tech & AI');
      showToast(`New hypothesis proposed: "${res.title}"`, 'success');
      setExperiments(prev => [res, ...prev]);
    } catch (err) {
      showToast(`Failed to propose experiment: ${err.message}`, 'error');
    } finally {
      setIsProposing(false);
    }
  };

  const handleEvaluate = async (expId) => {
    setEvaluatingId(expId);
    try {
      const res = await api.evaluateExperiment(expId);
      showToast(`Statistical evaluation complete! Result: ${res.evaluation_result?.decision || 'Evaluated'}`, 'success');
      setExperiments(prev => prev.map(e => e.id === expId ? res : e));
    } catch (err) {
      showToast(`Evaluation error: ${err.message}`, 'error');
    } finally {
      setEvaluatingId(null);
    }
  };

  if (loading && experiments.length === 0) {
    return <LoadingSkeleton rows={4} height="h-32" />;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
              Welch's Two-Sample t-Test Engine
            </span>
            <span className="text-xs text-slate-400">&bull;</span>
            <span className="text-xs text-slate-500 font-semibold">{experiments.length} Active Hypotheses</span>
          </div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">A/B Testing & Statistical Lab</h2>
          <p className="text-xs text-slate-500 mt-1">
            Validates content hypotheses using pure mathematical significance testing (p &lt; 0.05) without assuming equal variance.
          </p>
        </div>

        <button
          onClick={handlePropose}
          disabled={isProposing}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-xs transition flex items-center gap-1.5 shrink-0"
        >
          <Sparkles className={`w-3.5 h-3.5 ${isProposing ? 'animate-spin' : ''}`} />
          <span>{isProposing ? 'Analyzing Gaps...' : '+ Propose Hypothesis'}</span>
        </button>
      </div>

      {experiments.length === 0 ? (
        <EmptyState
          icon={FlaskConical}
          title="No Experiments Formulated Yet"
          description="Click '+ Propose Hypothesis' to let the Experiment Engine analyze performance gaps and set up a structured A/B test."
          actionLabel="Propose New Experiment"
          onAction={handlePropose}
        />
      ) : (
        <div className="space-y-4">
          {experiments.map((exp) => {
            const ev = exp.evaluation_result || {};
            const isEvaluated = Boolean(ev.decision);
            const isSig = ev.is_significant;
            const countA = (exp.variant_a?.assigned_post_ids || []).length;
            const countB = (exp.variant_b?.assigned_post_ids || []).length;
            const needsMoreData = countA < 3 || countB < 3;

            return (
              <div key={exp.id} className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-4">
                <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold capitalize ${
                        isSig ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                        exp.status === 'completed' ? 'bg-slate-100 text-slate-700' : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                      }`}>
                        {exp.status}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">Target: {exp.metric_target}</span>
                    </div>
                    <h3 className="text-base font-bold text-slate-900">{exp.title}</h3>
                  </div>

                  <button
                    onClick={() => handleEvaluate(exp.id)}
                    disabled={evaluatingId === exp.id}
                    className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-lg transition flex items-center gap-1.5 shrink-0"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${evaluatingId === exp.id ? 'animate-spin' : ''}`} />
                    <span>{evaluatingId === exp.id ? 'Evaluating...' : 'Evaluate Stats'}</span>
                  </button>
                </div>

                {/* Hypothesis Statement */}
                <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100 leading-relaxed">
                  <strong className="text-slate-900">Hypothesis: </strong>
                  {exp.hypothesis}
                </div>

                {/* Variants A vs B */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-4 rounded-xl border border-slate-200 bg-white">
                    <span className="font-extrabold text-slate-800 block mb-1">Variant A (Control)</span>
                    <p className="text-slate-500 text-[11px] mb-2">{exp.variant_a?.description || 'Standard hook structure'}</p>
                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100 font-mono">
                      <span>Assigned: {countA} posts</span>
                      <span>Mean ER: {ev.variant_a_mean ? `${(ev.variant_a_mean).toFixed(2)}%` : '--'}</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-200 bg-white">
                    <span className="font-extrabold text-indigo-900 block mb-1">Variant B (Treatment)</span>
                    <p className="text-slate-500 text-[11px] mb-2">{exp.variant_b?.description || 'Curiosity-gap hook structure'}</p>
                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100 font-mono">
                      <span>Assigned: {countB} posts</span>
                      <span>Mean ER: {ev.variant_b_mean ? `${(ev.variant_b_mean).toFixed(2)}%` : '--'}</span>
                    </div>
                  </div>
                </div>

                {/* Evaluation Results Banner */}
                {isEvaluated && (
                  <div className={`p-4 rounded-xl border flex items-start gap-3 ${
                    isSig ? 'bg-emerald-50 border-emerald-200 text-emerald-950' : 'bg-slate-50 border-slate-200 text-slate-800'
                  }`}>
                    {isSig ? <Award className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" /> : <AlertTriangle className="w-5 h-5 text-slate-500 shrink-0 mt-0.5" />}
                    <div className="text-xs">
                      <div className="font-bold mb-0.5">
                        {isSig ? `✓ Statistically Significant Win for ${ev.winner}!` : 'Inconclusive / Insufficient Variance'}
                      </div>
                      <div className="leading-relaxed text-[11px]">
                        p-value: <code className="font-mono font-bold">{ev.p_value?.toFixed(4) || '--'}</code> &bull; t-stat: <code className="font-mono font-bold">{ev.t_statistic?.toFixed(2) || '--'}</code> &bull; {ev.recommendation || 'Gather more post samples to reach 95% statistical confidence.'}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
