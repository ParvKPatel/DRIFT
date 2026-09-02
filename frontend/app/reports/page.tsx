'use client';

import React, { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { DataTable, Column } from '@/components/ui/DataTable';
import { SourceReport } from '@/types';
import { FileText, Search, Upload, RefreshCw, Database } from 'lucide-react';
import Link from 'next/link';

export default function ReportsPage() {
  const [reports, setReports] = useState<SourceReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [totalCount, setTotalCount] = useState(0);

  const fetchReports = async (search: string = '') => {
    setLoading(true);
    try {
      const url = search 
        ? `/api/v1/reports?search=${encodeURIComponent(search)}`
        : '/api/v1/reports?size=50';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setReports(data.items || []);
        setTotalCount(data.total || 0);
      }
    } catch (err) {
      console.error('Failed to fetch reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const res = await fetch('/api/v1/reports/seed', { method: 'POST' });
      if (res.ok) {
        await fetchReports();
      }
    } catch (err) {
      console.error('Failed to seed synthetic demo data:', err);
    } finally {
      setSeeding(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchReports(searchTerm);
  };

  const columns: Column<SourceReport>[] = [
    {
      header: 'Report ID',
      accessor: (r) => (
        <Link href={`/reports/${r.report_id}`} className="font-mono font-semibold text-blue-400 hover:underline">
          {r.report_id}
        </Link>
      ),
    },
    {
      header: 'Date',
      accessor: (r) => r.report_date ? String(r.report_date) : '—',
    },
    { header: 'Site', accessor: (r) => r.site || '—' },
    { header: 'Functional Location', accessor: (r) => r.functional_location || '—' },
    { header: 'Incident Type', accessor: (r) => r.incident_type || '—' },
    {
      header: 'Incident Cause (Source)',
      accessor: (r) => (
        <span className="font-mono text-emerald-300">
          {r.incident_cause || '—'}
        </span>
      ),
    },
    {
      header: 'Short Description',
      accessor: (r) => (
        <span className="truncate max-w-xs block text-industrial-300">
          {r.fixed_short_description || r.narrative}
        </span>
      ),
    },
    {
      header: 'Provenance',
      accessor: (r) => (
        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
          r.provenance === 'SYNTHETIC' 
            ? 'bg-purple-950/80 text-purple-300 border border-purple-800' 
            : 'bg-blue-950/80 text-blue-300 border border-blue-800'
        }`}>
          {r.provenance || 'OIL_EXPORT'}
        </span>
      ),
    },
    {
      header: 'AI Analysis',
      accessor: (r) => (
        <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-semibold uppercase ${
          r.analysis_status === 'COMPLETED'
            ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
            : r.analysis_status === 'PROCESSING'
              ? 'bg-blue-950/80 text-blue-300 border border-blue-800'
              : 'bg-industrial-900 text-industrial-500 border border-industrial-800'
        }`}>
          {r.analysis_status || 'NOT_ANALYZED'}
        </span>
      ),
    },
    {
      header: 'SIF/FPI Potential',
      accessor: (r) => {
        const val = r.sif_fpi_potential;
        if (val === 'YES') {
          return (
            <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase bg-red-950/90 text-red-300 border border-red-700">
              HIGH / YES
            </span>
          );
        }
        if (val === 'UNCERTAIN') {
          return (
            <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase bg-amber-950/90 text-amber-300 border border-amber-700">
              UNCERTAIN
            </span>
          );
        }
        if (val === 'NO') {
          return (
            <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase bg-emerald-950/90 text-emerald-300 border border-emerald-800">
              NO
            </span>
          );
        }
        return (
          <span className="px-2 py-0.5 rounded text-[9px] font-mono font-semibold uppercase text-industrial-500 bg-industrial-900 border border-industrial-800">
            UNSCREENED
          </span>
        );
      },
    },
    {
      header: 'Life-Saving Rule',
      accessor: (r) => (
        <span className="font-mono text-purple-300 text-xs">
          {r.primary_life_saving_rule || '—'}
        </span>
      ),
    },
    {
      header: 'HSE Priority',
      accessor: (r) => {
        const lvl = r.priority_level;
        const score = r.priority_score;
        if (!lvl) return <span className="text-industrial-500 text-[10px] font-mono">—</span>;

        const map: Record<string, string> = {
          CRITICAL: 'bg-red-950/90 text-red-300 border-red-700 font-bold',
          HIGH_PRIORITY_SIF_FPI_PRECURSOR: 'bg-orange-950/90 text-orange-300 border-orange-700 font-bold',
          SAFETY_REVIEW: 'bg-amber-950/90 text-amber-300 border-amber-700 font-semibold',
          ROUTINE: 'bg-emerald-950/90 text-emerald-300 border-emerald-800',
          UNCERTAIN: 'bg-industrial-900 text-industrial-400 border-industrial-700',
        };
        const cls = map[lvl] || map.UNCERTAIN;
        return (
          <span className={`px-2 py-0.5 rounded text-[9px] font-mono uppercase border ${cls}`}>
            {score !== undefined && score !== null ? `[${score}] ` : ''}{lvl.replace('_PRECURSOR', '')}
          </span>
        );
      },
    },
  ];

  return (
    <AppShell title="Safety Reports Register">
      <SectionCard
        title="Raw Safety Reports Database"
        subtitle={`Immutable raw incident reports, unsafe acts, conditions, and near-misses (${totalCount} records total).`}
        action={
          <div className="flex items-center gap-2">
            <button
              onClick={handleSeed}
              disabled={seeding}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-industrial-800 hover:bg-industrial-700 text-industrial-200 border border-industrial-600 font-mono text-xs font-semibold uppercase tracking-wider transition-colors disabled:opacity-50"
            >
              {seeding ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Database className="w-3.5 h-3.5 text-purple-400" />}
              Seed Demo Data
            </button>
            <Link
              href="/upload"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-semibold uppercase tracking-wider transition-colors"
            >
              <Upload className="w-3.5 h-3.5" />
              Upload CSV
            </Link>
          </div>
        }
      >
        <div className="space-y-4">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 max-w-md">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-industrial-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search narrative, report ID, or cause..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-industrial-950 border border-industrial-700 rounded pl-9 pr-3 py-1.5 text-xs text-industrial-100 placeholder-industrial-500 focus:outline-none focus:border-blue-500 font-sans"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 bg-industrial-800 hover:bg-industrial-700 text-industrial-200 border border-industrial-600 rounded text-xs font-mono font-semibold"
            >
              Search
            </button>
          </form>

          {loading ? (
            <div className="p-8 text-center font-mono text-xs text-industrial-400 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              Loading database reports...
            </div>
          ) : reports.length === 0 ? (
            <EmptyState
              title="No Reports Ingested"
              description="No safety reports matching criteria exist in the database. Seed synthetic data or upload a CSV."
              action={
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleSeed}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-industrial-800 hover:bg-industrial-700 text-industrial-200 border border-industrial-600 font-mono text-xs font-semibold uppercase tracking-wider transition-colors"
                  >
                    <Database className="w-3.5 h-3.5 text-purple-400" />
                    Seed Synthetic Demo Data
                  </button>
                  <Link
                    href="/upload"
                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-semibold uppercase tracking-wider transition-colors"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    Upload Dataset
                  </Link>
                </div>
              }
            />
          ) : (
            <DataTable columns={columns} data={reports} />
          )}
        </div>
      </SectionCard>
    </AppShell>
  );
}
