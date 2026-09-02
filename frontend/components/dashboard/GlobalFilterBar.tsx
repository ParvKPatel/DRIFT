'use client';

import React from 'react';
import { Filter, Calendar, MapPin, Shield, Layers, RefreshCw, X } from 'lucide-react';

export interface FilterState {
  window: string;
  site: string;
  lsr: string;
  priority_level: string;
  sif_status: string;
  barrier_condition: string;
}

interface GlobalFilterBarProps {
  filters: FilterState;
  onFilterChange: (newFilters: FilterState) => void;
  onReset: () => void;
  loading?: boolean;
}

const OFFICIAL_LSR_OPTIONS = [
  'Bypassing Safety Controls',
  'Confined Space',
  'Driving',
  'Energy Isolation',
  'Hot Work',
  'Line of Fire',
  'Safe Mechanical Lifting',
  'Work Authorisation',
  'Working at Height',
];

export const GlobalFilterBar: React.FC<GlobalFilterBarProps> = ({
  filters,
  onFilterChange,
  onReset,
  loading = false,
}) => {
  const handleChange = (key: keyof FilterState, value: string) => {
    onFilterChange({
      ...filters,
      [key]: value,
    });
  };

  const hasActiveFilters =
    filters.window !== '30d' ||
    filters.site !== '' ||
    filters.lsr !== '' ||
    filters.priority_level !== '' ||
    filters.sif_status !== '' ||
    filters.barrier_condition !== '';

  return (
    <div className="p-3.5 bg-industrial-950/80 border border-industrial-800 rounded space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-industrial-200">
          <Filter className="w-3.5 h-3.5 text-blue-400" />
          <span>HSE INTELLIGENCE FILTERS</span>
          {loading && <RefreshCw className="w-3 h-3 text-blue-400 animate-spin ml-2" />}
        </div>

        {hasActiveFilters && (
          <button
            onClick={onReset}
            className="inline-flex items-center gap-1 text-[11px] font-mono text-industrial-400 hover:text-red-400 transition-colors"
          >
            <X className="w-3 h-3" />
            Reset Filters
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {/* Time Window */}
        <div className="space-y-1">
          <label className="text-[9px] font-mono uppercase text-industrial-400 block flex items-center gap-1">
            <Calendar className="w-2.5 h-2.5 text-industrial-500" />
            Time Window
          </label>
          <select
            value={filters.window}
            onChange={(e) => handleChange('window', e.target.value)}
            className="w-full bg-industrial-900 border border-industrial-700 rounded px-2 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="12m">Last 12 Months</option>
          </select>
        </div>

        {/* Site Filter */}
        <div className="space-y-1">
          <label className="text-[9px] font-mono uppercase text-industrial-400 block flex items-center gap-1">
            <MapPin className="w-2.5 h-2.5 text-industrial-500" />
            Operational Site
          </label>
          <select
            value={filters.site}
            onChange={(e) => handleChange('site', e.target.value)}
            className="w-full bg-industrial-900 border border-industrial-700 rounded px-2 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Sites</option>
            <option value="Offshore Platform Alpha">Offshore Platform Alpha</option>
            <option value="Refinery Complex Beta">Refinery Complex Beta</option>
            <option value="Gas Processing Terminal Delta">Gas Processing Terminal Delta</option>
          </select>
        </div>

        {/* SIF Status Filter */}
        <div className="space-y-1">
          <label className="text-[9px] font-mono uppercase text-industrial-400 block">
            SIF / FPI Status
          </label>
          <select
            value={filters.sif_status}
            onChange={(e) => handleChange('sif_status', e.target.value)}
            className="w-full bg-industrial-900 border border-industrial-700 rounded px-2 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Decisions</option>
            <option value="YES">SIF Precursor (YES)</option>
            <option value="UNCERTAIN">Uncertain Review</option>
            <option value="NO">Non-SIF (NO)</option>
          </select>
        </div>

        {/* Life-Saving Rule */}
        <div className="space-y-1">
          <label className="text-[9px] font-mono uppercase text-industrial-400 block flex items-center gap-1">
            <Shield className="w-2.5 h-2.5 text-industrial-500" />
            Life-Saving Rule
          </label>
          <select
            value={filters.lsr}
            onChange={(e) => handleChange('lsr', e.target.value)}
            className="w-full bg-industrial-900 border border-industrial-700 rounded px-2 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All 9 Rules</option>
            {OFFICIAL_LSR_OPTIONS.map((rule) => (
              <option key={rule} value={rule}>
                {rule}
              </option>
            ))}
          </select>
        </div>

        {/* HSE Priority Level */}
        <div className="space-y-1">
          <label className="text-[9px] font-mono uppercase text-industrial-400 block">
            Priority Level
          </label>
          <select
            value={filters.priority_level}
            onChange={(e) => handleChange('priority_level', e.target.value)}
            className="w-full bg-industrial-900 border border-industrial-700 rounded px-2 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Priorities</option>
            <option value="CRITICAL">Critical Override</option>
            <option value="HIGH_PRIORITY_SIF_FPI_PRECURSOR">High Priority</option>
            <option value="SAFETY_REVIEW">Safety Review</option>
            <option value="ROUTINE">Routine</option>
            <option value="UNCERTAIN">Uncertain</option>
          </select>
        </div>

        {/* Barrier Condition */}
        <div className="space-y-1">
          <label className="text-[9px] font-mono uppercase text-industrial-400 block">
            Barrier State
          </label>
          <select
            value={filters.barrier_condition}
            onChange={(e) => handleChange('barrier_condition', e.target.value)}
            className="w-full bg-industrial-900 border border-industrial-700 rounded px-2 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Barrier States</option>
            <option value="FAILED">Failed</option>
            <option value="DEGRADED">Degraded</option>
            <option value="ABSENT">Absent</option>
            <option value="INTACT">Intact</option>
            <option value="UNKNOWN">Unknown</option>
          </select>
        </div>
      </div>
    </div>
  );
};
