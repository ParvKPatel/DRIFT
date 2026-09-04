'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  FileText,
  AlertTriangle,
  GitMerge,
  Shield,
  MapPin,
  UserCheck,
  BarChart3,
  Upload,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { label: 'Overview', href: '/', icon: LayoutDashboard },
  { label: 'Upload Data', href: '/upload', icon: Upload },
  { label: 'Safety Reports', href: '/reports', icon: FileText },
  { label: 'Priority Queue', href: '/priority', icon: AlertTriangle },
  { label: 'Common Concerns', href: '/clusters', icon: GitMerge },
  { label: 'Controls Attention', href: '/barriers', icon: Shield },
  { label: 'Sites & Activities', href: '/sites', icon: MapPin },
  { label: 'Needs Review', href: '/review', icon: UserCheck },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);

  return (
    <aside
      className={cn(
        'bg-white border-r border-industrial-850 flex flex-col justify-between transition-all duration-200 shrink-0 z-30',
        collapsed ? 'w-16' : 'w-56'
      )}
    >
      {/* Brand */}
      <div className="h-14 px-4 border-b border-industrial-850 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 overflow-hidden">
          <div className="w-7 h-7 rounded-md bg-industrial-100 text-white flex items-center justify-center shrink-0 text-xs font-bold">
            DR
          </div>
          {!collapsed && (
            <span className="text-[13px] font-semibold tracking-wide text-industrial-200 uppercase">
              Drift
            </span>
          )}
        </Link>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded text-industrial-700 hover:text-industrial-300 transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="px-2 py-3 space-y-0.5 overflow-y-auto flex-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-2.5 px-2.5 py-2 rounded-md text-[13px] transition-colors',
                isActive
                  ? 'bg-industrial-900 text-industrial-100 font-medium'
                  : 'text-industrial-600 hover:bg-industrial-900 hover:text-industrial-300'
              )}
            >
              <Icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-industrial-300' : 'text-industrial-700')} />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Minimal footer */}
      <div className="px-3 py-2.5 border-t border-industrial-850">
        <div className="flex items-center gap-1.5 text-[11px] text-industrial-700">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          {!collapsed && <span>System Online</span>}
        </div>
      </div>
    </aside>
  );
};
