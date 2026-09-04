'use client';

import React, { useEffect, useState, useCallback, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ArrowRight, Activity, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import {
  DashboardSummary,
  SourceReport,
  RecentAlertSummary,
} from '@/types';

function DashboardContent() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [priorityQueue, setPriorityQueue] = useState<SourceReport[]>([]);
  const [alerts, setAlerts] = useState<RecentAlertSummary[]>([]);

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      const [sumRes, prioRes, alertRes] = await Promise.all([
        fetch('/api/v1/dashboard/summary'),
        fetch('/api/v1/reports?size=5'),
        fetch('/api/v1/dashboard/alerts'),
      ]);

      if (sumRes.ok) setSummary(await sumRes.json());
      if (prioRes.ok) {
        const pData = await prioRes.json();
        const items = pData.items || [];
        items.sort((a: any, b: any) => (b.priority_score || 0) - (a.priority_score || 0));
        setPriorityQueue(items);
      }
      if (alertRes.ok) setAlerts(await alertRes.json());
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const critical = summary?.critical || 0;
  const high = summary?.high_priority || 0;
  const review = summary?.sif_uncertain || 0;
  const total = summary?.total_reports || 1; // prevent div by zero
  const normal = Math.max(0, total - (critical + high + review));
  
  const pCrit = (critical / total) * 100;
  const pHigh = (high / total) * 100;
  const pReview = (review / total) * 100;
  const pNormal = (normal / total) * 100;

  return (
    <AppShell title="Overview">
      <div className="max-w-5xl mx-auto space-y-12">

        {/* ── 5 Second View: Current Safety Status ────────────────────── */}
        <div>
          <h2 className="text-[13px] font-semibold tracking-wider uppercase text-industrial-500 mb-6">
            Current Safety Status
          </h2>
          
          <div className="flex flex-col md:flex-row md:items-end gap-12 border-b border-industrial-850 pb-8">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                {(critical > 0 || high > 0) ? (
                  <AlertCircle className="w-5 h-5 text-amber-500" />
                ) : (
                  <Activity className="w-5 h-5 text-emerald-500" />
                )}
                <h3 className="text-xl font-semibold text-industrial-100">
                  {(critical > 0 || high > 0) ? 'Attention Required' : 'Operations Normal'}
                </h3>
              </div>
              <p className="text-[13px] text-industrial-500">
                {total.toLocaleString()} total reports analyzed
              </p>
            </div>

            <div className="flex items-center gap-8 md:gap-12">
              <div className="flex flex-col">
                <span className="text-3xl font-semibold text-industrial-100 mb-1">{critical}</span>
                <span className="text-[11px] font-medium uppercase text-industrial-600 flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-red-500"/>Critical</span>
              </div>
              <div className="flex flex-col">
                <span className="text-3xl font-semibold text-industrial-100 mb-1">{high}</span>
                <span className="text-[11px] font-medium uppercase text-industrial-600 flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-amber-500"/>High</span>
              </div>
              <div className="flex flex-col">
                <span className="text-3xl font-semibold text-industrial-100 mb-1">{review}</span>
                <span className="text-[11px] font-medium uppercase text-industrial-600 flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-yellow-500"/>Review</span>
              </div>
              <div className="flex flex-col">
                <span className="text-3xl font-semibold text-industrial-100 mb-1">{normal}</span>
                <span className="text-[11px] font-medium uppercase text-industrial-600 flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-emerald-500"/>Normal</span>
              </div>
            </div>
          </div>
          
          {/* Risk Distribution Bar */}
          <div className="mt-6">
             <div className="flex items-center justify-between text-[11px] font-medium uppercase text-industrial-600 mb-2">
                <span>Risk Distribution</span>
             </div>
             <div className="flex h-2.5 w-full rounded-full overflow-hidden bg-industrial-900 gap-0.5">
                {pCrit > 0 && <div style={{width: `${pCrit}%`}} className="bg-red-500 transition-all" title="Critical"/>}
                {pHigh > 0 && <div style={{width: `${pHigh}%`}} className="bg-amber-500 transition-all" title="High"/>}
                {pReview > 0 && <div style={{width: `${pReview}%`}} className="bg-yellow-500 transition-all" title="Review"/>}
                {pNormal > 0 && <div style={{width: `${pNormal}%`}} className="bg-emerald-500 transition-all" title="Normal"/>}
             </div>
          </div>
        </div>

        {/* ── 30 Second View: Needs Attention ──────────────────────── */}
        <div>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-[15px] font-semibold text-industrial-100">
              Needs Attention
            </h2>
            <Link
              href="/priority"
              className="text-[13px] text-industrial-600 hover:text-industrial-300 transition-colors flex items-center gap-1"
            >
              View all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {priorityQueue.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-industrial-850">
                    <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-industrial-600 pr-4">Priority</th>
                    <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-industrial-600 pr-4">Report</th>
                    <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-industrial-600 pr-4">Site</th>
                    <th className="pb-3 text-[11px] font-medium uppercase tracking-wider text-industrial-600">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {priorityQueue.slice(0, 5).map((r) => (
                    <tr key={r.report_id} className="border-b border-industrial-900 last:border-b-0 hover:bg-industrial-900/50 transition-colors">
                      <td className="py-3 pr-4">
                        <PriorityBadge level={r.priority_level} />
                      </td>
                      <td className="py-3 pr-4">
                        <Link
                          href={`/reports/${r.report_id}`}
                          className="text-[13px] font-medium text-industrial-200 hover:text-industrial-100 transition-colors"
                        >
                          {r.report_id}
                        </Link>
                        <p className="text-[12px] text-industrial-500 mt-0.5 truncate max-w-[280px]">
                          {r.fixed_short_description || r.narrative?.slice(0, 60)}
                        </p>
                      </td>
                      <td className="py-3 pr-4 text-[13px] text-industrial-400">
                        {r.site || '—'}
                      </td>
                      <td className="py-3">
                        <Link
                          href={`/reports/${r.report_id}`}
                          className="text-[12px] font-medium text-blue-500 hover:text-blue-400 transition-colors"
                        >
                          Review
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              title="No reports requiring attention"
              description="Upload and analyze safety reports to populate the priority queue."
            />
          )}
        </div>

        {/* ── Recent Activity ──────────────────────────────────────── */}
        <div>
          <h2 className="text-[15px] font-semibold text-industrial-100 mb-5">
            Recent Activity
          </h2>

          {alerts.length > 0 ? (
            <div className="space-y-3">
              {alerts.slice(0, 4).map((a) => (
                <div key={a.id} className="flex items-start gap-3 py-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-industrial-800 mt-2 shrink-0" />
                  <div>
                    <p className="text-[13px] text-industrial-300">
                      {a.cluster_name && (
                        <span className="font-medium text-industrial-200">{a.cluster_name}</span>
                      )}
                      {a.cluster_name && ' — '}
                      {a.reason}
                    </p>
                    <p className="text-[11px] text-industrial-600 mt-0.5">
                      {a.location && `${a.location} · `}{a.created_at}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[13px] text-industrial-600">
              No recent activity recorded.
            </p>
          )}
        </div>

      </div>
    </AppShell>
  );
}

export default function OverviewPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-[13px] text-industrial-600">Loading…</div>}>
      <DashboardContent />
    </Suspense>
  );
}
