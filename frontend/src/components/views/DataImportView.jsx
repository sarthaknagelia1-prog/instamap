import React, { useState } from 'react';
import { api } from '../../api/client';
import {
  UploadCloud,
  FileText,
  Clipboard,
  CheckCircle2,
  AlertTriangle,
  Download,
  ArrowRight,
  RefreshCw
} from 'lucide-react';

export default function DataImportView({ creatorId, onImportSuccess, showToast }) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'paste'
  const [selectedFile, setSelectedFile] = useState(null);
  const [pastedText, setPastedText] = useState('');
  const [targetCreatorId, setTargetCreatorId] = useState(creatorId || 'creator_sarthak');
  const [isValidating, setIsValidating] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [readinessReport, setReadinessReport] = useState(null);
  const [parsedPreview, setParsedPreview] = useState([]);
  const [importResult, setImportResult] = useState(null);

  // Download standard CSV template
  const handleDownloadTemplate = () => {
    window.open(api.getCsvTemplateUrl(), '_blank');
  };

  // Step 2: Validate Data Readiness without persisting
  const handleCheckReadiness = async () => {
    if (activeTab === 'upload' && !selectedFile) {
      showToast('Please select a CSV, TSV, or JSON file first.', 'error');
      return;
    }
    if (activeTab === 'paste' && !pastedText.trim()) {
      showToast('Please paste your spreadsheet or markdown table text.', 'error');
      return;
    }

    setIsValidating(true);
    setReadinessReport(null);
    setImportResult(null);

    try {
      let report;
      if (activeTab === 'upload') {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('creator_id', targetCreatorId);
        formData.append('source', 'file_upload');
        report = await api.checkDataReadiness(formData, true);
      } else {
        // Parse sample rows from paste text
        const rows = pastedText.trim().split('\n').map(r => r.split(/[\t,]/));
        const headers = rows[0] || [];
        const rawList = rows.slice(1).map(cols => {
          const item = {};
          headers.forEach((h, idx) => { item[h.trim()] = cols[idx]?.trim() || ''; });
          return item;
        });

        report = await api.checkDataReadiness({
          creator_id: targetCreatorId,
          source: 'paste_text',
          raw_data: rawList,
          quality_threshold: 0.5,
        });
      }

      setReadinessReport(report);
      setParsedPreview(report.processed_data?.slice(0, 5) || []);
      showToast('Data readiness check completed!', 'success');
    } catch (err) {
      showToast(`Validation failed: ${err.message}`, 'error');
    } finally {
      setIsValidating(false);
    }
  };

  // Step 3: Explicit confirmation to ingest into PostgreSQL
  const handleConfirmIngest = async () => {
    setIsIngesting(true);

    try {
      let result;
      if (activeTab === 'upload') {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('creator_id', targetCreatorId);
        formData.append('source', 'file_upload');
        result = await api.ingestData(formData, true);
      } else {
        result = await api.ingestPaste({
          creator_id: targetCreatorId,
          text_data: pastedText,
          source: 'bulk_paste',
          quality_threshold: 0.5,
        });
      }

      setImportResult(result);
      showToast(`Ingestion complete! ${result.inserted_count} posts saved to PostgreSQL.`, 'success');
      if (onImportSuccess) onImportSuccess(targetCreatorId);
    } catch (err) {
      showToast(`Ingestion error: ${err.message}`, 'error');
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">Data Import & Readiness Studio</h2>
          <p className="text-xs text-slate-500 mt-1">
            Zero-API ingestion pipeline. Import CSV exports from Meta Business Suite, Metricool, Later, or paste directly.
          </p>
        </div>
        <button
          onClick={handleDownloadTemplate}
          className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg transition flex items-center gap-1.5"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download CSV Template</span>
        </button>
      </div>

      {/* Target Creator ID Selector */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs">
        <label className="block text-xs font-bold text-slate-700 mb-1.5">
          Target Creator ID (Destination Workspace)
        </label>
        <input
          type="text"
          value={targetCreatorId}
          onChange={(e) => setTargetCreatorId(e.target.value)}
          placeholder="e.g. creator_sarthak"
          className="w-full max-w-sm text-xs bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
        />
      </div>

      {/* STEP 1: Source Selection (File or Paste) */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs">
        <div className="flex items-center gap-2 border-b border-slate-200 pb-3 mb-4">
          <span className="w-6 h-6 rounded-full bg-indigo-600 text-white font-black text-xs flex items-center justify-center">1</span>
          <h3 className="text-sm font-bold text-slate-900">Select Input Source</h3>
          <div className="ml-auto flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
            <button
              onClick={() => { setActiveTab('upload'); setReadinessReport(null); }}
              className={`px-3 py-1 text-xs font-bold rounded-md transition ${activeTab === 'upload' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600'}`}
            >
              Upload File (CSV / TSV / JSON)
            </button>
            <button
              onClick={() => { setActiveTab('paste'); setReadinessReport(null); }}
              className={`px-3 py-1 text-xs font-bold rounded-md transition ${activeTab === 'paste' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600'}`}
            >
              Paste Tabular Data
            </button>
          </div>
        </div>

        {activeTab === 'upload' ? (
          <div>
            <div className="border-2 border-dashed border-slate-300 hover:border-indigo-400 rounded-2xl p-8 text-center cursor-pointer transition bg-slate-50/50">
              <input
                type="file"
                id="file-upload"
                accept=".csv,.tsv,.json,.txt"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="hidden"
              />
              <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                <UploadCloud className="w-10 h-10 text-indigo-600 mb-2" />
                <span className="text-sm font-bold text-slate-900 mb-1">
                  {selectedFile ? selectedFile.name : 'Click to select CSV, TSV, or JSON export file'}
                </span>
                <span className="text-xs text-slate-500">
                  {selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : 'Supports Meta Suite, Metricool, Later, Hootsuite & Sprout Social exports'}
                </span>
              </label>
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Paste spreadsheet rows (Tab-separated from Google Sheets / Excel, or Markdown table)
            </label>
            <textarea
              rows={6}
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              placeholder="post_id\tdate\ttype\tlikes\tcomments\treach\npost_001\t2026-10-01T18:00:00Z\treel\t250\t35\t4200"
              className="w-full text-xs font-mono bg-slate-50 border border-slate-300 rounded-xl p-3 outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <button
            onClick={handleCheckReadiness}
            disabled={isValidating}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-xs transition flex items-center gap-1.5"
          >
            {isValidating && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
            <span>{isValidating ? 'Evaluating Readiness...' : 'Step 2: Check Data Readiness'}</span>
          </button>
        </div>
      </div>

      {/* STEP 2: Data Readiness Report */}
      {readinessReport && (
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs animate-in fade-in duration-150">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-3 mb-4">
            <span className="w-6 h-6 rounded-full bg-indigo-600 text-white font-black text-xs flex items-center justify-center">2</span>
            <h3 className="text-sm font-bold text-slate-900">Data Readiness Quality Report</h3>
            <span className={`ml-auto px-2.5 py-0.5 rounded-full text-xs font-bold ${
              readinessReport.data_ready ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
            }`}>
              {readinessReport.data_ready ? '✓ Data Ready for Ingestion' : 'Quality Below Threshold'}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-5">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Quality Score</span>
              <div className="text-xl font-black text-slate-900 font-mono mt-0.5">
                {((readinessReport.quality_score || 0) * 100).toFixed(0)}%
              </div>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Valid Records</span>
              <div className="text-xl font-black text-slate-900 font-mono mt-0.5">
                {readinessReport.record_count}
              </div>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Duplicates Cleaned</span>
              <div className="text-xl font-black text-slate-900 font-mono mt-0.5">
                {readinessReport.duplicate_records_removed}
              </div>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Invalid Dates</span>
              <div className="text-xl font-black text-slate-900 font-mono mt-0.5">
                {readinessReport.invalid_timestamps}
              </div>
            </div>
          </div>

          {/* Sample Rows Preview Table */}
          {parsedPreview.length > 0 && (
            <div className="mb-5">
              <span className="text-xs font-bold text-slate-700 block mb-2">Sample Preview (First 5 Rows Normalized)</span>
              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-xs text-left border-collapse">
                  <thead className="bg-slate-50 text-slate-500 font-semibold uppercase text-[10px]">
                    <tr>
                      <th className="py-2 px-3">Post ID</th>
                      <th className="py-2 px-3">Type</th>
                      <th className="py-2 px-3">Timestamp</th>
                      <th className="py-2 px-3">Likes</th>
                      <th className="py-2 px-3">Comments</th>
                      <th className="py-2 px-3">Reach</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {parsedPreview.map((r, i) => (
                      <tr key={i} className="hover:bg-slate-50/50">
                        <td className="py-2 px-3 text-indigo-700 font-bold">{r.post_id || `row_${i}`}</td>
                        <td className="py-2 px-3 capitalize">{r.content_type || 'reel'}</td>
                        <td className="py-2 px-3 text-slate-500">{r.timestamp || 'N/A'}</td>
                        <td className="py-2 px-3">{r.likes_count || 0}</td>
                        <td className="py-2 px-3">{r.comments_count || 0}</td>
                        <td className="py-2 px-3">{r.reach || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Explicit Confirmation Step */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Requires explicit confirmation before writing to PostgreSQL database.
            </span>
            <button
              onClick={handleConfirmIngest}
              disabled={isIngesting || !readinessReport.data_ready}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-xs transition flex items-center gap-1.5"
            >
              {isIngesting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
              <span>{isIngesting ? 'Writing to PostgreSQL...' : 'Step 3: Confirm & Ingest Posts'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Final Confirmed Ingestion Result */}
      {importResult && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6 flex items-start gap-4 animate-in fade-in">
          <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-bold text-emerald-950 mb-1">
              Ingestion Successfully Confirmed & Persisted
            </h4>
            <p className="text-xs text-emerald-800 leading-relaxed mb-3">
              {importResult.inserted_count} new posts have been written to <code className="font-mono font-bold">instaDB.posts</code> for creator <span className="font-bold">{targetCreatorId}</span>. Analytical caches have been refreshed.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
