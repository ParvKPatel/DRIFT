import React from 'react';
import { EvidenceBadge } from './EvidenceBadge';
import { EvidenceStatus } from '@/types';
import { cn } from '@/lib/utils';

interface SafetyFactCardProps {
  label: string;
  value?: string;
  evidenceStatus?: EvidenceStatus;
  subtext?: string;
  className?: string;
}

export const SafetyFactCard: React.FC<SafetyFactCardProps> = ({
  label,
  value = 'UNKNOWN',
  evidenceStatus = 'UNKNOWN',
  subtext,
  className,
}) => {
  return (
    <div className={cn('p-3 rounded bg-industrial-900 border border-industrial-700 flex flex-col justify-between space-y-2', className)}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono uppercase tracking-wider text-industrial-400">
          {label}
        </span>
        <EvidenceBadge status={evidenceStatus} />
      </div>
      <div className="text-xs font-mono font-semibold text-industrial-100 break-words">
        {value || 'UNKNOWN'}
      </div>
      {subtext && (
        <div className="text-[11px] font-sans text-industrial-400 italic">
          {subtext}
        </div>
      )}
    </div>
  );
};
