'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { MetricCard } from '@/components/ui/MetricCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { DataTable, Column } from '@/components/ui/DataTable';
import {
  ReviewQueueItem,
  ReviewAnalyticsSummary,
  ReviewStatus,
} from '@/types';
import {
  UserCheck,
  RefreshCw,
  AlertTriangle,
  Flame,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowRight,
  Filter,
} from 'lucide-react';
import Link from 'next/link';

export default function ReviewPage() {
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [analytics, setAnalytics] = useState<ReviewAnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [sifFilter, setSifFilter] = useState<string>('');
  const [siteFilter, setSiteFilter] = useState<string>('');

  const fetchQueueAndAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const q = new URLSearchParams();
      if (statusFilter && statusFilter !== 'ALL') q.set('status', statusFilter);
      if (priorityFilter) q.set('priority', priorityFilter);
      if (sifFilter) q.set('sif', sifFilter);
      if (siteFilter) q.set('site', siteFilter);

      const qs = q.toString() ? `?${q.toString()}` : '';

      const [qRes, aRes] = await Promise.all([
        fetch(`/api/v1/reviews/queue${qs}`),
        fetch('/api/v1/reviews/analytics'),
      ]);

      if (qRes.ok) {
        const data = await qRes.json();
        setItems(data.items || []);
      }
      if (aRes.ok) {
        setAnalytics(await aRes.json());
      }
    } catch (err) {
      console.error('Failed to fetch review queue:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter, sifFilter, siteFilter]);

  useEffect(() => {
    fetchQueueAndAnalytics();
  }, [fetchQueueAndAnalytics]);

  const columns: Column<ReviewQueueItem>[] = [
    {
      header: 'Report ID',
      accessor: (item) => (
        <div className="space-y-0.5">
          <Link
            href={`/reports/${item.report_id}`}
            className="font-mono text-xs font-bold text-blue-400 hover:underline block"
          >
            {item.report_id}
          </Link>
          <span className="text-[10px] font-mono text-industrial-500">
            {item.report_date || 'N/A'}
          </span>
        </div>
      ),
    },
    {
      header: 'Location / Site',
      accessor: (item) => (
        <div className="space-y-0.5">
          <span className="text-xs font-mono text-industrial-200 block">
            {item.site || 'Cross-Site'}
          </span>
          <span className="text-[10px] font-mono text-industrial-400 truncate max-w-[140px] block">
            {item.functional_location || '—'}
          </span>
        </div>
      ),
    },
    {
      header: 'AI Finding (SIF / Priority)',
      accessor: (item) => (
        <div className="space-y-1">
          <div className="flex items-center gap-1.5">
            <span
              className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold uppercase border ${
                item.ai_sif_potential === 'YES'
                  ? 'bg-red-950 text-red-300 border-red-800'
                  : item.ai_sif_potential === 'UNCERTAIN'
                  ? 'bg-amber-950 text-amber-300 border-amber-800'
                  : 'bg-emerald-950 text-emerald-400 border-emerald-800'
              }`}
            >
              SIF: {item.ai_sif_potential || 'UNKNOWN'}
            </span>
            {item.ai_priority_level && (
              <span className="text-[9px] font-mono text-orange-300">
                {item.ai_priority_level.replace('_PRECURSOR', '')}
              </span>
            )}
          </div>
          <span className="text-[10px] font-mono text-purple-300 block">
            LSR: {item.ai_lsr || '—'}
          </span>
        </div>
      ),
    },
    {
      header: 'Narrative Snippet',
      accessor: (item) => (
        <span className="text-xs font-sans text-industrial-200 line-clamp-2 max-w-xs block">
          &quot;{item.narrative_snippet}&quot;
        </span>
      ),
    },
    {
      header: 'Review Status',
      accessor: (item) => {
        const st = item.review_status;
        const dec = item.latest_decision;
        if (st === 'REVIEWED') {
          return (
            <div className="space-y-0.5">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase bg-emerald-950/80 text-emerald-300 border border-emerald-700">
                <CheckCircle2 className="w-2.5 h-2.5" />
                REVIEWED
              </span>
              {dec && (
                <span className="text-[9px] font-mono text-industrial-400 block">
                  ({dec.replace('_', ' ')})
                </span>
              )}
            </div>
          );
        }
        if (st === 'NEEDS_MORE_INFORMATION') {
          return (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase bg-amber-950/80 text-amber-300 border border-amber-700">
              <HelpCircle className="w-2.5 h-2.5" />
              NEEDS INFO
            </span>
          );
        }
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase bg-industrial-900 text-industrial-400 border border-industrial-700">
            PENDING
          </span>
        );
      },
    },
    {
      header: 'Action',
      accessor: (item) => (
        <Link
          href={`/reports/${item.report_id}#review`}
          className="inline-flex items-center gap-1 px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-mono text-[10px] uppercase font-semibold transition-colors"
        >
          <span>Review</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
      ),
    },
  ];

  return (
    <AppShell title="HSE Review & Human-in-the-Loop Command Center">
      <div className="space-y-6 max-w-7xl mx-auto">
        {/* KPI Metrics Banner */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
          <MetricCard
            title="In Queue Scope"
            value={analytics?.total_in_scope ?? '—'}
            subtitle="Total Safety Reports"
            icon={UserCheck}
          />
          <MetricCard
            title="Pending Review"
            value={analytics?.pending_review ?? '—'}
            subtitle="Requires Verification"
            icon={AlertTriangle}
            variant={analytics && analytics.pending_review > 0 ? 'warning' : 'default'}
          />
          <MetricCard
            title="Total Reviewed"
            value={analytics?.total_reviewed ?? '—'}
            subtitle="Human Decisions Logged"
            icon={CheckCircle2}
            variant="success"
          />
          <MetricCard
            title="Confirmed AI"
            value={analytics?.confirmed_count ?? '—'}
            subtitle="Agreed with AI"
            icon={CheckCircle2}
          />
          <MetricCard
            title="Overridden"
            value={analytics?.overridden_count ?? '—'}
            subtitle="Modified AI Decision"
            icon={Flame}
            variant={analytics && analytics.overridden_count > 0 ? 'warning' : 'default'}
          />
          <MetricCard
            title="Needs More Info"
            value={analytics?.needs_more_info_count ?? '—'}
            subtitle="Missing Evidence Spans"
            icon={HelpCircle}
            variant="info"
          />
        </div>

        {/* Filter Bar */}
        <div className="p-3.5 bg-industrial-950/80 border border-industrial-800 rounded flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-industrial-200">
            <Filter className="w-3.5 h-3.5 text-blue-400" />
            <span>QUEUE FILTERS</span>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-industrial-900 border border-industrial-700 rounded px-2.5 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Review Statuses</option>
              <option value="UNREVIEWED">Pending Review</option>
              <option value="REVIEWED">Reviewed</option>
              <option value="NEEDS_MORE_INFORMATION">Needs More Information</option>
            </select>

            {/* SIF Filter */}
            <select
              value={sifFilter}
              onChange={(e) => setSifFilter(e.target.value)}
              className="bg-industrial-900 border border-industrial-700 rounded px-2.5 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
            >
              <option value="">All SIF Decisions</option>
              <option value="YES">SIF: YES</option>
              <option value="UNCERTAIN">SIF: UNCERTAIN</option>
              <option value="NO">SIF: NO</option>
            </select>

            {/* Priority Filter */}
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-industrial-900 border border-industrial-700 rounded px-2.5 py-1 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Priorities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH_PRIORITY_SIF_FPI_PRECURSOR">High Priority</option>
              <option value="SAFETY_REVIEW">Safety Review</option>
              <option value="ROUTINE">Routine</option>
              <option value="UNCERTAIN">Uncertain</option>
            </select>

            <button
              onClick={() => {
                setStatusFilter('ALL');
                setPriorityFilter('');
                setSifFilter('');
                setSiteFilter('');
              }}
              className="px-2.5 py-1 rounded bg-industrial-800 hover:bg-industrial-700 text-xs font-mono text-industrial-300 transition-colors"
            >
              Reset
            </button>
          </div>
        </div>

        {/* Review Queue Table */}
        <SectionCard
          title="Safety Reports Triage & Verification Queue"
          subtitle="AI findings presented for human inspection, verification, override, or rejection with full auditability."
        >
          {loading ? (
            <div className="p-8 text-center font-mono text-xs text-industrial-400 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              Loading HSE review queue...
            </div>
          ) : items.length === 0 ? (
            <EmptyState
              title="Review Queue Clear"
              description="No safety reports currently match the selected queue filters."
            />
          ) : (
            <DataTable columns={columns} data={items} />
          )}
        </SectionCard>
      </div>
    </AppShell>
  );
}
