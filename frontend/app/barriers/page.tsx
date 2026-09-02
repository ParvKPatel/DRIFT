'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { DataTable, Column } from '@/components/ui/DataTable';
import { BarrierSummary } from '@/types';
import { Shield, RefreshCw, Download, AlertTriangle, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function BarriersPage() {
  const [barriers, setBarriers] = useState<BarrierSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchBarriers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/dashboard/barriers');
      if (res.ok) {
        const data = await res.json();
        setBarriers(data);
      }
    } catch (err) {
      console.error('Failed to fetch barrier intelligence:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBarriers();
  }, [fetchBarriers]);

  const columns: Column<BarrierSummary>[] = [
    {
      header: 'Barrier',
      accessor: (b) => (
        <span className="font-mono text-xs font-bold text-industrial-100 block">
          {b.barrier}
        </span>
      ),
    },
    {
      header: 'Weakness Score',
      accessor: (b) => (
        <div className="p-1.5 bg-industrial-950 border border-industrial-700 rounded text-center min-w-[50px]">
          <span className="text-xs font-mono font-bold text-red-400 block">{b.weakness_score}</span>
        </div>
      ),
    },
    {
      header: 'Mentions',
      accessor: (b) => <span className="font-mono text-xs text-industrial-300">{b.total_mentions}</span>,
    },
    {
      header: 'Failed',
      accessor: (b) => (
        <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${b.failed_count > 0 ? 'bg-red-950 text-red-300 border border-red-800' : 'text-industrial-500'}`}>
          {b.failed_count}
        </span>
      ),
    },
    {
      header: 'Degraded',
      accessor: (b) => (
        <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${b.degraded_count > 0 ? 'bg-amber-950 text-amber-300 border border-amber-800' : 'text-industrial-500'}`}>
          {b.degraded_count}
        </span>
      ),
    },
    {
      header: 'Absent',
      accessor: (b) => (
        <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${b.absent_count > 0 ? 'bg-purple-950 text-purple-300 border border-purple-800' : 'text-industrial-500'}`}>
          {b.absent_count}
        </span>
      ),
    },
    {
      header: 'Intact',
      accessor: (b) => (
        <span className="text-xs font-mono text-emerald-400">{b.intact_count}</span>
      ),
    },
    {
      header: 'Unknown State',
      accessor: (b) => (
        <span className="text-xs font-mono text-industrial-500">{b.unknown_count}</span>
      ),
    },
    {
      header: 'SIF Precursors',
      accessor: (b) => (
        <span className="text-xs font-mono font-bold text-red-400">{b.sif_count}</span>
      ),
    },
  ];

  return (
    <AppShell title="Physical & Procedural Barrier Intelligence">
      <div className="space-y-6 max-w-6xl mx-auto">
        <SectionCard
          title="Safety Barrier Weakness & Condition Matrix"
          subtitle="Ranked by failure evidence (Failed, Absent, Degraded). Unknown states are treated strictly separately from intact or failed controls."
          action={
            <a
              href="/api/v1/dashboard/export/barriers"
              download
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-industrial-900 hover:bg-industrial-800 border border-industrial-700 text-xs font-mono text-industrial-200 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Export CSV
            </a>
          }
        >
          {loading ? (
            <div className="p-8 text-center font-mono text-xs text-industrial-400 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              Loading barrier intelligence matrix...
            </div>
          ) : barriers.length === 0 ? (
            <EmptyState
              title="No Barrier Degradation Data"
              description="Extract AI safety facts to track physical & procedural barrier condition distribution."
            />
          ) : (
            <DataTable columns={columns} data={barriers} />
          )}
        </SectionCard>
      </div>
    </AppShell>
  );
}
