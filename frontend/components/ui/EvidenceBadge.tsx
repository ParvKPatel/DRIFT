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
        return 'bg-black text-white border-black';
      case 'INFERRED':
        return 'bg-industrial-800 text-industrial-100 border-industrial-800';
      case 'UNKNOWN':
      default:
        return 'bg-white text-industrial-400 border-industrial-800';
    }
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-sans font-medium border tracking-wide uppercase',
        getStyle(status),
        className
      )}
    >
      EVIDENCE: {status}
    </span>
  );
};
