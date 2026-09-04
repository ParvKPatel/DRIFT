'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { EmptyState } from '@/components/ui/EmptyState';
import { ClusterResponse } from '@/types';
import { RefreshCw, Sparkles, TrendingUp, AlertCircle, ArrowRight } from 'lucide-react';
import Link from 'next/link';

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

  return (
    <AppShell title="Common Concerns">
      <div className="space-y-8 max-w-5xl mx-auto pb-12">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-industrial-850 pb-6">
          <div>
            <h1 className="text-2xl font-semibold text-industrial-100">Most Common Safety Concerns</h1>
            <p className="text-[13px] text-industrial-500 mt-1">AI-detected patterns across multiple safety reports.</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={filterBand}
              onChange={(e) => setFilterBand(e.target.value)}
              className="bg-industrial-900 border border-industrial-800 rounded px-2.5 py-1.5 text-[12px] font-medium text-industrial-300 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Concerns</option>
              <option value="CRITICAL">Critical Patterns</option>
              <option value="HIGH">High Patterns</option>
              <option value="REVIEW">Needs Review</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-[12px] text-industrial-500 flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
            Analyzing common concerns...
          </div>
        ) : filteredClusters.length === 0 ? (
          <EmptyState
            title="No Common Concerns Found"
            description="No safety patterns match the selected criteria."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredClusters.map((c) => {
              const isCritical = c.escalation_band === 'CRITICAL_PATTERN' || c.escalation_band === 'HIGH';
              return (
                <div key={c.id} className="flex flex-col p-5 bg-industrial-950 border border-industrial-850 rounded hover:border-industrial-700 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-[14px] font-semibold text-industrial-200 flex-1 pr-3">
                      {c.cluster_name}
                    </h3>
                    <div className="flex items-center gap-1 bg-industrial-900 px-2 py-1 rounded">
                      <TrendingUp className={`w-3.5 h-3.5 ${isCritical ? 'text-red-500' : 'text-industrial-400'}`} />
                      <span className="text-[12px] font-semibold text-industrial-200">{c.recurrence_count}</span>
                    </div>
                  </div>
                  
                  <p className="text-[12px] text-industrial-500 mb-4 line-clamp-2">
                    {c.common_mechanism || 'General recurring pattern identified.'}
                  </p>
                  
                  <div className="mt-auto space-y-2 mb-4">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-industrial-600 uppercase">Common Asset</span>
                      <span className="text-industrial-300 font-medium">{c.common_asset || 'Various'}</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-industrial-600 uppercase">Life-Saving Rule</span>
                      <span className="text-purple-400 font-medium">{c.common_lsr || 'None'}</span>
                    </div>
                  </div>
                  
                  <div className="pt-3 border-t border-industrial-900 flex justify-between items-center">
                    {isCritical ? (
                      <div className="flex items-center gap-1.5 text-red-500 text-[11px] font-medium uppercase">
                        <AlertCircle className="w-3.5 h-3.5" /> High Risk Pattern
                      </div>
                    ) : (
                      <div className="text-[11px] text-industrial-500 uppercase">Monitoring</div>
                    )}
                    
                    <Link
                      href={`/clusters/${c.id}`}
                      className="flex items-center gap-1 text-[12px] font-medium text-blue-500 hover:text-blue-400 transition-colors"
                    >
                      View Reports <ArrowRight className="w-3 h-3" />
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
