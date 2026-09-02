import React from 'react';
import { cn } from '@/lib/utils';

interface StatusBadgeProps {
  status?: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status = 'UNKNOWN', className }) => {
  const getStyle = (val: string) => {
    switch (val.toUpperCase()) {
      case 'YES':
      case 'CRITICAL':
      case 'FAILED':
        return 'bg-red-500/10 text-red-400 border-red-500/30';
      case 'HIGH':
      case 'DEGRADED':
      case 'REVIEW':
      case 'SAFETY_REVIEW':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'NO':
      case 'INTACT':
      case 'ROUTINE':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'UNCERTAIN':
      case 'UNKNOWN':
      case 'ABSENT':
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium border',
        getStyle(status),
        className
      )}
    >
      {status}
    </span>
  );
};
