import React from 'react';
import { X, BookOpen } from 'lucide-react';

export default function UserGuideModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#111827] border border-[#334155] rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
        <div className="px-6 py-4 border-b border-[#1f293d] flex items-center justify-between">
          <h3 className="font-bold text-white flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-sky-400" />
            InstaMap Engine Walkthrough & User Guide
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-4 text-xs leading-relaxed text-slate-300">
          <div className="bg-[#1e293b] p-4 rounded-xl border border-[#334155]">
            <h4 className="font-bold text-white text-sm mb-1">1. Zero-API Ingestion</h4>
            <p className="text-slate-400">
              Upload past post exports via CSV or paste rows. The Smart Schema Mapper normalizes column aliases automatically without requiring Meta API credentials.
            </p>
          </div>

          <div className="bg-[#1e293b] p-4 rounded-xl border border-[#334155]">
            <h4 className="font-bold text-white text-sm mb-1">2. Algorithmic Sweet Spot Window</h4>
            <p className="text-slate-400">
              The engine measures comment and reach velocity across hours and days of the week to pinpoint the exact 3-hour cluster where initial distribution peaks.
            </p>
          </div>

          <div className="bg-[#1e293b] p-4 rounded-xl border border-[#334155]">
            <h4 className="font-bold text-white text-sm mb-1">3. Autonomous 7-Day Planning</h4>
            <p className="text-slate-400">
              Clicking <strong>Run Autonomous Cycle</strong> invokes the LangGraph state machine to allocate formats (60% Reels, 30% Carousels), formulate core pillars, and draft full content scripts.
            </p>
          </div>

          <div className="bg-[#1e293b] p-4 rounded-xl border border-[#334155]">
            <h4 className="font-bold text-white text-sm mb-1">4. Human-in-the-Loop Review Queue</h4>
            <p className="text-slate-400">
              No draft is published automatically. You review all hook copy, body scripts, and CTAs in the <strong>Review Studio</strong>, with options to Approve, Request Edit, or Reject.
            </p>
          </div>

          <div className="bg-[#1e293b] p-4 rounded-xl border border-[#334155]">
            <h4 className="font-bold text-white text-sm mb-1">5. AI Advisory Copilot (Chatbot)</h4>
            <p className="text-slate-400">
              Chat with your copilot anytime! Ask for viral hook rewrites, posting time explanations, or performance critiques grounded directly in your PostgreSQL metrics.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
