'use client';

import React from 'react';
import { Search } from 'lucide-react';

interface TopBarProps {
  title?: string;
}

export const TopBar: React.FC<TopBarProps> = ({ title = 'HSE Intelligence' }) => {
  return (
    <header className="h-14 px-6 bg-white border-b border-industrial-850 flex items-center justify-between z-20 shrink-0">
      {/* Page Title */}
      <h1 className="text-[15px] font-semibold text-industrial-100">
        {title}
      </h1>

      {/* Search */}
      <div className="hidden md:flex items-center w-72 relative">
        <Search className="w-3.5 h-3.5 text-industrial-700 absolute left-3" />
        <input
          type="text"
          placeholder="Search reports, sites, mechanisms…"
          className="w-full bg-industrial-950 border border-industrial-850 rounded-md pl-9 pr-3 py-1.5 text-[13px] text-industrial-200 placeholder:text-industrial-700 focus:outline-none focus:border-industrial-600 transition-colors"
        />
      </div>

      {/* Right: system status + user */}
      <div className="flex items-center gap-4 text-[13px]">


        {/* User */}
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-industrial-900 flex items-center justify-center text-[11px] font-medium text-industrial-400">
            HA
          </div>
          <span className="text-[13px] text-industrial-300 hidden sm:inline">HSE Analyst</span>
        </div>
      </div>
    </header>
  );
};
