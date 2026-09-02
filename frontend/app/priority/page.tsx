'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { DataTable, Column } from '@/components/ui/DataTable';
import { SourceReport, PriorityLevel } from '@/types';
import { AlertTriangle, ShieldAlert, RefreshCw, Sparkles } from 'lucide-react';
import Link from 'next/link';

export default function PriorityQueuePage() {
  const [reports, setReports] = useState<SourceReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [filterLevel, setFilterLevel] = useState<string>('ALL');

  const fetchPriorityQueue = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/reports?size=50');
      if (res.ok) {
        const data = await res.json();
        const items: SourceReport[] = data.items || [];
        // Sort items by priority_score descending
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

  const columns: Column<SourceReport>[] = [
    {
      header: 'Score',
      accessor: (r) => (
        <span className="p-1.5 bg-industrial-950 border border-industrial-700 rounded text-xs font-mono font-bold text-industrial-100 block text-center min-w-[45px]">
          {r.priority_score !== undefined && r.priority_score !== null ? r.priority_score : '—'}
        </span>
      ),
    },
    {
      header: 'Priority Level',
      accessor: (r) => {
        const lvl = r.priority_level;
        if (!lvl) return <span className="text-industrial-500 text-[10px] font-mono">UNCLASSIFIED</span>;

        const map: Record<string, string> = {
          CRITICAL: 'bg-red-950/90 text-red-300 border-red-700 font-bold animate-pulse',
          HIGH_PRIORITY_SIF_FPI_PRECURSOR: 'bg-orange-950/90 text-orange-300 border-orange-700 font-bold',
          SAFETY_REVIEW: 'bg-amber-950/90 text-amber-300 border-amber-700 font-semibold',
          ROUTINE: 'bg-emerald-950/90 text-emerald-300 border-emerald-800',
          UNCERTAIN: 'bg-industrial-900 text-industrial-400 border-industrial-700',
        };
        const cls = map[lvl] || map.UNCERTAIN;
        return (
          <span className={`px-2.5 py-1 rounded text-xs font-mono uppercase border ${cls}`}>
            {lvl.replace('_PRECURSOR', '')}
          </span>
        );
      },
    },
    {
      header: 'Report ID',
      accessor: (r) => (
        <Link href={`/reports/${r.report_id}`} className="font-mono font-semibold text-blue-400 hover:underline">
          {r.report_id}
        </Link>
      ),
    },
    { header: 'Site', accessor: (r) => r.site || '—' },
    { header: 'Location', accessor: (r) => r.functional_location || '—' },
    {
      header: 'SIF Potential',
      accessor: (r) => {
        const val = r.sif_fpi_potential;
        if (val === 'YES') {
          return <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-red-950 text-red-300 border border-red-800">YES</span>;
        }
        if (val === 'UNCERTAIN') {
          return <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-amber-950 text-amber-300 border border-amber-800">UNCERTAIN</span>;
        }
        return <span className="px-2 py-0.5 rounded text-[9px] font-mono text-emerald-400">NO</span>;
      },
    },
    {
      header: 'Life-Saving Rule',
      accessor: (r) => (
        <span className="font-mono text-purple-300 text-xs">
          {r.primary_life_saving_rule || '—'}
        </span>
      ),
    },
    {
      header: 'Action Needed',
      accessor: (r) => (
        <Link
          href={`/reports/${r.report_id}`}
          className="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-mono text-[10px] uppercase font-semibold transition-colors inline-block"
        >
          Inspect Triage
        </Link>
      ),
    },
  ];

  return (
    <AppShell title="HSE Priority Queue">
      <SectionCard
        title="High-Priority Precursor Risk Queue"
        subtitle="Database-derived HSE incident rankings based on SIF screening, barrier condition, and safety rule overrides."
        action={
          <div className="flex items-center gap-3">
            <button
              onClick={handleBatchCalculate}
              disabled={calculating}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-industrial-800 hover:bg-industrial-700 text-industrial-200 border border-industrial-600 font-mono text-xs font-semibold uppercase tracking-wider transition-colors disabled:opacity-50"
            >
              {calculating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5 text-blue-400" />}
              Recalculate Priority Queue
            </button>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-mono text-industrial-400">Filter Level:</span>
              <select
                value={filterLevel}
                onChange={(e) => setFilterLevel(e.target.value)}
                className="bg-industrial-950 border border-industrial-700 rounded px-2.5 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
              >
                <option value="ALL">All Priority Levels</option>
                <option value="CRITICAL">Critical Only</option>
                <option value="HIGH">High Priority SIF Only</option>
                <option value="REVIEW">Safety Review Only</option>
                <option value="ROUTINE">Routine Only</option>
                <option value="UNCERTAIN">Uncertain Only</option>
              </select>
            </div>
          </div>
        }
      >
        <div className="space-y-4">
          {loading ? (
            <div className="p-8 text-center font-mono text-xs text-industrial-400 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              Loading database HSE priority rankings...
            </div>
          ) : filteredReports.length === 0 ? (
            <EmptyState
              title="Priority Queue Empty"
              description="No reports match the selected priority filter criteria in the database."
            />
          ) : (
            <DataTable columns={columns} data={filteredReports} />
          )}
        </div>
      </SectionCard>
    </AppShell>
  );
}
