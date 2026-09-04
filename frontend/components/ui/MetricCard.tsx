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
  variant = 'default',
  className,
}) => {
  
  const getDotStyle = (v: string) => {
    switch (v) {
      case 'critical': return 'bg-red-500';
      case 'warning': return 'bg-amber-500';
      case 'success': return 'bg-emerald-500';
      case 'info': return 'bg-blue-500';
      default: return 'bg-industrial-800';
    }
  };

  return (
    <div className={cn('py-6', className)}>
      <div className="flex items-center gap-2 mb-2">
        {variant !== 'default' && (
          <div className={cn("w-2 h-2 rounded-full", getDotStyle(variant))} />
        )}
        <span className="text-[11px] font-medium tracking-wider uppercase text-industrial-600">
          {title}
        </span>
        {Icon && <Icon className="w-4 h-4 text-industrial-700 ml-auto" />}
      </div>
      <div className="text-4xl font-semibold tracking-tight text-industrial-100">
        {value}
      </div>
      {subtitle && (
        <div className="mt-1.5 text-[12px] text-industrial-600">
          {subtitle}
        </div>
      )}
    </div>
  );
};
