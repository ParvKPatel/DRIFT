'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { DataTable, Column } from '@/components/ui/DataTable';
import { SiteSummary } from '@/types';
import { MapPin, RefreshCw, Download, Layers, ShieldAlert, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function SitesPage() {
  const [sites, setSites] = useState<SiteSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<string>('sif');

  const fetchSites = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/dashboard/sites');
      if (res.ok) {
        const data = await res.json();
        setSites(data);
      }
    } catch (err) {
      console.error('Failed to fetch site intelligence:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSites();
  }, [fetchSites]);

  const sortedSites = [...sites].sort((a, b) => {
    if (sortBy === 'sif') return b.sif_count - a.sif_count;
    if (sortBy === 'critical') return (b.critical_count + b.high_priority_count) - (a.critical_count + a.high_priority_count);
    if (sortBy === 'escalation') return b.escalating_cluster_count - a.escalating_cluster_count;
    if (sortBy === 'density') return (b.precursor_density || 0) - (a.precursor_density || 0);
    return b.report_count - a.report_count;
  });

  const columns: Column<SiteSummary>[] = [
    {
      header: 'Operational Site',
      accessor: (s) => (
        <div className="space-y-0.5">
          <span className="font-mono text-xs font-bold text-blue-400 block">{s.site}</span>
          <span className="text-[10px] font-mono text-industrial-500">
            {s.cluster_count} Precursor Clusters
          </span>
        </div>
      ),
    },
    {
      header: 'Reports',
      accessor: (s) => <span className="font-mono text-xs text-industrial-200">{s.report_count}</span>,
    },
    {
      header: 'SIF Precursors',
      accessor: (s) => (
        <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-red-950/80 text-red-300 border border-red-800">
          {s.sif_count}
        </span>
      ),
    },
    {
      header: 'High / Critical',
      accessor: (s) => (
        <span className="font-mono text-xs text-orange-300 font-semibold">
          {s.high_priority_count + s.critical_count}
        </span>
      ),
    },
    {
      header: 'Escalating Clusters',
      accessor: (s) => (
        <span className="font-mono text-xs text-purple-300">
          {s.escalating_cluster_count > 0 ? `${s.escalating_cluster_count} active` : '—'}
        </span>
      ),
    },
    {
      header: 'Man-Hours',
      accessor: (s) => (
        <span className="font-mono text-xs text-industrial-300">
          {s.has_valid_man_hours ? s.total_man_hours.toLocaleString() : 'Insufficient data'}
        </span>
      ),
    },
    {
      header: 'Precursor Metric',
      accessor: (s) => {
        if (s.has_valid_man_hours && s.precursor_density !== undefined) {
          return (
            <div>
              <span className="font-mono text-xs font-bold text-emerald-400">
                {s.precursor_density}
              </span>
              <span className="text-[9px] font-mono text-industrial-500 block uppercase">
                Density (per 10k hrs)
              </span>
            </div>
          );
        }
        return (
          <div>
            <span className="font-mono text-xs font-bold text-amber-300">
              {s.precursor_concentration_pct}%
            </span>
            <span className="text-[9px] font-mono text-industrial-500 block uppercase">
              Concentration (share)
            </span>
          </div>
        );
      },
    },
    {
      header: 'Action',
      accessor: (s) => (
        <Link
          href={`/reports?site=${encodeURIComponent(s.site)}`}
          className="inline-flex items-center gap-1 text-[10px] font-mono text-blue-400 hover:text-blue-300 transition-colors"
        >
          <span>Reports</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
      ),
    },
  ];

  return (
    <AppShell title="Site & Functional Location Intelligence">
      <div className="space-y-6 max-w-6xl mx-auto">
        <SectionCard
          title="Site Precursor Concentration & Exposure Matrix"
          subtitle="Precursor metrics across operational sites. Normalized density is calculated only when valid man-hours exist; precursor concentration is used as explicit fallback."
          action={
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-mono text-industrial-400">Sort by:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-industrial-950 border border-industrial-700 rounded px-2.5 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
                >
                  <option value="sif">SIF Precursor Count</option>
                  <option value="critical">High & Critical Priority</option>
                  <option value="escalation">Escalating Clusters</option>
                  <option value="density">Precursor Density</option>
                  <option value="reports">Total Reports</option>
                </select>
              </div>

              <a
                href="/api/v1/dashboard/export/sites"
                download
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-industrial-900 hover:bg-industrial-800 border border-industrial-700 text-xs font-mono text-industrial-200 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                Export CSV
              </a>
            </div>
          }
        >
          {loading ? (
            <div className="p-8 text-center font-mono text-xs text-industrial-400 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              Loading site intelligence...
            </div>
          ) : sortedSites.length === 0 ? (
            <EmptyState
              title="No Site Records Found"
              description="Ingest operational reports to calculate site precursor concentration metrics."
            />
          ) : (
            <DataTable columns={columns} data={sortedSites} />
          )}
        </SectionCard>
      </div>
    </AppShell>
  );
}
