'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { DataTable, Column } from '@/components/ui/DataTable';
import { ClusterResponse, EscalationBand } from '@/types';
import { Network, RefreshCw, Sparkles, AlertTriangle, ShieldAlert, ArrowRight, Layers } from 'lucide-react';
import Link from 'next/link';

const EscalationBandBadge = ({ band }: { band?: EscalationBand }) => {
  const map: Record<EscalationBand, { label: string; classes: string }> = {
    CRITICAL_PATTERN: { label: 'CRITICAL PATTERN', classes: 'bg-red-950/90 text-red-300 border-red-700 font-bold animate-pulse' },
    HIGH:             { label: 'HIGH PATTERN',     classes: 'bg-orange-950/90 text-orange-300 border-orange-700 font-bold' },
    REVIEW:           { label: 'REVIEW',           classes: 'bg-amber-950/90 text-amber-300 border-amber-700 font-semibold' },
    WATCH:            { label: 'WATCH',            classes: 'bg-blue-950/90 text-blue-300 border-blue-700' },
    LOW:              { label: 'LOW ACTIVITY',     classes: 'bg-industrial-900 text-industrial-400 border-industrial-700' },
  };
  const cfg = band ? (map[band] ?? map.LOW) : map.LOW;
  return (
    <span className={`px-2.5 py-1 rounded text-[10px] font-mono uppercase border tracking-wider ${cfg.classes}`}>
      {cfg.label}
    </span>
  );
};

export default function PrecursorClustersPage() {
  const [clusters, setClusters] = useState<ClusterResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [rebuilding, setRebuilding] = useState(false);
  const [filterBand, setFilterBand] = useState<string>('ALL');

  const fetchClusters = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/clusters');
      if (res.ok) {
        const data = await res.json();
        setClusters(data);
      }
    } catch (err) {
      console.error('Failed to fetch precursor clusters:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClusters();
  }, [fetchClusters]);

  const handleRebuildClusters = async () => {
    setRebuilding(true);
    try {
      const res = await fetch('/api/v1/clusters/rebuild', { method: 'POST' });
      if (res.ok) {
        await fetchClusters();
      }
    } catch (err) {
      console.error('Failed to rebuild clusters:', err);
    } finally {
      setRebuilding(false);
    }
  };

  const filteredClusters = clusters.filter((c) => {
    if (filterBand === 'ALL') return true;
    if (filterBand === 'CRITICAL') return c.escalation_band === 'CRITICAL_PATTERN';
    if (filterBand === 'HIGH') return c.escalation_band === 'HIGH';
    if (filterBand === 'REVIEW') return c.escalation_band === 'REVIEW';
    if (filterBand === 'WATCH') return c.escalation_band === 'WATCH';
    return true;
  });

  const columns: Column<ClusterResponse>[] = [
    {
      header: 'Escalation Score',
      accessor: (c) => (
        <div className="p-2 bg-industrial-950 border border-industrial-700 rounded text-center min-w-[60px]">
          <span className="text-xs font-mono font-bold text-industrial-100 block">{c.escalation_score}</span>
          <span className="text-[8px] font-mono text-industrial-500 block uppercase">/ 100</span>
        </div>
      ),
    },
    {
      header: 'Escalation Band',
      accessor: (c) => <EscalationBandBadge band={c.escalation_band} />,
    },
    {
      header: 'Precursor Cluster Name',
      accessor: (c) => (
        <div className="space-y-0.5">
          <Link href={`/clusters/${c.id}`} className="font-mono font-bold text-xs text-blue-400 hover:underline block">
            {c.cluster_name}
          </Link>
          <span className="text-[10px] font-mono text-industrial-400 block truncate max-w-xs">
            {c.common_mechanism || 'General Safety Precursor Pattern'}
          </span>
        </div>
      ),
    },
    {
      header: 'Recurrence Count',
      accessor: (c) => (
        <span className="px-2.5 py-1 rounded bg-industrial-900 border border-industrial-700 text-xs font-mono font-bold text-purple-300">
          {c.recurrence_count} {c.recurrence_count === 1 ? 'Report' : 'Reports'}
        </span>
      ),
    },
    {
      header: 'Common Asset',
      accessor: (c) => (
        <span className="text-xs font-mono text-industrial-300">
          {c.common_asset || 'Cross-Asset Pattern'}
        </span>
      ),
    },
    {
      header: 'Common LSR',
      accessor: (c) => (
        <span className="text-xs font-mono text-purple-300">
          {c.common_lsr || '—'}
        </span>
      ),
    },
    {
      header: 'Action',
      accessor: (c) => (
        <Link
          href={`/clusters/${c.id}`}
          className="inline-flex items-center gap-1 px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-mono text-[10px] uppercase font-semibold transition-colors"
        >
          <span>Inspect Cluster</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
      ),
    },
  ];

  return (
    <AppShell title="Precursor Safety Clusters">
      <div className="space-y-6 max-w-6xl mx-auto">
        <SectionCard
          title="Precursor Mechanism & Pattern Clusters"
          subtitle="Phase 6 — Grouped safety reports sharing underlying mechanisms, hazards, assets, or Life-Saving Rules across time."
          action={
            <div className="flex items-center gap-3">
              <button
                onClick={handleRebuildClusters}
                disabled={rebuilding}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-semibold uppercase tracking-wider transition-colors disabled:opacity-50"
              >
                {rebuilding ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                Rebuild Clusters
              </button>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-mono text-industrial-400">Escalation Filter:</span>
                <select
                  value={filterBand}
                  onChange={(e) => setFilterBand(e.target.value)}
                  className="bg-industrial-950 border border-industrial-700 rounded px-2.5 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
                >
                  <option value="ALL">All Escalation Bands</option>
                  <option value="CRITICAL">Critical Pattern Only</option>
                  <option value="HIGH">High Pattern Only</option>
                  <option value="REVIEW">Review Only</option>
                  <option value="WATCH">Watch Only</option>
                </select>
              </div>
            </div>
          }
        >
          <div className="space-y-4">
            {loading ? (
              <div className="p-8 text-center font-mono text-xs text-industrial-400 flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
                Loading precursor safety clusters...
              </div>
            ) : filteredClusters.length === 0 ? (
              <EmptyState
                title="No Precursor Clusters Found"
                description="No recurring safety precursor patterns match the selected escalation filter. Click 'Rebuild Clusters' above."
              />
            ) : (
              <DataTable columns={columns} data={filteredClusters} />
            )}
          </div>
        </SectionCard>
      </div>
    </AppShell>
  );
}
