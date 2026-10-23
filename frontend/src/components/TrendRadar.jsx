import React, { useState } from 'react';
import { Radio, Sparkles } from 'lucide-react';
import { api } from '../api/client';

export default function TrendRadar({ onDraftFromTrend }) {
  const [niche, setNiche] = useState('Tech & AI');
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSniff = async (selectedNiche) => {
    const n = selectedNiche || niche;
    setLoading(true);
    try {
      const data = await api.sniffTrends(n, 6);
      setSignals(data.signals || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-6">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Radio className="w-5 h-5 text-pink-400" />
            Real-Time Trend Sniffer & Hook Synthesizer
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Sniffs public Reddit discussions and Google Trends surges without paid Meta APIs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={niche}
            onChange={(e) => {
              setNiche(e.target.value);
              handleSniff(e.target.value);
            }}
            className="bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-1.5 text-xs text-white outline-none cursor-pointer"
          >
            <option value="Tech & AI">Tech & AI</option>
            <option value="Fitness & Wellness">Fitness & Wellness</option>
            <option value="Personal Finance">Personal Finance</option>
            <option value="Creator Economy">Creator Economy</option>
            <option value="Travel & Adventure">Travel & Adventure</option>
            <option value="Fashion & Aesthetics">Fashion & Aesthetics</option>
            <option value="Food & Culinary">Food & Culinary</option>
            <option value="Productivity & Habits">Productivity & Habits</option>
          </select>
          <button
            onClick={() => handleSniff()}
            disabled={loading}
            className="flex items-center gap-2 bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white font-semibold text-xs px-3.5 py-2 rounded-lg transition"
          >
            <Radio className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Scanning...' : 'Sniff Live Trends'}</span>
          </button>
        </div>
      </div>

      {signals.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          <p>Select a niche and click "Sniff Live Trends" to scan emerging discussions.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {signals.map((s, idx) => (
            <div
              key={idx}
              className="bg-[#1e293b] border border-[#334155] rounded-xl p-4 flex flex-col gap-2.5 transition hover:border-pink-500/40"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-sky-500/15 text-sky-400">
                  {s.source}
                </span>
                <span className="text-xs font-bold text-pink-400">
                  Velocity: {Math.round(s.velocity_score || 0)}
                </span>
              </div>
              <div className="font-bold text-sm text-white">{s.topic}</div>
              <div className="text-xs text-slate-400 line-clamp-2">{s.context_summary}</div>
              <div className="bg-[#090d16]/70 border-l-2 border-purple-500 px-3 py-2 rounded text-xs mt-1">
                <strong className="text-sky-400 text-[11px] block">Suggested 3s Hook:</strong>
                <em className="text-slate-300">"{s.suggested_hooks ? s.suggested_hooks[0] : ''}"</em>
              </div>
              <button
                onClick={() => onDraftFromTrend(s.topic)}
                className="mt-auto flex items-center justify-center gap-1.5 bg-[#334155] hover:bg-[#475569] text-white text-xs font-semibold py-1.5 rounded-lg transition"
              >
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                <span>Convert to Draft</span>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
