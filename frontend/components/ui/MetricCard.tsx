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
  const getBorderColor = () => {
    switch (variant) {
      case 'critical':
        return 'border-red-900/60 bg-red-950/20';
      case 'warning':
        return 'border-amber-900/60 bg-amber-950/20';
      case 'success':
        return 'border-emerald-900/60 bg-emerald-950/20';
      case 'info':
        return 'border-blue-900/60 bg-blue-950/20';
      default:
        return 'border-industrial-700 bg-industrial-900';
    }
  };

  return (
    <div className={cn('p-4 rounded border transition-all', getBorderColor(), className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono tracking-wider uppercase text-industrial-300">
          {title}
        </span>
        {Icon && <Icon className="w-4 h-4 text-industrial-400" />}
      </div>
      <div className="mt-2 text-2xl font-mono font-bold tracking-tight text-industrial-100">
        {value}
      </div>
      {subtitle && (
        <div className="mt-1 text-xs text-industrial-400 font-mono">
          {subtitle}
        </div>
      )}
    </div>
  );
};
