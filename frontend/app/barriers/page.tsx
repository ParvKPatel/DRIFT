'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { EmptyState } from '@/components/ui/EmptyState';
import { BarrierSummary } from '@/types';
import { Shield, RefreshCw, AlertTriangle, CheckCircle2, XCircle, AlertCircle, ArrowDownCircle } from 'lucide-react';

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

  return (
    <AppShell title="Controls Attention">
      <div className="space-y-8 max-w-5xl mx-auto pb-12">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-industrial-850 pb-6">
          <div>
            <h1 className="text-2xl font-semibold text-industrial-100">Controls Requiring Attention</h1>
            <p className="text-[13px] text-industrial-500 mt-1">Physical and procedural barriers with highest failure or degradation rates.</p>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-[12px] text-industrial-500 flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
            Analyzing barrier health...
          </div>
        ) : barriers.length === 0 ? (
          <EmptyState
            title="No Control Data Found"
            description="Extract AI safety facts to track physical & procedural control conditions."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {barriers.map((b) => {
              const totalIssues = b.failed_count + b.absent_count + b.degraded_count;
              const isCritical = b.weakness_score > 50 || totalIssues > 2;

              return (
                <div key={b.barrier} className="flex flex-col p-5 bg-industrial-950 border border-industrial-850 rounded hover:border-industrial-700 transition-colors">
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-[14px] font-semibold text-industrial-200 flex-1 pr-3 flex items-center gap-2">
                      <Shield className={`w-4 h-4 ${isCritical ? 'text-red-500' : 'text-industrial-500'}`} />
                      {b.barrier}
                    </h3>
                    <div className="flex flex-col items-end">
                      <span className="text-[10px] text-industrial-600 uppercase mb-0.5">Weakness</span>
                      <span className={`text-[14px] font-bold ${isCritical ? 'text-red-500' : 'text-amber-500'}`}>
                        {b.weakness_score}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="p-2.5 bg-industrial-900/50 rounded flex justify-between items-center border border-red-900/20">
                      <span className="text-[11px] uppercase text-industrial-500 flex items-center gap-1">
                        <XCircle className="w-3 h-3 text-red-500" /> Failed
                      </span>
                      <span className="text-[12px] font-semibold text-industrial-200">{b.failed_count}</span>
                    </div>
                    <div className="p-2.5 bg-industrial-900/50 rounded flex justify-between items-center border border-amber-900/20">
                      <span className="text-[11px] uppercase text-industrial-500 flex items-center gap-1">
                        <ArrowDownCircle className="w-3 h-3 text-amber-500" /> Degraded
                      </span>
                      <span className="text-[12px] font-semibold text-industrial-200">{b.degraded_count}</span>
                    </div>
                    <div className="p-2.5 bg-industrial-900/50 rounded flex justify-between items-center border border-purple-900/20">
                      <span className="text-[11px] uppercase text-industrial-500 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3 text-purple-500" /> Absent
                      </span>
                      <span className="text-[12px] font-semibold text-industrial-200">{b.absent_count}</span>
                    </div>
                    <div className="p-2.5 bg-industrial-900/50 rounded flex justify-between items-center border border-emerald-900/20">
                      <span className="text-[11px] uppercase text-industrial-500 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-emerald-500" /> Intact
                      </span>
                      <span className="text-[12px] font-semibold text-industrial-200">{b.intact_count}</span>
                    </div>
                  </div>

                  <div className="mt-auto pt-3 border-t border-industrial-900 flex justify-between items-center">
                    <div className="text-[11px] text-industrial-500">
                      {b.total_mentions} Total Mentions
                    </div>
                    {b.sif_count > 0 && (
                      <div className="flex items-center gap-1.5 px-2 py-1 bg-red-950/40 rounded text-red-500 text-[10px] font-medium uppercase">
                        <AlertTriangle className="w-3 h-3" /> {b.sif_count} SIF Precursors
                      </div>
                    )}
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
