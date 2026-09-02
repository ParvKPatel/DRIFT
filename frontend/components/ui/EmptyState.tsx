import React from 'react';
import { LucideIcon, Inbox } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Data Available',
  description = 'No reports or precursor clusters have been processed yet.',
  icon: Icon = Inbox,
  action,
  className,
}) => {
  return (
    <div className={cn('flex flex-col items-center justify-center p-12 text-center border border-dashed border-industrial-700 rounded bg-industrial-900/50', className)}>
      <div className="w-12 h-12 rounded-full bg-industrial-800 flex items-center justify-center text-industrial-400 mb-4 border border-industrial-700">
        <Icon className="w-6 h-6" />
      </div>
      <h4 className="text-sm font-mono font-semibold text-industrial-200 uppercase tracking-wide">
        {title}
      </h4>
      <p className="text-xs text-industrial-400 max-w-sm mt-1 mb-4 font-sans">
        {description}
      </p>
      {action}
    </div>
  );
};
