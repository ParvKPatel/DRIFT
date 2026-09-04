import React from 'react';
import { cn } from '@/lib/utils';
import { PriorityLevel } from '@/types';

interface PriorityBadgeProps {
  level?: PriorityLevel | string;
  score?: number;
  className?: string;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ level = 'UNCERTAIN', score, className }) => {
  const getStyle = (val?: string | null) => {
    switch (val) {
      case 'CRITICAL':
        return { dot: 'bg-red-500', text: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' };
      case 'HIGH_PRIORITY_SIF_FPI_PRECURSOR':
        return { dot: 'bg-amber-500', text: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' };
      case 'SAFETY_REVIEW':
        return { dot: 'bg-yellow-500', text: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' };
      case 'ROUTINE':
        return { dot: 'bg-emerald-500', text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' };
      case 'UNCERTAIN':
      default:
        return { dot: 'bg-industrial-500', text: 'text-industrial-400', bg: 'bg-industrial-800/50', border: 'border-industrial-700/50' };
    }
  };

  const formatLabel = (val?: string | null) => {
    if (!val) return 'UNCERTAIN';
    switch (val) {
      case 'HIGH_PRIORITY_SIF_FPI_PRECURSOR':
        return 'HIGH PRIORITY SIF PRECURSOR';
      case 'SAFETY_REVIEW':
        return 'REVIEW';
      default:
        return val.replace(/_/g, ' ');
    }
  };

  const style = getStyle(level);

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium border',
        style.text,
        style.bg,
        style.border,
        className
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', style.dot)} />
      <span>{formatLabel(level)}</span>
      {score !== undefined && (
        <span className="opacity-60 ml-0.5 font-mono text-[10px]">({score.toFixed(0)})</span>
      )}
    </div>
  );
};
