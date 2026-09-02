import React from 'react';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value?: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  variant?: 'default' | 'critical' | 'warning' | 'success' | 'info';
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value = '—',
  subtitle,
  icon: Icon,
  className,
}) => {
  return (
    <div className={cn('p-4 flex flex-col', className)}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] font-sans font-bold tracking-wider uppercase text-industrial-500">
          {title}
        </span>
        {Icon && <Icon className="w-4 h-4 text-industrial-400" />}
      </div>
      <div className="text-3xl font-sans font-bold tracking-tight text-industrial-100">
        {value}
      </div>
      {subtitle && (
        <div className="mt-1 text-xs text-industrial-500 font-sans">
          {subtitle}
        </div>
      )}
    </div>
  );
};
