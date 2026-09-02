'use client';

import React, { useEffect, useState, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { MetricCard } from '@/components/ui/MetricCard';
import { SectionCard } from '@/components/ui/SectionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { DataTable, Column } from '@/components/ui/DataTable';
import { GlobalFilterBar, FilterState } from '@/components/dashboard/GlobalFilterBar';
import {
  DashboardSummary,
  TrendPoint,
  SiteSummary,
  ActivitySummary,
  HazardSummary,
  LsrSummary,
  BarrierSummary,
  RecentAlertSummary,
  DataQualitySummary,
  SourceReport,
} from '@/types';
import {
  FileText,
  AlertTriangle,
  Flame,
  ShieldAlert,
  GitMerge,
  Shield,
  Layers,
  ArrowRight,
  Download,
  CheckCircle2,
  RefreshCw,
  Activity,
  MapPin,
  HelpCircle,
} from 'lucide-react';
import Link from 'next/link';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Initialize filters from searchParams
  const [filters, setFilters] = useState<FilterState>({
    window: searchParams?.get('window') || '30d',
    site: searchParams?.get('site') || '',
    lsr: searchParams?.get('lsr') || '',
    priority_level: searchParams?.get('priority_level') || '',
    sif_status: searchParams?.get('sif_status') || '',
    barrier_condition: searchParams?.get('barrier_condition') || '',
  });

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [sites, setSites] = useState<SiteSummary[]>([]);
  const [activities, setActivities] = useState<ActivitySummary[]>([]);
  const [hazards, setHazards] = useState<HazardSummary[]>([]);
  const [lsrList, setLsrList] = useState<LsrSummary[]>([]);
  const [barriers, setBarriers] = useState<BarrierSummary[]>([]);
  const [alerts, setAlerts] = useState<RecentAlertSummary[]>([]);
  const [dataQuality, setDataQuality] = useState<DataQualitySummary | null>(null);
  const [priorityQueue, setPriorityQueue] = useState<SourceReport[]>([]);

  // Update URL params when filters change
  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters);
    const params = new URLSearchParams();
    if (newFilters.window && newFilters.window !== '30d') params.set('window', newFilters.window);
    if (newFilters.site) params.set('site', newFilters.site);
    if (newFilters.lsr) params.set('lsr', newFilters.lsr);
    if (newFilters.priority_level) params.set('priority_level', newFilters.priority_level);
    if (newFilters.sif_status) params.set('sif_status', newFilters.sif_status);
    if (newFilters.barrier_condition) params.set('barrier_condition', newFilters.barrier_condition);
    const qs = params.toString();
    router.replace(qs ? `/?${qs}` : '/');
  };

  const handleResetFilters = () => {
    const emptyFilters: FilterState = {
      window: '30d',
      site: '',
      lsr: '',
      priority_level: '',
      sif_status: '',
      barrier_condition: '',
    };
    handleFilterChange(emptyFilters);
  };

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      const q = new URLSearchParams();
      if (filters.site) q.set('site', filters.site);
      if (filters.lsr) q.set('lsr', filters.lsr);
      if (filters.priority_level) q.set('priority_level', filters.priority_level);
      if (filters.sif_status) q.set('sif_status', filters.sif_status);
      if (filters.barrier_condition) q.set('barrier_condition', filters.barrier_condition);

      const qs = q.toString() ? `?${q.toString()}` : '';

      const [
        sumRes,
        trendRes,
        siteRes,
        actRes,
        hazRes,
        lsrRes,
        barRes,
        alertRes,
        dqRes,
        prioRes,
      ] = await Promise.all([
        fetch(`/api/v1/dashboard/summary${qs}`),
        fetch(`/api/v1/dashboard/trends?window=${filters.window}${q.toString() ? `&${q.toString()}` : ''}`),
        fetch(`/api/v1/dashboard/sites${qs}`),
        fetch(`/api/v1/dashboard/activities${qs}`),
        fetch(`/api/v1/dashboard/hazards${qs}`),
        fetch(`/api/v1/dashboard/lsr${qs}`),
        fetch(`/api/v1/dashboard/barriers${qs}`),
        fetch('/api/v1/dashboard/alerts'),
        fetch('/api/v1/dashboard/data-quality'),
        fetch('/api/v1/reports?size=5'),
      ]);

      if (sumRes.ok) setSummary(await sumRes.json());
      if (trendRes.ok) setTrends(await trendRes.json());
      if (siteRes.ok) setSites(await siteRes.json());
      if (actRes.ok) setActivities(await actRes.json());
      if (hazRes.ok) setHazards(await hazRes.json());
      if (lsrRes.ok) setLsrList(await lsrRes.json());
      if (barRes.ok) setBarriers(await barRes.json());
      if (alertRes.ok) setAlerts(await alertRes.json());
      if (dqRes.ok) setDataQuality(await dqRes.json());
      if (prioRes.ok) {
        const pData = await prioRes.json();
        const items = pData.items || [];
        items.sort((a: any, b: any) => (b.priority_score || 0) - (a.priority_score || 0));
        setPriorityQueue(items);
      }
    } catch (err) {
      console.error('Failed to fetch dashboard intelligence:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Site ranking columns
  const siteColumns: Column<SiteSummary>[] = [
    {
      header: 'Operational Site',
      accessor: (s) => (
        <span className="font-mono text-xs font-semibold text-industrial-100">{s.site}</span>
      ),
    },
    {
      header: 'Reports',
      accessor: (s) => <span className="font-mono text-xs text-industrial-300">{s.report_count}</span>,
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
        <span className="font-mono text-xs text-orange-300">
          {s.high_priority_count + s.critical_count}
        </span>
      ),
    },
    {
      header: 'Escalating Patterns',
      accessor: (s) => (
        <span className="font-mono text-xs text-purple-300">
          {s.escalating_cluster_count > 0 ? `${s.escalating_cluster_count} active` : '—'}
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
  ];

  return (
    <AppShell title="HSE Intelligence Command Center">
      <div className="space-y-6 max-w-7xl mx-auto">
        {/* Global Filter Bar */}
        <GlobalFilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
          onReset={handleResetFilters}
          loading={loading}
        />

        {/* ── PART 3: Executive Summary KPI Cards ───────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
          <MetricCard
            title="Total Reports"
            value={summary?.total_reports ?? '—'}
            subtitle={summary?.comparison_period_label || 'All Ingested Records'}
            icon={FileText}
          />
          <MetricCard
            title="SIF Precursors"
            value={summary?.sif_yes ?? '—'}
            subtitle={summary?.sif_share_pct !== undefined ? `${summary.sif_share_pct}% of analyzed` : 'Screening in progress'}
            icon={ShieldAlert}
            variant={summary && summary.sif_yes > 0 ? 'critical' : 'default'}
          />
          <MetricCard
            title="High-Priority SIF"
            value={summary?.high_priority ?? '—'}
            subtitle="Immediate Action Precursors"
            icon={Flame}
            variant={summary && summary.high_priority > 0 ? 'warning' : 'default'}
          />
          <MetricCard
            title="Critical Overrides"
            value={summary?.critical ?? '—'}
            subtitle="Safety Rule Overrides"
            icon={AlertTriangle}
            variant={summary && summary.critical > 0 ? 'critical' : 'default'}
          />
          <MetricCard
            title="Escalating Patterns"
            value={summary?.escalating_clusters ?? '—'}
            subtitle="Accumulation Warnings"
            icon={GitMerge}
            variant={summary && summary.escalating_clusters > 0 ? 'warning' : 'default'}
          />
          <MetricCard
            title="Active Clusters"
            value={summary?.active_clusters ?? '—'}
            subtitle="Precursor Mechanism Groups"
            icon={Layers}
            variant="info"
          />
        </div>

        {/* ── SIF/FPI Summary Share + Time-Series Trend ─────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: SIF Distribution Share */}
          <SectionCard
            title="SIF / FPI Screening Share"
            subtitle="Share of analyzed reports (Not probability of death)"
          >
            {summary && summary.analyzed_reports > 0 ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-red-400 font-bold">YES — SIF Precursor</span>
                    <span className="text-industrial-200">
                      {summary.sif_yes} ({summary.sif_share_pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-industrial-950 rounded-full h-2 overflow-hidden border border-industrial-800">
                    <div
                      className="bg-red-500 h-full rounded-full"
                      style={{ width: `${summary.sif_share_pct || 0}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-amber-400 font-bold">UNCERTAIN — Needs Review</span>
                    <span className="text-industrial-200">
                      {summary.sif_uncertain} (
                      {roundPct(summary.sif_uncertain, summary.analyzed_reports)}%)
                    </span>
                  </div>
                  <div className="w-full bg-industrial-950 rounded-full h-2 overflow-hidden border border-industrial-800">
                    <div
                      className="bg-amber-500 h-full rounded-full"
                      style={{
                        width: `${roundPct(summary.sif_uncertain, summary.analyzed_reports)}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-emerald-400 font-bold">NO — Non-SIF Observation</span>
                    <span className="text-industrial-200">
                      {summary.sif_no} ({roundPct(summary.sif_no, summary.analyzed_reports)}%)
                    </span>
                  </div>
                  <div className="w-full bg-industrial-950 rounded-full h-2 overflow-hidden border border-industrial-800">
                    <div
                      className="bg-emerald-500 h-full rounded-full"
                      style={{
                        width: `${roundPct(summary.sif_no, summary.analyzed_reports)}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="pt-2 border-t border-industrial-800 text-[10px] font-mono text-industrial-400 flex justify-between">
                  <span>Analyzed: {summary.analyzed_reports}</span>
                  <span>Total Ingested: {summary.total_reports}</span>
                </div>
              </div>
            ) : (
              <EmptyState
                title="No Screening Data"
                description="Run SIF screening across ingested reports to calculate share distribution."
              />
            )}
          </SectionCard>

          {/* Right 2 Columns: Time-Series Trend */}
          <div className="lg:col-span-2">
            <SectionCard
              title="Precursor Accumulation Trend"
              subtitle={`Daily SIF/FPI precursor frequency (${filters.window.toUpperCase()} window)`}
            >
              {trends.length > 0 ? (
                <div className="h-60 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorSif" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                      <XAxis dataKey="date" stroke="#737373" fontSize={10} tickLine={false} />
                      <YAxis stroke="#737373" fontSize={10} tickLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#404040', fontSize: '11px', fontFamily: 'monospace' }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />
                      <Area type="monotone" dataKey="total_reports" name="Total Reports" stroke="#3b82f6" fillOpacity={1} fill="url(#colorTotal)" />
                      <Area type="monotone" dataKey="sif_yes" name="SIF Precursors" stroke="#ef4444" fillOpacity={1} fill="url(#colorSif)" />
                      <Area type="monotone" dataKey="sif_uncertain" name="Uncertain" stroke="#f59e0b" fillOpacity={0} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState
                  title="No Temporal Trend Data"
                  description="No report activity recorded within the selected filter window."
                />
              )}
            </SectionCard>
          </div>
        </div>

        {/* ── HSE Priority Queue Preview & Recent Escalating Patterns ──── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Priority Queue Preview */}
          <SectionCard
            title="HSE Priority Queue Preview"
            subtitle="Highest-urgency safety reports sorted by critical override & SIF evidence"
            action={
              <Link
                href="/priority"
                className="inline-flex items-center gap-1 text-xs font-mono text-blue-400 hover:text-blue-300 transition-colors"
              >
                <span>View Full Queue</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            }
          >
            {priorityQueue.length > 0 ? (
              <div className="space-y-2.5">
                {priorityQueue.slice(0, 5).map((r) => (
                  <div
                    key={r.report_id}
                    className="p-3 bg-industrial-950 rounded border border-industrial-800 flex items-center justify-between gap-3 hover:border-industrial-700 transition-colors"
                  >
                    <div className="space-y-0.5 min-w-0">
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/reports/${r.report_id}`}
                          className="font-mono text-xs font-bold text-blue-400 hover:underline"
                        >
                          {r.report_id}
                        </Link>
                        <span className="text-[9px] font-mono text-industrial-400">
                          {r.site || 'Cross-Site'}
                        </span>
                      </div>
                      <p className="text-xs font-sans text-industrial-200 truncate">
                        {r.narrative}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {r.priority_score !== undefined && (
                        <div className="p-1.5 bg-industrial-900 border border-industrial-700 rounded text-center min-w-[40px]">
                          <span className="text-xs font-mono font-bold text-industrial-100 block">
                            {r.priority_score}
                          </span>
                        </div>
                      )}
                      <span
                        className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase border ${
                          r.priority_level === 'CRITICAL'
                            ? 'bg-red-950 text-red-300 border-red-800'
                            : 'bg-orange-950 text-orange-300 border-orange-800'
                        }`}
                      >
                        {r.priority_level?.replace('_PRECURSOR', '') || 'ROUTINE'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No Priority Items"
                description="Run HSE priority calculation to populate prioritized precursor queue."
              />
            )}
          </SectionCard>

          {/* Escalating Precursor Patterns */}
          <SectionCard
            title="Escalating Precursor Patterns"
            subtitle="Precursor clusters accumulating recurrent mechanism risk"
            action={
              <Link
                href="/clusters"
                className="inline-flex items-center gap-1 text-xs font-mono text-blue-400 hover:text-blue-300 transition-colors"
              >
                <span>View All Clusters</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            }
          >
            {alerts.length > 0 ? (
              <div className="space-y-2.5">
                {alerts.slice(0, 5).map((a) => (
                  <div
                    key={a.id}
                    className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-1.5 hover:border-industrial-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {a.cluster_id ? (
                          <Link
                            href={`/clusters/${a.cluster_id}`}
                            className="font-mono text-xs font-bold text-purple-300 hover:underline"
                          >
                            {a.cluster_name}
                          </Link>
                        ) : (
                          <span className="font-mono text-xs font-bold text-purple-300">
                            {a.cluster_name}
                          </span>
                        )}
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-red-950 text-red-300 border border-red-800">
                          SCORE {Math.round(a.escalation_score)}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-industrial-500">
                        {a.created_at}
                      </span>
                    </div>
                    <p className="text-xs font-sans text-industrial-200 line-clamp-1">
                      {a.reason}
                    </p>
                    {a.location && (
                      <div className="flex items-center gap-1 text-[10px] font-mono text-industrial-400">
                        <MapPin className="w-3 h-3 text-industrial-500" />
                        <span>Asset: {a.location}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No Escalating Patterns"
                description="No precursor accumulation threshold alerts detected in database."
              />
            )}
          </SectionCard>
        </div>

        {/* ── Site & Functional Location Intelligence Table ─────────────── */}
        <SectionCard
          title="Site & Functional Location Intelligence"
          subtitle="Cross-location precursor density ranking (Density computed when valid man-hours exist; concentration fallback otherwise)"
          action={
            <a
              href="/api/v1/dashboard/export/sites"
              download
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-industrial-900 hover:bg-industrial-800 border border-industrial-700 text-xs font-mono text-industrial-200 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Export CSV
            </a>
          }
        >
          {sites.length > 0 ? (
            <DataTable columns={siteColumns} data={sites} />
          ) : (
            <EmptyState
              title="No Site Records"
              description="Upload location-tagged report datasets to visualize site precursor matrix."
            />
          )}
        </SectionCard>

        {/* ── Activity & Hazard Intelligence ───────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Activities */}
          <SectionCard
            title="Activity Precursor Intelligence"
            subtitle="High-risk operational activities ranked by SIF precursor volume"
          >
            {activities.length > 0 ? (
              <div className="space-y-2">
                {activities.slice(0, 6).map((act, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-industrial-950 rounded border border-industrial-800 flex items-center justify-between text-xs font-mono"
                  >
                    <span className="font-semibold text-industrial-200">{act.activity}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-industrial-400">{act.report_count} reports</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-950 text-red-300 border border-red-800">
                        {act.sif_count} SIF
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No Activity Facts"
                description="Extract AI safety facts to aggregate operational activities."
              />
            )}
          </SectionCard>

          {/* Top Hazards */}
          <SectionCard
            title="Hazard Precursor Intelligence"
            subtitle="Observed hazards ranked by precursor frequency"
          >
            {hazards.length > 0 ? (
              <div className="space-y-2">
                {hazards.slice(0, 6).map((haz, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-industrial-950 rounded border border-industrial-800 flex items-center justify-between text-xs font-mono"
                  >
                    <span className="font-semibold text-industrial-200">{haz.hazard}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-industrial-400">{haz.report_count} reports</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-950 text-orange-300 border border-orange-800">
                        {haz.sif_count} SIF
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No Hazard Facts"
                description="Extract AI safety facts to aggregate observed hazards."
              />
            )}
          </SectionCard>
        </div>

        {/* ── Life-Saving Rule Matrix (9 Project Rules) ─────────────────── */}
        <SectionCard
          title="Life-Saving Rules (LSR) Precursor Matrix"
          subtitle="Precursor mapping across all 9 official project Life-Saving Rules"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {lsrList.map((l) => (
              <div
                key={l.lsr}
                className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-purple-300">{l.lsr}</span>
                  <span className="text-[10px] font-mono text-industrial-500">
                    {l.mapped_count} Mapped
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-red-400 font-bold">{l.sif_yes_count} SIF Precursors</span>
                  <span className="text-orange-400">{l.high_priority_count} High Priority</span>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>

        {/* ── Barrier Intelligence & Data Quality ──────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Barrier Weakness Matrix */}
          <SectionCard
            title="Barrier Weakness Intelligence"
            subtitle="Ranked by failure evidence (Failed, Absent, Degraded)"
            action={
              <Link
                href="/barriers"
                className="inline-flex items-center gap-1 text-xs font-mono text-blue-400 hover:text-blue-300 transition-colors"
              >
                <span>Full Barrier Matrix</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            }
          >
            {barriers.length > 0 ? (
              <div className="space-y-2.5">
                {barriers.slice(0, 5).map((b) => (
                  <div
                    key={b.barrier}
                    className="p-2.5 bg-industrial-950 rounded border border-industrial-800 flex items-center justify-between text-xs font-mono"
                  >
                    <div>
                      <span className="font-semibold text-industrial-200 block">{b.barrier}</span>
                      <span className="text-[10px] text-industrial-500">
                        Total mentions: {b.total_mentions}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px]">
                      {b.failed_count > 0 && (
                        <span className="px-1.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-800">
                          {b.failed_count} FAILED
                        </span>
                      )}
                      {b.degraded_count > 0 && (
                        <span className="px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                          {b.degraded_count} DEGRADED
                        </span>
                      )}
                      <span className="px-2 py-0.5 rounded font-bold bg-industrial-900 text-industrial-200 border border-industrial-700">
                        Score {b.weakness_score}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No Barrier Degradation Data"
                description="Extract AI safety facts to track physical & procedural barrier weaknesses."
              />
            )}
          </SectionCard>

          {/* Data Quality & Pipeline Coverage */}
          <SectionCard
            title="Data Quality & Pipeline Coverage"
            subtitle="Completeness metrics ensuring decisions rest on solid data"
          >
            {dataQuality ? (
              <div className="space-y-3 font-mono text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-2.5 bg-industrial-950 rounded border border-industrial-800">
                    <span className="text-industrial-500 text-[10px] block uppercase">AI Analyzed</span>
                    <span className="text-industrial-100 font-bold">
                      {dataQuality.analyzed_count} / {dataQuality.total_imported}
                    </span>
                  </div>
                  <div className="p-2.5 bg-industrial-950 rounded border border-industrial-800">
                    <span className="text-industrial-500 text-[10px] block uppercase">SIF Screened</span>
                    <span className="text-industrial-100 font-bold">
                      {dataQuality.sif_screened_count}
                    </span>
                  </div>
                  <div className="p-2.5 bg-industrial-950 rounded border border-industrial-800">
                    <span className="text-industrial-500 text-[10px] block uppercase">LSR Mapped</span>
                    <span className="text-industrial-100 font-bold">
                      {dataQuality.lsr_mapped_count}
                    </span>
                  </div>
                  <div className="p-2.5 bg-industrial-950 rounded border border-industrial-800">
                    <span className="text-industrial-500 text-[10px] block uppercase">Vector Embeddings</span>
                    <span className="text-emerald-400 font-bold">
                      {dataQuality.embedding_coverage_pct}%
                    </span>
                  </div>
                </div>

                <div className="pt-2 border-t border-industrial-800 space-y-1.5 text-[11px]">
                  <span className="text-industrial-400 font-bold block">Field Completeness:</span>
                  {Object.entries(dataQuality.field_completeness).map(([f, pct]) => (
                    <div key={f} className="flex justify-between text-industrial-300">
                      <span className="capitalize">{f.replace('_', ' ')}</span>
                      <span>{pct}%</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <EmptyState title="No Data Quality Info" description="Database metrics loading..." />
            )}
          </SectionCard>
        </div>
      </div>
    </AppShell>
  );
}

function roundPct(val: number, denom: number): number {
  if (!denom) return 0;
  return Math.round((val / denom) * 100);
}

export default function OverviewPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center font-mono text-industrial-400">Loading Dashboard...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
