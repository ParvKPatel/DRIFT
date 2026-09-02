'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ShieldAlert,
  LayoutDashboard,
  FileText,
  AlertTriangle,
  GitMerge,
  Shield,
  MapPin,
  UserCheck,
  BarChart3,
  Upload,
  Settings,
  Activity,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { label: 'Overview', href: '/', icon: LayoutDashboard },
  { label: 'Upload Dataset', href: '/upload', icon: Upload },
  { label: 'Safety Reports', href: '/reports', icon: FileText },
  { label: 'Priority Queue', href: '/priority', icon: AlertTriangle },
  { label: 'Precursor Clusters', href: '/clusters', icon: GitMerge },
  { label: 'Barrier Intelligence', href: '/barriers', icon: Shield },
  { label: 'Sites & Activities', href: '/sites', icon: MapPin },
  { label: 'Human Review', href: '/review', icon: UserCheck },
  { label: 'Model Evaluation', href: '/evaluation', icon: BarChart3 },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);

  return (
    <aside
      className={cn(
        'bg-industrial-900 border-r border-industrial-800 flex flex-col justify-between transition-all duration-200 shrink-0 z-30',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Brand Header */}
      <div className="h-16 px-4 border-b border-industrial-800 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 overflow-hidden">
          <div className="w-8 h-8 rounded bg-industrial-100 text-industrial-950 flex items-center justify-center shrink-0">
            <ShieldAlert className="w-5 h-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-sans font-bold text-sm tracking-wider text-industrial-100 uppercase">
                OIL SENTINEL
              </span>
              <span className="text-[10px] font-sans text-industrial-500 uppercase tracking-widest">
                HSE Precursor AI
              </span>
            </div>
          )}
        </Link>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded text-industrial-400 hover:text-industrial-100 hover:bg-industrial-800 transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="p-2 space-y-1 overflow-y-auto flex-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded text-xs font-sans transition-colors',
                isActive
                  ? 'bg-industrial-850 text-industrial-100 font-semibold'
                  : 'text-industrial-400 hover:bg-industrial-850 hover:text-industrial-100'
              )}
            >
              <Icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-industrial-100' : 'text-industrial-500')} />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer Utilities */}
      <div className="p-3 border-t border-industrial-800 bg-industrial-950 space-y-2">
        <div className="flex items-center justify-between text-[11px] font-sans text-industrial-500">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-industrial-400" />
            {!collapsed && <span>SYS: ONLINE</span>}
          </div>
          {!collapsed && (
            <span className="px-1.5 py-0.5 rounded text-[10px] text-industrial-500 border border-industrial-800">
              DEMO MODE
            </span>
          )}
        </div>
        {!collapsed && (
          <div className="flex items-center justify-between text-[11px] font-sans text-industrial-500 pt-1">
            <span>v0.1.0-phase6</span>
            <Link href="#" className="hover:text-industrial-300 flex items-center gap-1">
              <Settings className="w-3 h-3" />
              Settings
            </Link>
          </div>
        )}
      </div>
    </aside>
  );
};
