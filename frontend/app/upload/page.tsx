'use client';

import React from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { FileUpload } from '@/components/ui/FileUpload';
import { ShieldCheck, FileSpreadsheet, CheckCircle, Info } from 'lucide-react';

export default function UploadPage() {
  return (
    <AppShell title="Safety Dataset Upload & Schema Validation">
      <div className="max-w-4xl mx-auto space-y-6">
        <SectionCard
          title="Upload Safety Report Dataset"
          subtitle="Ingest CSV files containing raw unsafe acts, conditions, near-misses, or incident reports."
        >
          <FileUpload />
        </SectionCard>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <SectionCard
            title="Expected Source Schema"
            subtitle="Required and canonical fields supported by the system"
          >
            <div className="space-y-2 text-xs font-mono text-industrial-300">
              <div className="flex items-center justify-between p-2 bg-industrial-950 rounded border border-industrial-800">
                <span className="text-industrial-100">report_id</span>
                <span className="text-emerald-400">Required (Primary Key)</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-industrial-950 rounded border border-industrial-800">
                <span className="text-industrial-100">narrative</span>
                <span className="text-emerald-400">Required (Report Text)</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-industrial-950 rounded border border-industrial-800">
                <span className="text-industrial-100">site / unit / shift</span>
                <span className="text-blue-400">Nullable (Location context)</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-industrial-950 rounded border border-industrial-800">
                <span className="text-industrial-100">incident_type / cause</span>
                <span className="text-blue-400">Nullable (Source Category)</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-industrial-950 rounded border border-industrial-800">
                <span className="text-industrial-100">corrective_action / outcome</span>
                <span className="text-blue-400">Nullable (Actions taken)</span>
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Ingestion Principles"
            subtitle="Data preservation and evidence-backed extraction rules"
          >
            <div className="space-y-3 text-xs font-sans text-industrial-300">
              <div className="flex items-start gap-2.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  <strong className="text-industrial-100 font-mono">Principle 2: Preserve Source Data.</strong> Original fields are never overwritten by AI inferences.
                </span>
              </div>
              <div className="flex items-start gap-2.5">
                <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                <span>
                  <strong className="text-industrial-100 font-mono">Principle 1: Evidence First.</strong> Facts not explicitly or implicitly stated in narrative default to UNKNOWN.
                </span>
              </div>
              <div className="flex items-start gap-2.5">
                <FileSpreadsheet className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                <span>
                  <strong className="text-industrial-100 font-mono">Large File Handling.</strong> Datasets up to 50MB (approx. 10,000 reports) supported per upload session.
                </span>
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </AppShell>
  );
}
