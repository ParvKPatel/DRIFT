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
        return 'bg-black text-white border-black';
      case 'HIGH':
      case 'DEGRADED':
        return 'bg-industrial-500 text-white border-industrial-500';
      case 'REVIEW':
      case 'SAFETY_REVIEW':
        return 'bg-industrial-700 text-white border-industrial-700';
      case 'NO':
      case 'INTACT':
      case 'ROUTINE':
        return 'bg-industrial-900 text-industrial-400 border-industrial-900';
      case 'UNCERTAIN':
      case 'UNKNOWN':
      case 'ABSENT':
      default:
        return 'bg-white text-industrial-400 border-industrial-700';
    }
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-sans font-medium border',
        getStyle(status),
        className
      )}
    >
      {status}
    </span>
  );
};
