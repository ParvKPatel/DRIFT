import React from 'react';
import { cn } from '@/lib/utils';
import { PriorityLevel } from '@/types';

interface PriorityBadgeProps {
  level?: PriorityLevel | string;
  score?: number;
  className?: string;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ level = 'UNCERTAIN', score, className }) => {
  const getStyle = (val: string) => {
    switch (val) {
      case 'CRITICAL':
        return 'bg-red-950/60 text-red-300 border-red-800';
      case 'HIGH_PRIORITY_SIF_FPI_PRECURSOR':
        return 'bg-orange-950/60 text-orange-300 border-orange-800';
      case 'SAFETY_REVIEW':
        return 'bg-amber-950/60 text-amber-300 border-amber-800';
      case 'ROUTINE':
        return 'bg-emerald-950/60 text-emerald-300 border-emerald-800';
      case 'UNCERTAIN':
      default:
        return 'bg-slate-900 text-slate-400 border-slate-700';
    }
  };

  const formatLabel = (val: string) => {
    switch (val) {
      case 'HIGH_PRIORITY_SIF_FPI_PRECURSOR':
        return 'HIGH PRIORITY SIF PRECURSOR';
      default:
        return val.replace(/_/g, ' ');
    }
  };

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-semibold border',
        getStyle(level),
        className
      )}
    >
      <span>{formatLabel(level)}</span>
      {score !== undefined && (
        <span className="opacity-75 font-mono">({score.toFixed(0)})</span>
      )}
    </div>
  );
};
