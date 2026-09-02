'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { DataTable, Column } from '@/components/ui/DataTable';
import { ClusterDetailResponse, ClusterMemberResponse, TimelineEvent, EscalationBand } from '@/types';
import {
  ArrowLeft, RefreshCw, AlertTriangle, ShieldAlert, BookOpen,
  Activity, Wrench, Shield, MapPin, CheckCircle2, Clock, Layers,
} from 'lucide-react';
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
    <span className={`px-3 py-1 rounded text-xs font-mono font-bold uppercase border tracking-wider ${cfg.classes}`}>
      {cfg.label}
    </span>
  );
};

export default function ClusterDetailPage() {
  const params = useParams();
  const clusterIdStr = (params?.id as string) || '';
  const clusterId = parseInt(clusterIdStr, 10);

  const [cluster, setCluster] = useState<ClusterDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchClusterDetail = useCallback(async () => {
    if (!clusterId) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/clusters/${clusterId}`);
      if (res.ok) {
        const data = await res.json();
        setCluster(data);
      }
    } catch (err) {
      console.error('Failed to fetch cluster detail:', err);
    } finally {
      setLoading(false);
    }
  }, [clusterId]);

  useEffect(() => {
    fetchClusterDetail();
  }, [fetchClusterDetail]);

  const memberColumns: Column<ClusterMemberResponse>[] = [
    {
      header: 'Report ID',
      accessor: (m) => (
        <Link href={`/reports/${m.report_id}`} className="font-mono font-bold text-xs text-blue-400 hover:underline">
          {m.report_id}
        </Link>
      ),
    },
    {
      header: 'Date',
      accessor: (m) => m.report_date ? String(m.report_date) : '—',
    },
    {
      header: 'Location / Asset',
      accessor: (m) => (
        <span className="text-xs font-mono text-industrial-300">
          {m.functional_location || m.site || '—'}
        </span>
      ),
    },
    {
      header: 'Description',
      accessor: (m) => (
        <span className="text-xs font-sans text-industrial-200 truncate max-w-xs block">
          {m.short_description || '—'}
        </span>
      ),
    },
    {
      header: 'SIF Potential',
      accessor: (m) => {
        const val = m.sif_fpi_potential;
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
      accessor: (m) => (
        <span className="text-xs font-mono text-purple-300">
          {m.primary_life_saving_rule || '—'}
        </span>
      ),
    },
    {
      header: 'Similarity',
      accessor: (m) => (
        <span className="text-xs font-mono font-bold text-blue-300">
          {Math.round((m.similarity_to_cluster || 0.5) * 100)}%
        </span>
      ),
    },
    {
      header: 'HSE Review',
      accessor: (m) => (
        <Link
          href={`/reports/${m.report_id}#review`}
          className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-blue-400 hover:text-blue-300 transition-colors"
        >
          <span>Review</span>
          <ArrowLeft className="w-3 h-3 rotate-180" />
        </Link>
      ),
    },
  ];

  return (
    <AppShell title={`Cluster Detail: ${cluster?.cluster_name || clusterIdStr}`}>
      <div className="space-y-6 max-w-6xl mx-auto">
        <Link
          href="/clusters"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-industrial-400 hover:text-industrial-200 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Precursor Clusters Directory
        </Link>

        {loading ? (
          <SectionCard title="Loading Cluster Detail">
            <div className="p-8 text-center font-mono text-xs text-industrial-400 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              Loading precursor cluster analytics & timeline...
            </div>
          </SectionCard>
        ) : !cluster ? (
          <SectionCard title="Cluster Not Found">
            <EmptyState
              title="Precursor Cluster Missing"
              description={`No cluster record found matching ID '${clusterIdStr}'.`}
            />
          </SectionCard>
        ) : (
          <div className="space-y-6">
            {/* Header & Escalation Score Card */}
            <div className="p-5 bg-industrial-950 rounded border border-industrial-800 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Layers className="w-5 h-5 text-purple-400" />
                    <span className="text-[10px] font-mono text-industrial-500 uppercase">PRECURSOR CLUSTER</span>
                  </div>
                  <h1 className="text-xl font-mono font-bold text-industrial-100">{cluster.cluster_name}</h1>
                </div>

                <div className="flex items-center gap-4">
                  <div className="p-3 bg-industrial-900 border border-industrial-700 rounded text-center min-w-[100px]">
                    <span className="text-[9px] font-mono text-industrial-400 block uppercase">ESCALATION SCORE</span>
                    <span className="text-2xl font-mono font-bold text-industrial-100">{cluster.escalation_score}</span>
                    <span className="text-[9px] font-mono text-industrial-500 block">/ 100</span>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono text-industrial-400 uppercase block mb-1">Escalation Band</span>
                    <EscalationBandBadge band={cluster.escalation_band} />
                  </div>
                </div>
              </div>

              {/* Pattern Escalation Alert Banner */}
              {cluster.escalation_score >= 60.0 && (
                <div className="p-3.5 bg-red-950/80 border border-red-800 rounded text-xs font-mono text-red-200 flex items-start gap-2.5">
                  <ShieldAlert className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <span className="font-bold text-red-300 uppercase tracking-wider block">PATTERN ESCALATION ALERT ACTIVE</span>
                    <p className="font-sans text-red-200/90 leading-relaxed">
                      Multiple semantically related precursor incidents indicate recurring safety mechanism accumulation at shared asset or barrier.
                    </p>
                  </div>
                </div>
              )}

              {/* Why Escalating Evidence Checklist */}
              <div className="p-3.5 bg-industrial-900/60 rounded border border-industrial-800 space-y-2">
                <span className="text-[10px] font-mono font-bold text-industrial-400 uppercase tracking-wider block">
                  Why is this Pattern Escalating?
                </span>
                <ul className="space-y-1.5 text-xs font-sans text-industrial-200">
                  {cluster.why_escalating && cluster.why_escalating.map((reason, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-emerald-400 font-mono font-bold">✓</span>
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Common Mechanism Breakdown Cards */}
            <SectionCard title="Common Safety Mechanism Attributes">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-1">
                  <span className="text-[9px] font-mono text-industrial-500 uppercase block">Common Hazard</span>
                  <span className="text-xs font-mono text-industrial-200 font-semibold">{cluster.common_hazard || '—'}</span>
                </div>
                <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-1">
                  <span className="text-[9px] font-mono text-industrial-500 uppercase block">Common Activity</span>
                  <span className="text-xs font-mono text-industrial-200 font-semibold">{cluster.common_activity || '—'}</span>
                </div>
                <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-1">
                  <span className="text-[9px] font-mono text-industrial-500 uppercase block">Common Equipment</span>
                  <span className="text-xs font-mono text-industrial-200 font-semibold">{cluster.common_equipment || '—'}</span>
                </div>
                <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-1">
                  <span className="text-[9px] font-mono text-industrial-500 uppercase block">Common Barrier</span>
                  <span className="text-xs font-mono text-emerald-300 font-semibold">{cluster.common_barrier || '—'}</span>
                </div>
                <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-1">
                  <span className="text-[9px] font-mono text-industrial-500 uppercase block">Common Life-Saving Rule</span>
                  <span className="text-xs font-mono text-purple-300 font-semibold">{cluster.common_lsr || '—'}</span>
                </div>
                <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-1">
                  <span className="text-[9px] font-mono text-industrial-500 uppercase block">Common Asset / Location</span>
                  <span className="text-xs font-mono text-industrial-200 font-semibold">{cluster.common_asset || '—'}</span>
                </div>
              </div>
            </SectionCard>

            {/* Timeline Visualization */}
            <SectionCard
              title="Temporal Precursor Accumulation Timeline"
              subtitle="Chronological sequence demonstrating precursor repetition and accumulating risk across time"
            >
              {!cluster.timeline || cluster.timeline.length === 0 ? (
                <div className="p-4 text-center text-xs font-mono text-industrial-500 italic">No timeline events.</div>
              ) : (
                <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-industrial-800">
                  {cluster.timeline.map((ev, idx) => (
                    <div key={ev.report_id} className="relative space-y-1.5">
                      <span className="absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full bg-blue-500 border-2 border-industrial-950" />
                      <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-1">
                        <div className="flex items-center justify-between text-xs font-mono">
                          <div className="flex items-center gap-2">
                            <span className="text-industrial-500">Day {ev.days_from_first + 1}</span>
                            <span className="text-industrial-600">({ev.report_date ? String(ev.report_date) : 'N/A'})</span>
                            <Link href={`/reports/${ev.report_id}`} className="text-blue-400 font-bold hover:underline">
                              {ev.report_id}
                            </Link>
                          </div>
                          {ev.sif_fpi_potential === 'YES' && (
                            <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-red-950 text-red-300 border border-red-800">
                              SIF PRECURSOR
                            </span>
                          )}
                        </div>
                        <p className="text-xs font-sans text-industrial-200 leading-snug">
                          &quot;{ev.narrative_snippet}&quot;
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>

            {/* Member Reports Table */}
            <SectionCard title={`Cluster Member Reports (${cluster.members.length})`}>
              <DataTable columns={memberColumns} data={cluster.members} />
            </SectionCard>
          </div>
        )}
      </div>
    </AppShell>
  );
}
