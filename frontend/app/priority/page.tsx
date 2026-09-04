'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { EmptyState } from '@/components/ui/EmptyState';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SourceReport } from '@/types';
import { RefreshCw, Sparkles, AlertCircle } from 'lucide-react';
import Link from 'next/link';

export default function PriorityQueuePage() {
  const [reports, setReports] = useState<SourceReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [filterLevel, setFilterLevel] = useState<string>('ALL');

  const fetchPriorityQueue = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/reports?size=100');
      if (res.ok) {
        const data = await res.json();
        const items: SourceReport[] = data.items || [];
        items.sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0));
        setReports(items);
      }
    } catch (err) {
      console.error('Failed to fetch priority queue:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPriorityQueue();
  }, [fetchPriorityQueue]);

  const handleBatchCalculate = async () => {
    setCalculating(true);
    try {
      const res = await fetch('/api/v1/reports/calculate-priority', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force_recalculate: true }),
      });
      if (res.ok) {
        await fetchPriorityQueue();
      }
    } catch (err) {
      console.error('Failed to run batch priority calculation:', err);
    } finally {
      setCalculating(false);
    }
  };

  const filteredReports = reports.filter((r) => {
    if (filterLevel === 'ALL') return true;
    if (filterLevel === 'CRITICAL') return r.priority_level === 'CRITICAL';
    if (filterLevel === 'HIGH') return r.priority_level === 'HIGH_PRIORITY_SIF_FPI_PRECURSOR';
    if (filterLevel === 'REVIEW') return r.priority_level === 'SAFETY_REVIEW';
    if (filterLevel === 'ROUTINE') return r.priority_level === 'ROUTINE';
    if (filterLevel === 'UNCERTAIN') return r.priority_level === 'UNCERTAIN';
    return true;
  });

  const criticalCount = reports.filter((r) => r.priority_level === 'CRITICAL').length;
  const highCount = reports.filter((r) => r.priority_level === 'HIGH_PRIORITY_SIF_FPI_PRECURSOR').length;
  const reviewCount = reports.filter((r) => r.priority_level === 'SAFETY_REVIEW').length;
  const totalCount = reports.length;

  return (
    <AppShell title="Priority Queue">
      <div className="max-w-5xl mx-auto space-y-8 pb-12">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-industrial-850 pb-6">
          <div>
            <h1 className="text-2xl font-semibold text-industrial-100">Attention Required</h1>
            <p className="text-[13px] text-industrial-500 mt-1">Review cases prioritized by risk level.</p>
          </div>
          <div className="flex items-center gap-3">
          </div>
        </div>

        {/* Priority Summary Blocks */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 bg-industrial-950 border border-industrial-850 rounded">
            <div className="text-[11px] uppercase text-industrial-500 mb-1">Critical</div>
            <div className="text-3xl font-semibold text-red-500">{criticalCount}</div>
          </div>
          <div className="p-4 bg-industrial-950 border border-industrial-850 rounded">
            <div className="text-[11px] uppercase text-industrial-500 mb-1">High</div>
            <div className="text-3xl font-semibold text-amber-500">{highCount}</div>
          </div>
          <div className="p-4 bg-industrial-950 border border-industrial-850 rounded">
            <div className="text-[11px] uppercase text-industrial-500 mb-1">Review</div>
            <div className="text-3xl font-semibold text-yellow-500">{reviewCount}</div>
          </div>
          <div className="p-4 bg-industrial-950 border border-industrial-850 rounded">
            <div className="text-[11px] uppercase text-industrial-500 mb-1">Total Queue</div>
            <div className="text-3xl font-semibold text-industrial-200">{totalCount}</div>
          </div>
        </div>

        {/* Priority Table */}
        <div className="bg-industrial-950 border border-industrial-850 rounded p-5">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-[13px] font-semibold text-industrial-200">Current Queue</h2>
            <select
              value={filterLevel}
              onChange={(e) => setFilterLevel(e.target.value)}
              className="bg-industrial-900 border border-industrial-800 rounded px-2.5 py-1.5 text-[12px] font-medium text-industrial-300 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="REVIEW">Review</option>
              <option value="ROUTINE">Routine</option>
            </select>
          </div>

          {loading ? (
             <div className="py-12 text-center text-[12px] text-industrial-500 flex items-center justify-center gap-2">
               <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
               Loading queue...
             </div>
          ) : filteredReports.length === 0 ? (
            <EmptyState title="Queue Empty" description="No reports match the current filter." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-industrial-850">
                    <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-industrial-600 pr-4">Priority</th>
                    <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-industrial-600 pr-4">Score</th>
                    <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-industrial-600 pr-4">Report</th>
                    <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-industrial-600 pr-4">Site</th>
                    <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-industrial-600 text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredReports.map((r) => (
                    <tr key={r.report_id} className="border-b border-industrial-900 last:border-b-0 hover:bg-industrial-900/40 transition-colors">
                      <td className="py-3 pr-4">
                        <PriorityBadge level={r.priority_level} />
                      </td>
                      <td className="py-3 pr-4 text-[13px] font-semibold text-industrial-300">
                        {r.priority_score ?? '—'}
                      </td>
                      <td className="py-3 pr-4">
                        <Link href={`/reports/${r.report_id}`} className="text-[13px] font-medium text-industrial-200 hover:text-industrial-100 transition-colors block">
                          {r.report_id}
                        </Link>
                        <span className="text-[12px] text-industrial-500 truncate max-w-[200px] block">
                          {r.fixed_short_description || r.narrative?.slice(0, 40)}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-[13px] text-industrial-400">
                        {r.site || '—'}
                      </td>
                      <td className="py-3 text-right">
                        <Link href={`/reports/${r.report_id}`} className="text-[12px] font-medium text-blue-500 hover:text-blue-400 transition-colors">
                          Review
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
