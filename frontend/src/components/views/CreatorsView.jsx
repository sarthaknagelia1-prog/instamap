import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import LoadingSkeleton from '../common/LoadingSkeleton';
import EmptyState from '../common/EmptyState';
import { Users, Check, FileCheck, ShieldCheck, Database, Calendar } from 'lucide-react';

export default function CreatorsView({ currentCreatorId, onSelectCreator, onNavigate }) {
  const [creators, setCreators] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getCreators().catch(() => []),
      api.getCreatorIngestionLogs(currentCreatorId).catch(() => []),
    ]).then(([creatorsList, logsList]) => {
      if (!isMounted) return;
      setCreators(creatorsList || []);
      setLogs(logsList || []);
      setLoading(false);
    });

    return () => { isMounted = false; };
  }, [currentCreatorId]);

  if (loading) {
    return <LoadingSkeleton rows={5} height="h-20" />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">Creator Profiles</h2>
          <p className="text-xs text-slate-500 mt-1">
            Manage creator workspaces, view ingestion health, and switch active data contexts.
          </p>
        </div>
        <button
          onClick={() => onNavigate('import')}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-xs transition"
        >
          + Import New Creator Data
        </button>
      </div>

      {/* Creators Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {creators.map((c) => {
          const isSelected = c.id === currentCreatorId;
          return (
            <div
              key={c.id}
              className={`
                bg-white rounded-xl border p-5 shadow-xs transition flex flex-col justify-between
                ${isSelected ? 'border-indigo-600 ring-2 ring-indigo-500/10' : 'border-slate-200 hover:border-slate-300'}
              `}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-base font-extrabold text-slate-900">{c.id}</span>
                  {isSelected ? (
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1">
                      <Check className="w-3 h-3" /> Active
                    </span>
                  ) : (
                    <button
                      onClick={() => onSelectCreator(c.id)}
                      className="text-xs font-bold text-slate-600 hover:text-indigo-600 px-2 py-1 rounded hover:bg-slate-50 transition"
                    >
                      Select
                    </button>
                  )}
                </div>

                <div className="space-y-1.5 text-xs text-slate-600 mb-4">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Niche:</span>
                    <span className="font-semibold text-slate-800">{c.niche || 'Tech & AI'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Posts:</span>
                    <span className="font-semibold text-slate-800 font-mono">{c.total_posts || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Last Post Date:</span>
                    <span className="font-semibold text-slate-800">
                      {c.last_post_date ? new Date(c.last_post_date).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                <span>Created: {c.created_at ? new Date(c.created_at).toLocaleDateString() : 'Active'}</span>
                <span className="font-semibold text-slate-700">PostgreSQL</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Ingestion Audit Logs for current creator */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs">
        <h3 className="text-base font-bold text-slate-900 tracking-tight mb-1">
          Ingestion Audit History for {currentCreatorId}
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Every upload and paste batch is evaluated by the Data Readiness Agent before persisting to PostgreSQL.
        </p>

        {logs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase text-[11px]">
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Source</th>
                  <th className="py-2.5 px-3">Quality Score</th>
                  <th className="py-2.5 px-3">Records Ingested</th>
                  <th className="py-2.5 px-3">Duplicates Cleaned</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/70">
                    <td className="py-3 px-3 text-slate-500">
                      {log.created_at ? new Date(log.created_at).toLocaleString() : 'Recent'}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-700">{log.source}</td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            style={{ width: `${(log.quality_score || 0) * 100}%` }}
                            className={`h-full ${log.quality_score >= 0.7 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                          />
                        </div>
                        <span className="font-mono text-slate-700">{((log.quality_score || 0) * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 font-semibold text-slate-900">{log.inserted_count} posts</td>
                    <td className="py-3 px-3 text-slate-500 font-mono">{log.duplicate_records_removed}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Ready
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-xs text-slate-500 text-center py-6 bg-slate-50 rounded-xl">
            No past ingestion logs recorded for this creator.
          </div>
        )}
      </div>
    </div>
  );
}
