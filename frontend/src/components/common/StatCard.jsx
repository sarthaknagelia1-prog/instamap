import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trendDelta = null,
  trendLabel = 'vs last period',
  accentColor = 'indigo'
}) {
  const isPositive = trendDelta !== null && trendDelta > 0;
  const isNegative = trendDelta !== null && trendDelta < 0;

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs hover:border-slate-300 transition">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className="w-8 h-8 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-600">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="text-2xl font-black text-slate-900 tracking-tight mb-1">
        {value}
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-500">
        {trendDelta !== null && (
          <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded font-bold text-[11px] ${
            isPositive ? 'bg-emerald-50 text-emerald-700' : isNegative ? 'bg-rose-50 text-rose-700' : 'bg-slate-100 text-slate-600'
          }`}>
            {isPositive && <TrendingUp className="w-3 h-3" />}
            {isNegative && <TrendingDown className="w-3 h-3" />}
            {!isPositive && !isNegative && <Minus className="w-3 h-3" />}
            <span>{isPositive ? '+' : ''}{Number(trendDelta).toFixed(1)}%</span>
          </span>
        )}
        <span>{subtitle || trendLabel}</span>
      </div>
    </div>
  );
}
