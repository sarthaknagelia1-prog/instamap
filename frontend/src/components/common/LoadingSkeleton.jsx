import React from 'react';

export default function LoadingSkeleton({ rows = 4, height = 'h-10' }) {
  return (
    <div className="w-full space-y-2.5 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className={`w-full bg-slate-200/70 rounded-lg ${height}`} />
      ))}
    </div>
  );
}
