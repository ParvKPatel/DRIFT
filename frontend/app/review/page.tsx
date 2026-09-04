'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { EmptyState } from '@/components/ui/EmptyState';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ReviewQueueItem, ReviewAnalyticsSummary } from '@/types';
import { RefreshCw, Filter, ArrowRight, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import Link from 'next/link';

export default function ReviewPage() {
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [analytics, setAnalytics] = useState<ReviewAnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('UNREVIEWED');

  const fetchQueueAndAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const q = new URLSearchParams();
      if (statusFilter && statusFilter !== 'ALL') q.set('status', statusFilter);

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
  }, [statusFilter]);

  useEffect(() => {
    fetchQueueAndAnalytics();
  }, [fetchQueueAndAnalytics]);

  return (
    <AppShell title="Needs Review">
      <div className="space-y-8 max-w-5xl mx-auto pb-12">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-industrial-850 pb-6">
          <div>
            <h1 className="text-2xl font-semibold text-industrial-100">Reports Requiring Your Review</h1>
            <p className="text-[13px] text-industrial-500 mt-1">Verify AI findings and provide human oversight.</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-[12px] font-medium text-industrial-400">
              <span className="flex items-center gap-1"><Clock className="w-4 h-4 text-amber-500" /> {analytics?.pending_review || 0} Pending</span>
              <span className="px-2 text-industrial-700">|</span>
              <span className="flex items-center gap-1"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> {analytics?.total_reviewed || 0} Reviewed</span>
            </div>
          </div>
        </div>

        <div className="flex justify-between items-center bg-industrial-950 p-4 rounded border border-industrial-850">
          <div className="flex items-center gap-2 text-[12px] font-medium text-industrial-400">
            <Filter className="w-4 h-4" /> Filter By Status
          </div>
          <div className="flex gap-2">
            {[
              { id: 'UNREVIEWED', label: 'Pending Review' },
              { id: 'NEEDS_MORE_INFORMATION', label: 'Needs Info' },
              { id: 'REVIEWED', label: 'Completed' },
              { id: 'ALL', label: 'All Reports' }
            ].map((opt) => (
              <button
                key={opt.id}
                onClick={() => setStatusFilter(opt.id)}
                className={`px-3 py-1.5 rounded text-[12px] font-medium transition-colors ${
                  statusFilter === opt.id
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500'
                    : 'bg-industrial-900 text-industrial-400 border border-industrial-800 hover:text-industrial-300'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-[12px] text-industrial-500 flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-500" /> Loading queue...
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            title="All Caught Up"
            description="There are no reports requiring your review at this time."
          />
        ) : (
          <div className="space-y-3">
            {items.map((item) => {
              const isReviewed = item.review_status === 'REVIEWED';
              const needsInfo = item.review_status === 'NEEDS_MORE_INFORMATION';
              
              return (
                <div key={item.report_id} className="p-5 bg-industrial-950 border border-industrial-850 rounded flex flex-col md:flex-row gap-6 hover:bg-industrial-900/40 transition-colors">
                  <div className="md:w-1/4 space-y-2">
                    <Link href={`/reports/${item.report_id}#review`} className="text-[14px] font-semibold text-industrial-200 hover:text-blue-400 transition-colors">
                      {item.report_id}
                    </Link>
                    <div className="text-[11px] text-industrial-500">{item.report_date || 'Unknown Date'} • {item.site || 'Unknown Site'}</div>
                    <div className="pt-2">
                      {isReviewed ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-500 uppercase">
                          <CheckCircle2 className="w-3 h-3" /> Reviewed
                        </span>
                      ) : needsInfo ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-500 uppercase">
                          <AlertCircle className="w-3 h-3" /> Needs Info
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-industrial-400 uppercase">
                          <Clock className="w-3 h-3" /> Pending Review
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="md:w-2/4">
                    <div className="text-[10px] uppercase tracking-wider text-industrial-600 mb-1">AI Findings</div>
                    <div className="flex items-center gap-2 mb-3">
                      <PriorityBadge level={item.ai_priority_level} />
                      <StatusBadge status={item.ai_sif_potential} />
                    </div>
                    <div className="text-[13px] text-industrial-300 leading-relaxed line-clamp-2">
                      &quot;{item.narrative_snippet}&quot;
                    </div>
                  </div>
                  
                  <div className="md:w-1/4 flex flex-col justify-center items-end">
                    <Link
                      href={`/reports/${item.report_id}#review`}
                      className={`inline-flex items-center gap-1.5 px-4 py-2 rounded text-[12px] font-medium transition-colors ${
                        isReviewed
                          ? 'bg-industrial-800 text-industrial-300 hover:bg-industrial-700'
                          : 'bg-blue-600 text-white hover:bg-blue-500'
                      }`}
                    >
                      {isReviewed ? 'View Details' : 'Review Report'} <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}
