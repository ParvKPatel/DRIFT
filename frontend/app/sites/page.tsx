'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { EmptyState } from '@/components/ui/EmptyState';
import { SiteSummary } from '@/types';
import { RefreshCw, MapPin, AlertCircle } from 'lucide-react';
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
    return b.report_count - a.report_count;
  });

  const maxReports = Math.max(...sites.map(s => s.report_count), 1);
  const maxSif = Math.max(...sites.map(s => s.sif_count), 1);
  const maxCritical = Math.max(...sites.map(s => s.critical_count + s.high_priority_count), 1);

  return (
    <AppShell title="Sites & Activities">
      <div className="space-y-8 max-w-4xl mx-auto pb-12">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-industrial-850 pb-6">
          <div>
            <h1 className="text-2xl font-semibold text-industrial-100">Sites & Activities</h1>
            <p className="text-[13px] text-industrial-500 mt-1">Compare safety performance and risk across operational sites.</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchSites}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-industrial-800 hover:bg-industrial-700 text-industrial-200 text-[12px] font-medium transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-industrial-900 border border-industrial-800 rounded px-2.5 py-1.5 text-[12px] font-medium text-industrial-300 focus:outline-none focus:border-blue-500"
            >
              <option value="sif">Sort by SIF Count</option>
              <option value="critical">Sort by Priority</option>
              <option value="reports">Sort by Total Reports</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-[12px] text-industrial-500 flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
            Loading site rankings...
          </div>
        ) : sortedSites.length === 0 ? (
          <EmptyState
            title="No Site Records Found"
            description="Ingest operational reports to populate site rankings."
          />
        ) : (
          <div className="space-y-4">
            {sortedSites.map((s, idx) => {
              const pTotal = (s.report_count / maxReports) * 100;
              const pSif = (s.sif_count / maxSif) * 100;
              const critHigh = s.critical_count + s.high_priority_count;
              const pCrit = (critHigh / maxCritical) * 100;

              return (
                <div key={s.site} className="p-5 bg-industrial-950 border border-industrial-850 rounded flex flex-col md:flex-row md:items-center gap-6">
                  
                  {/* Site Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[12px] font-mono text-industrial-500">#{idx + 1}</span>
                      <h3 className="text-[15px] font-semibold text-industrial-200 flex items-center gap-1.5">
                        <MapPin className="w-4 h-4 text-blue-500" /> {s.site}
                      </h3>
                    </div>
                    <div className="text-[12px] text-industrial-500 flex items-center gap-3">
                      <span>{s.cluster_count} Clusters</span>
                      {s.escalating_cluster_count > 0 && (
                        <span className="text-amber-500 flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" /> {s.escalating_cluster_count} Escalating
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Visual Bars */}
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-16 text-[10px] uppercase text-industrial-500 text-right">Reports</div>
                      <div className="flex-1 h-2 bg-industrial-900 rounded-full overflow-hidden">
                        <div className="h-full bg-industrial-600 rounded-full" style={{ width: `${pTotal}%` }} />
                      </div>
                      <div className="w-6 text-[11px] font-medium text-industrial-300">{s.report_count}</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-16 text-[10px] uppercase text-industrial-500 text-right">Priority</div>
                      <div className="flex-1 h-2 bg-industrial-900 rounded-full overflow-hidden">
                        <div className="h-full bg-amber-500 rounded-full" style={{ width: `${pCrit}%` }} />
                      </div>
                      <div className="w-6 text-[11px] font-medium text-amber-500">{critHigh}</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-16 text-[10px] uppercase text-industrial-500 text-right">SIF</div>
                      <div className="flex-1 h-2 bg-industrial-900 rounded-full overflow-hidden">
                        <div className="h-full bg-red-500 rounded-full" style={{ width: `${pSif}%` }} />
                      </div>
                      <div className="w-6 text-[11px] font-medium text-red-500">{s.sif_count}</div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="md:w-24 text-right">
                    <Link
                      href={`/reports?site=${encodeURIComponent(s.site)}`}
                      className="text-[12px] font-medium text-blue-500 hover:text-blue-400 transition-colors"
                    >
                      View Reports
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
