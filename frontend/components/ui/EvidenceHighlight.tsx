import React from 'react';
import { EvidenceStatus } from '@/types';
import { cn } from '@/lib/utils';

interface EvidenceHighlightProps {
  narrative: string;
  span?: string;
  status?: EvidenceStatus;
  className?: string;
}

export const EvidenceHighlight: React.FC<EvidenceHighlightProps> = ({
  narrative,
  span,
  status = 'UNKNOWN',
  className,
}) => {
  if (!span || !narrative.includes(span)) {
    return (
      <div className={cn('p-4 font-mono text-xs text-industrial-200 leading-relaxed bg-industrial-950 rounded border border-industrial-800', className)}>
        {narrative}
      </div>
    );
  }

  const parts = narrative.split(span);

  const getHighlightBg = (evStatus: EvidenceStatus) => {
    switch (evStatus) {
      case 'EXPLICIT':
        return 'bg-blue-950/80 text-blue-200 border-b-2 border-blue-500 font-semibold px-1 rounded-t';
      case 'INFERRED':
        return 'bg-purple-950/80 text-purple-200 border-b-2 border-purple-500 font-semibold px-1 rounded-t';
      case 'UNKNOWN':
      default:
        return 'bg-slate-800 text-slate-200 border-b border-slate-600 px-1';
    }
  };

  return (
    <div className={cn('p-4 font-mono text-xs text-industrial-200 leading-relaxed bg-industrial-950 rounded border border-industrial-800', className)}>
      {parts[0]}
      <mark className={getHighlightBg(status)}>
        {span}
      </mark>
      {parts[1]}
    </div>
  );
};
