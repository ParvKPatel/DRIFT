import React from 'react';
import { cn } from '@/lib/utils';

interface StatusBadgeProps {
  status?: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status = 'UNKNOWN', className }) => {
  const getStyle = (val?: string | null) => {
    if (!val) return { dot: 'bg-industrial-500', text: 'text-industrial-400', bg: 'bg-industrial-800/50', border: 'border-industrial-700/50' };
    switch (val.toUpperCase()) {
      case 'YES':
      case 'CRITICAL':
      case 'FAILED':
        return { dot: 'bg-red-500', text: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' };
      case 'HIGH':
      case 'DEGRADED':
        return { dot: 'bg-amber-500', text: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' };
      case 'REVIEW':
      case 'SAFETY_REVIEW':
      case 'UNCERTAIN':
      case 'WEAK':
        return { dot: 'bg-yellow-500', text: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' };
      case 'NO':
      case 'INTACT':
      case 'EFFECTIVE':
        return { dot: 'bg-emerald-500', text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' };
      case 'ROUTINE':
      case 'UNKNOWN':
      case 'ABSENT':
      default:
        return { dot: 'bg-industrial-500', text: 'text-industrial-400', bg: 'bg-industrial-800/50', border: 'border-industrial-700/50' };
    }
  };

  const style = getStyle(status);

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium border',
        style.text,
        style.bg,
        style.border,
        className
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full', style.dot)} />
      {status}
    </span>
  );
};
