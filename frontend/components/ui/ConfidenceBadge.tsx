import React from 'react';
import { cn } from '@/lib/utils';

interface ConfidenceBadgeProps {
  confidence?: number; // 0.0 to 1.0
  className?: string;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ confidence, className }) => {
  if (confidence === undefined || confidence === null) {
    return <span className="text-xs text-slate-500 font-mono">—</span>;
  }

  const pct = Math.round(confidence * 100);

  const getStyle = (val: number) => {
    if (val >= 85) return 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40';
    if (val >= 60) return 'text-amber-400 bg-amber-950/40 border-amber-800/40';
    return 'text-slate-400 bg-slate-900 border-slate-700';
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono border',
        getStyle(pct),
        className
      )}
    >
      CONFIDENCE: {pct}%
    </span>
  );
};
