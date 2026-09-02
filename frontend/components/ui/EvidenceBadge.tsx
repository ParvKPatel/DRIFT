import React from 'react';
import { cn } from '@/lib/utils';
import { EvidenceStatus } from '@/types';

interface EvidenceBadgeProps {
  status?: EvidenceStatus | string;
  className?: string;
}

export const EvidenceBadge: React.FC<EvidenceBadgeProps> = ({ status = 'UNKNOWN', className }) => {
  const getStyle = (val: string) => {
    switch (val) {
      case 'EXPLICIT':
        return 'bg-blue-950/60 text-blue-300 border-blue-800/60';
      case 'INFERRED':
        return 'bg-purple-950/60 text-purple-300 border-purple-800/60';
      case 'UNKNOWN':
      default:
        return 'bg-slate-900 text-slate-400 border-slate-700';
    }
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium border tracking-wide uppercase',
        getStyle(status),
        className
      )}
    >
      EVIDENCE: {status}
    </span>
  );
};
