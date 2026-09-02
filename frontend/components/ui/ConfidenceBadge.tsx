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
    if (val >= 85) return 'text-black bg-industrial-900 border-industrial-800';
    if (val >= 60) return 'text-industrial-500 bg-industrial-900 border-industrial-800';
    return 'text-industrial-400 bg-white border-industrial-800';
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-sans border',
        getStyle(pct),
        className
      )}
    >
      CONFIDENCE: {pct}%
    </span>
  );
};
