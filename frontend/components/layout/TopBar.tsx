'use client';

import React from 'react';
import { Search, User, Database, ShieldCheck } from 'lucide-react';

interface TopBarProps {
  title?: string;
}

export const TopBar: React.FC<TopBarProps> = ({ title = 'Overview Dashboard' }) => {
  return (
    <header className="h-16 px-6 bg-industrial-900 border-b border-industrial-700 flex items-center justify-between z-20 shrink-0">
      {/* Current Page Title */}
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-mono font-bold tracking-wider text-industrial-100 uppercase">
          {title}
        </h1>
      </div>

      {/* Center Search Bar Placeholder */}
      <div className="hidden md:flex items-center w-80 relative">
        <Search className="w-4 h-4 text-industrial-400 absolute left-3" />
        <input
          type="text"
          placeholder="Search mechanism, site, LSR..."
          className="w-full bg-industrial-950 border border-industrial-700 rounded pl-9 pr-3 py-1.5 text-xs font-mono text-industrial-200 placeholder:text-industrial-500 focus:outline-none focus:border-blue-500 transition-colors"
        />
      </div>

      {/* Right User & Environment Indicators */}
      <div className="flex items-center gap-4 text-xs font-mono">
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-industrial-800 border border-industrial-700 text-industrial-300">
          <Database className="w-3.5 h-3.5 text-blue-400" />
          <span>PostgreSQL / pgvector</span>
        </div>

        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-industrial-800 border border-industrial-700 text-industrial-200">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>HSE Analyst</span>
          <User className="w-3.5 h-3.5 text-industrial-400" />
        </div>
      </div>
    </header>
  );
};
