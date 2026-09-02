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
        return 'bg-black text-white border-black';
      case 'HIGH_PRIORITY_SIF_FPI_PRECURSOR':
        return 'bg-industrial-500 text-white border-industrial-500';
      case 'SAFETY_REVIEW':
        return 'bg-industrial-700 text-white border-industrial-700';
      case 'ROUTINE':
        return 'bg-industrial-900 text-industrial-400 border-industrial-900';
      case 'UNCERTAIN':
      default:
        return 'bg-white text-industrial-400 border-industrial-700';
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
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-sans font-semibold border',
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
