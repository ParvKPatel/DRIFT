import React from 'react';
import { cn } from '@/lib/utils';

interface SectionCardProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const SectionCard: React.FC<SectionCardProps> = ({
  title,
  subtitle,
  action,
  children,
  className,
}) => {
  return (
    <div className={cn('bg-transparent border border-industrial-800 rounded-sm overflow-hidden', className)}>
      <div className="px-5 py-3 border-b border-industrial-800 flex items-center justify-between bg-industrial-900">
        <div>
          <h3 className="text-sm font-sans font-bold uppercase tracking-wider text-industrial-100">
            {title}
          </h3>
          {subtitle && (
            <p className="text-xs text-industrial-500 font-sans mt-0.5">
              {subtitle}
            </p>
          )}
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
};
