import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle2 } from 'lucide-react';
import { api } from '../api/client';

export default function IngestionOnboard({ selectedCreator, onComplete }) {
  const [creatorId, setCreatorId] = useState(selectedCreator || 'creator_sarthak');
  const [niche, setNiche] = useState('Tech & AI');
  const [rawData, setRawData] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  const loadSample = () => {
    const sample = [
      { post_id: 'p401', content_type: 'reel', likes_count: 550, comments_count: 40, shares_count: 120, saves_count: 140, reach: 5800, impressions: 7200, timestamp: '2026-10-18T18:30:00Z' },
      { post_id: 'p402', content_type: 'carousel', likes_count: 360, comments_count: 26, shares_count: 60, saves_count: 95, reach: 3500, impressions: 4600, timestamp: '2026-10-19T19:00:00Z' },
      { post_id: 'p403', content_type: 'reel', likes_count: 820, comments_count: 68, shares_count: 195, saves_count: 240, reach: 8200, impressions: 11000, timestamp: '2026-10-20T20:15:00Z' },
    ];
    setRawData(JSON.stringify(sample, null, 2));
  };

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      setRawData(evt.target.result);
      setMsg(`Loaded file: ${file.name}`);
    };
    reader.readAsText(file);
  };

  const handleSubmit = async () => {
    if (!rawData.trim()) return alert('Please provide data.');
    setIsLoading(true);
    setMsg(null);

    let parsed;
    try {
      parsed = JSON.parse(rawData);
    } catch {
      const lines = rawData.split('\n').filter((l) => l.trim().length > 0);
      const headers = lines[0].split(',').map((h) => h.trim().replace(/^["']|["']$/g, ''));
      parsed = [];
      for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(',').map((c) => c.trim().replace(/^["']|["']$/g, ''));
        const row = {};
        headers.forEach((h, idx) => { row[h] = cols[idx] !== undefined ? cols[idx] : null; });
        parsed.push(row);
      }
    }

    try {
      const res = await api.submitOnboarding(creatorId, niche, parsed);
      setMsg(`Onboarding complete! ${res.posts_ingested} posts ingested.`);
      if (onComplete) onComplete(creatorId);
    } catch (err) {
      alert('Onboarding failed: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-[#111827] border border-[#1f293d] rounded-xl p-6">
      <div className="mb-6">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-sky-400" />
          Zero-API Data Ingestion & Onboarding
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Upload a CSV file or paste spreadsheet metrics to automatically normalize columns, generate strategic allocations, and build your content blueprint.
        </p>
      </div>

      {msg && (
        <div className="mb-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs px-4 py-2.5 rounded-lg flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{msg}</span>
        </div>
      )}

      <div className="space-y-4">
        <div className="flex gap-4 items-center flex-wrap">
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Creator ID:</label>
            <input
              type="text"
              value={creatorId}
              onChange={(e) => setCreatorId(e.target.value)}
              className="bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-1.5 text-xs text-white outline-none w-48"
            />
          </div>

          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Niche:</label>
            <select
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              className="bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-1.5 text-xs text-white outline-none cursor-pointer"
            >
              <option value="Tech & AI">Tech & AI</option>
              <option value="Fitness & Wellness">Fitness & Wellness</option>
              <option value="Personal Finance">Personal Finance</option>
              <option value="Creator Economy">Creator Economy</option>
            </select>
          </div>

          <div className="mt-5 flex gap-2">
            <button
              onClick={loadSample}
              className="bg-[#1e293b] hover:bg-[#334155] text-slate-200 border border-[#334155] text-xs font-semibold px-3 py-1.5 rounded-lg transition"
            >
              📋 Load Sample Data
            </button>
            <label className="bg-[#1e293b] hover:bg-[#334155] text-slate-200 border border-[#334155] text-xs font-semibold px-3 py-1.5 rounded-lg transition cursor-pointer">
              📁 Upload CSV
              <input type="file" accept=".csv,.tsv,.json" onChange={handleFile} className="hidden" />
            </label>
          </div>
        </div>

        <textarea
          value={rawData}
          onChange={(e) => setRawData(e.target.value)}
          placeholder="Paste raw array of JSON post records or CSV rows here..."
          className="w-full h-44 bg-[#090d16] border border-[#334155] rounded-lg p-3 text-xs text-slate-200 font-mono outline-none focus:border-sky-400 resize-y"
        />

        <div className="flex justify-between items-center flex-wrap gap-4 pt-2">
          <span className="text-xs text-slate-400">
            Smart schema mapper automatically resolves 40+ column variants (Likes, Reach, Views, etc.).
          </span>
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white font-semibold text-xs px-5 py-2.5 rounded-lg shadow-md transition disabled:opacity-50"
          >
            {isLoading ? 'Ingesting & Planning...' : '🚀 Ingest & Complete Onboarding'}
          </button>
        </div>
      </div>
    </div>
  );
}
