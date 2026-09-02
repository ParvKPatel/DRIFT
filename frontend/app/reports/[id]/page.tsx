'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import {
  SourceReport,
  SafetyAnalysisResult,
  SifScreeningResult,
  LsrMappingResult,
  PriorityResult,
  SimilarReportResponse,
  ReviewResponse,
  ReviewHistoryItem,
  ReviewDecision,
  EvidenceStatus,
  EvidenceItem,
  SifDecision,
  PriorityLevel,
  LifeSavingRule,
} from '@/types';
import {
  ArrowLeft, Sparkles, RefreshCw, AlertCircle, CheckCircle2,
  XCircle, HelpCircle, Activity, Wrench, Zap, Shield,
  MapPin, User, AlertTriangle, ShieldAlert, BookOpen, Flame, Network,
  UserCheck, Save, History, Check, ThumbsUp, AlertOctagon,
} from 'lucide-react';
import Link from 'next/link';

// ── Evidence Status badge ────────────────────────────────────────────────────
const EvidenceBadge = ({ status }: { status?: EvidenceStatus }) => {
  const map: Record<EvidenceStatus, { label: string; classes: string }> = {
    EXPLICIT:  { label: 'EXPLICIT',  classes: 'bg-emerald-950/80 text-emerald-300 border-emerald-700' },
    INFERRED:  { label: 'INFERRED',  classes: 'bg-amber-950/80 text-amber-300 border-amber-700' },
    UNKNOWN:   { label: 'UNKNOWN',   classes: 'bg-industrial-900 text-industrial-500 border-industrial-700' },
  };
  const cfg = status ? map[status] : map.UNKNOWN;
  return (
    <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase border tracking-wide ${cfg.classes}`}>
      {cfg.label}
    </span>
  );
};

// ── Confidence bar ───────────────────────────────────────────────────────────
const ConfidenceBar = ({ value }: { value?: number }) => {
  if (value === undefined || value === null) return null;
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-industrial-600';
  return (
    <div className="flex items-center gap-1.5 mt-1">
      <div className="flex-1 h-1 bg-industrial-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[9px] font-mono text-industrial-500">{pct}%</span>
    </div>
  );
};

// ── Analysis Status badge ────────────────────────────────────────────────────
const AnalysisStatusBadge = ({ status }: { status?: string }) => {
  const map: Record<string, { label: string; classes: string; Icon: React.FC<any> }> = {
    COMPLETED:    { label: 'AI ANALYSIS COMPLETE', classes: 'bg-emerald-950/80 text-emerald-300 border-emerald-700', Icon: CheckCircle2 },
    PROCESSING:   { label: 'PROCESSING…',          classes: 'bg-blue-950/80 text-blue-300 border-blue-700',         Icon: RefreshCw },
    FAILED:       { label: 'ANALYSIS FAILED',      classes: 'bg-red-950/80 text-red-400 border-red-700',            Icon: XCircle },
    NEEDS_REVIEW: { label: 'NEEDS REVIEW',         classes: 'bg-amber-950/80 text-amber-300 border-amber-700',      Icon: AlertCircle },
    NOT_ANALYZED: { label: 'NOT ANALYZED',         classes: 'bg-industrial-900 text-industrial-500 border-industrial-700', Icon: HelpCircle },
  };
  const cfg = status ? (map[status] ?? map.NOT_ANALYZED) : map.NOT_ANALYZED;
  const { Icon } = cfg;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[9px] font-mono font-bold uppercase tracking-wider ${cfg.classes}`}>
      <Icon className="w-2.5 h-2.5" />
      {cfg.label}
    </span>
  );
};

// ── SIF Decision Badge ──────────────────────────────────────────────────────
const SifDecisionBadge = ({ decision }: { decision?: SifDecision }) => {
  if (decision === 'YES') {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-red-950/90 text-red-300 border border-red-700 font-mono font-bold text-xs uppercase tracking-wider">
        <ShieldAlert className="w-4 h-4 text-red-400" />
        HIGH / YES — SIF/FPI PRECURSOR DETECTED
      </span>
    );
  }
  if (decision === 'UNCERTAIN') {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-amber-950/90 text-amber-300 border border-amber-700 font-mono font-bold text-xs uppercase tracking-wider">
        <AlertCircle className="w-4 h-4 text-amber-400" />
        UNCERTAIN — HUMAN SAFETY REVIEW REQUIRED
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-emerald-950/90 text-emerald-300 border border-emerald-700 font-mono font-bold text-xs uppercase tracking-wider">
      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
      NO — NO CREDIBLE SIF PRECURSOR DETECTED
    </span>
  );
};

// ── Priority Level Badge ────────────────────────────────────────────────────
const PriorityLevelBadge = ({ level }: { level?: PriorityLevel }) => {
  const map: Record<PriorityLevel, { label: string; classes: string }> = {
    CRITICAL:                        { label: 'CRITICAL PRIORITY', classes: 'bg-red-950/90 text-red-300 border-red-700 animate-pulse' },
    HIGH_PRIORITY_SIF_FPI_PRECURSOR: { label: 'HIGH PRIORITY SIF PRECURSOR', classes: 'bg-orange-950/90 text-orange-300 border-orange-700' },
    SAFETY_REVIEW:                   { label: 'SAFETY REVIEW REQUIRED', classes: 'bg-amber-950/90 text-amber-300 border-amber-700' },
    ROUTINE:                         { label: 'ROUTINE MONITORING', classes: 'bg-emerald-950/90 text-emerald-300 border-emerald-700' },
    UNCERTAIN:                       { label: 'UNCERTAIN — REVIEW NEEDED', classes: 'bg-industrial-900 text-industrial-400 border-industrial-700' },
  };
  const cfg = level ? map[level] : map.UNCERTAIN;
  return (
    <span className={`px-2.5 py-1 rounded text-xs font-mono font-bold uppercase border tracking-wider ${cfg.classes}`}>
      {cfg.label}
    </span>
  );
};

// ── Single safety fact card ──────────────────────────────────────────────────
interface FactCardProps {
  label: string;
  icon: React.ReactNode;
  value?: string | null;
  evidence?: string | null;
  evidenceStatus?: EvidenceStatus;
  confidence?: number;
  onEvidenceHover?: (evidence: string | null) => void;
}

const FactCard = ({ label, icon, value, evidence, evidenceStatus, confidence, onEvidenceHover }: FactCardProps) => {
  const isEmpty = !value;
  return (
    <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-1.5">
      <div className="flex items-center gap-1.5">
        <span className="text-industrial-500">{icon}</span>
        <span className="text-[9px] font-mono font-bold text-industrial-400 uppercase tracking-wider flex-1">{label}</span>
        <EvidenceBadge status={evidenceStatus} />
      </div>
      {isEmpty ? (
        <span className="block text-[10px] font-mono text-industrial-600 italic">
          UNKNOWN — No supporting evidence in narrative
        </span>
      ) : (
        <>
          <span className="block text-xs font-sans text-industrial-100 leading-snug">{value}</span>
          <ConfidenceBar value={confidence} />
          {evidence && (
            <button
              className="text-[9px] font-mono text-blue-400/70 hover:text-blue-300 transition-colors mt-0.5 truncate max-w-full text-left"
              onMouseEnter={() => onEvidenceHover?.(evidence)}
              onMouseLeave={() => onEvidenceHover?.(null)}
              title={`Evidence: "${evidence}"`}
            >
              ▸ &quot;{evidence}&quot;
            </button>
          )}
        </>
      )}
    </div>
  );
};

// ── Narrative with evidence highlighting ─────────────────────────────────────
const NarrativeWithHighlights = ({
  narrative,
  evidenceItems,
  hoveredEvidence,
}: {
  narrative: string;
  evidenceItems: EvidenceItem[];
  hoveredEvidence: string | null;
}) => {
  if (!evidenceItems.length && !hoveredEvidence) {
    return (
      <p className="text-industrial-100 font-sans text-xs leading-relaxed whitespace-pre-wrap">
        {narrative}
      </p>
    );
  }

  const ranges: { start: number; end: number; field: string; status: EvidenceStatus }[] = [];
  evidenceItems.forEach((ev) => {
    if (ev.start_offset !== undefined && ev.end_offset !== undefined &&
        ev.start_offset !== null && ev.end_offset !== null) {
      ranges.push({ start: ev.start_offset, end: ev.end_offset, field: ev.field_name, status: ev.evidence_status });
    } else if (ev.evidence_text) {
      const idx = narrative.toLowerCase().indexOf(ev.evidence_text.toLowerCase());
      if (idx !== -1) {
        ranges.push({ start: idx, end: idx + ev.evidence_text.length, field: ev.field_name, status: ev.evidence_status });
      }
    }
  });

  if (hoveredEvidence) {
    const idx = narrative.toLowerCase().indexOf(hoveredEvidence.toLowerCase());
    if (idx !== -1) {
      ranges.push({ start: idx, end: idx + hoveredEvidence.length, field: 'hovered', status: 'EXPLICIT' });
    }
  }

  if (!ranges.length) {
    return (
      <p className="text-industrial-100 font-sans text-xs leading-relaxed whitespace-pre-wrap">
        {narrative}
      </p>
    );
  }

  ranges.sort((a, b) => a.start - b.start);
  const merged: typeof ranges = [];
  for (const r of ranges) {
    if (merged.length && r.start <= merged[merged.length - 1].end) {
      merged[merged.length - 1].end = Math.max(merged[merged.length - 1].end, r.end);
    } else {
      merged.push({ ...r });
    }
  }

  const parts: React.ReactNode[] = [];
  let cursor = 0;
  merged.forEach((range, i) => {
    if (range.start > cursor) {
      parts.push(<span key={`plain-${i}`}>{narrative.slice(cursor, range.start)}</span>);
    }
    const isHovered = hoveredEvidence &&
      narrative.slice(range.start, range.end).toLowerCase().includes(hoveredEvidence.toLowerCase());
    parts.push(
      <mark
        key={`highlight-${i}`}
        className={`rounded px-0.5 ${
          isHovered
            ? 'bg-blue-400/30 text-blue-100'
            : range.status === 'EXPLICIT'
              ? 'bg-emerald-900/60 text-emerald-200'
              : 'bg-amber-900/40 text-amber-200'
        }`}
        title={`Evidence for: ${range.field}`}
      >
        {narrative.slice(range.start, range.end)}
      </mark>
    );
    cursor = range.end;
  });
  if (cursor < narrative.length) {
    parts.push(<span key="tail">{narrative.slice(cursor)}</span>);
  }

  return (
    <p className="text-industrial-100 font-sans text-xs leading-relaxed whitespace-pre-wrap">
      {narrative}
    </p>
  );
};

// ══════════════════════════════════════════════════════════════════════════════
// Main Report Detail Page
// ══════════════════════════════════════════════════════════════════════════════

export default function ReportDetailPage() {
  const params = useParams();
  const reportId = (params?.id as string) || '';

  const [report, setReport] = useState<SourceReport | null>(null);
  const [analysis, setAnalysis] = useState<SafetyAnalysisResult | null>(null);
  const [sifResult, setSifResult] = useState<SifScreeningResult | null>(null);
  const [lsrResult, setLsrResult] = useState<LsrMappingResult | null>(null);
  const [priorityResult, setPriorityResult] = useState<PriorityResult | null>(null);
  const [similarResult, setSimilarResult] = useState<SimilarReportResponse | null>(null);
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [reviewHistory, setReviewHistory] = useState<ReviewHistoryItem[]>([]);

  // Review Form state
  const [selectedDecision, setSelectedDecision] = useState<ReviewDecision>('CONFIRM_AI');
  const [overrideSif, setOverrideSif] = useState<string>('');
  const [overrideLsr, setOverrideLsr] = useState<string>('');
  const [overridePriority, setOverridePriority] = useState<string>('');
  const [reviewerComment, setReviewerComment] = useState<string>('');
  const [rejectionReason, setRejectionReason] = useState<string>('FALSE_POSITIVE');
  const [missingFieldsInput, setMissingFieldsInput] = useState<string>('exposure_duration, barrier_condition');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewFeedback, setReviewFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const [loading, setLoading] = useState(true);
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [hoveredEvidence, setHoveredEvidence] = useState<string | null>(null);

  // Fetch report and all intelligence results
  const loadIntelligence = useCallback(async () => {
    if (!reportId) return;
    try {
      const repRes = await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}`);
      if (repRes.ok) setReport(await repRes.json());

      const anRes = await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/analysis`);
      if (anRes.ok) setAnalysis(await anRes.json());

      const sifRes = await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/sif-analysis`);
      if (sifRes.ok) setSifResult(await sifRes.json());

      const lsrRes = await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/lsr`);
      if (lsrRes.ok) setLsrResult(await lsrRes.json());

      const prioRes = await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/priority`);
      if (prioRes.ok) setPriorityResult(await prioRes.json());

      const simRes = await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/similar?top_k=4&min_threshold=0.5`);
      if (simRes.ok) setSimilarResult(await simRes.json());

      const revRes = await fetch(`/api/v1/reviews/${encodeURIComponent(reportId)}`);
      if (revRes.ok) {
        const revData = await revRes.json();
        setReview(revData);
        if (revData) {
          setOverrideSif(revData.final_sif_potential || '');
          setOverrideLsr(revData.final_lsr || '');
          setOverridePriority(revData.final_priority || '');
          setReviewerComment(revData.reviewer_comment || '');
        }
      }

      const histRes = await fetch(`/api/v1/reviews/${encodeURIComponent(reportId)}/history`);
      if (histRes.ok) setReviewHistory(await histRes.json());
    } catch (err: any) {
      console.error('Failed loading report intelligence:', err);
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    loadIntelligence();
  }, [loadIntelligence]);

  // Trigger full pipeline (Phase 3 -> Phase 4 -> Phase 5)
  const runFullPipeline = useCallback(async () => {
    setRunningPipeline(true);
    setPipelineError(null);
    try {
      const res = await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/intelligence`, {
        method: 'POST',
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Pipeline execution failed (HTTP ${res.status})`);
      }
      const data = await res.json();
      if (data.extraction) setAnalysis(data.extraction);
      if (data.sif_screening) setSifResult(data.sif_screening);
      if (data.lsr_mapping) setLsrResult(data.lsr_mapping);
      if (data.priority) setPriorityResult(data.priority);
      await loadIntelligence();
    } catch (err: any) {
      setPipelineError(err.message || 'Error running full intelligence pipeline.');
    } finally {
      setRunningPipeline(false);
    }
  }, [reportId, loadIntelligence]);

  // Submit human review decision
  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingReview(true);
    setReviewFeedback(null);
    try {
      const missingFields =
        selectedDecision === 'NEEDS_MORE_INFORMATION'
          ? missingFieldsInput.split(',').map((s) => s.trim()).filter(Boolean)
          : [];

      const body: any = {
        reviewer_id: 'HSE Safety Officer (Field Reviewer)',
        review_decision: selectedDecision,
        reviewer_comment: reviewerComment,
      };

      if (selectedDecision === 'OVERRIDE') {
        body.final_sif_potential = overrideSif || undefined;
        body.final_lsr = overrideLsr || undefined;
        body.final_priority = overridePriority || undefined;
      } else if (selectedDecision === 'REJECT') {
        body.rejection_reason = rejectionReason;
      } else if (selectedDecision === 'NEEDS_MORE_INFORMATION') {
        body.missing_information_fields = missingFields;
      }

      const res = await fetch(`/api/v1/reviews/${encodeURIComponent(reportId)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Review submission failed (HTTP ${res.status})`);
      }

      const updated = await res.json();
      setReview(updated);
      setReviewFeedback({
        type: 'success',
        message: `HSE Review decision (${selectedDecision}) successfully persisted with complete audit trail.`,
      });
      await loadIntelligence();
    } catch (err: any) {
      setReviewFeedback({ type: 'error', message: err.message || 'Failed to submit review.' });
    } finally {
      setSubmittingReview(false);
    }
  };

  const factDefs = analysis ? [
    { label: 'Activity',            icon: <Activity className="w-3 h-3" />,   field: 'activity' as const },
    { label: 'Equipment',           icon: <Wrench className="w-3 h-3" />,     field: 'equipment' as const },
    { label: 'Hazard',              icon: <AlertTriangle className="w-3 h-3" />, field: 'hazard' as const },
    { label: 'Energy Source',       icon: <Zap className="w-3 h-3" />,        field: 'energy_source' as const },
    { label: 'Exposure',            icon: <User className="w-3 h-3" />,        field: 'exposure' as const },
    { label: 'Exposure Location',   icon: <MapPin className="w-3 h-3" />,      field: 'exposure_location' as const },
    { label: 'Barrier',             icon: <Shield className="w-3 h-3" />,      field: 'barrier' as const },
    { label: 'Barrier Condition',   icon: <Shield className="w-3 h-3" />,      field: 'barrier_condition' as const },
    { label: 'Potential Consequence', icon: <AlertCircle className="w-3 h-3" />, field: 'potential_consequence' as const },
  ] : [];

  return (
    <AppShell title={`Report Intelligence: ${reportId}`}>
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Navigation & Header Status */}
        <div className="flex items-center justify-between">
          <Link
            href="/reports"
            className="inline-flex items-center gap-1.5 text-xs font-mono text-industrial-400 hover:text-industrial-200 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Reports Register
          </Link>

          <div className="flex items-center gap-2">
            <button
              id="run-pipeline-btn"
              onClick={runFullPipeline}
              disabled={runningPipeline}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-semibold uppercase tracking-wider transition-colors disabled:opacity-50"
            >
              {runningPipeline ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Run Full Intelligence Pipeline
            </button>
          </div>
        </div>

        {pipelineError && (
          <div className="p-3 bg-red-950/40 border border-red-800 text-red-300 rounded text-xs font-mono">
            ⚠ Pipeline Execution Error: {pipelineError}
          </div>
        )}

        {loading ? (
          <SectionCard title={`Loading Report ${reportId}`}>
            <div className="p-8 text-center text-xs font-mono text-industrial-400 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              Loading safety report and intelligence analytics...
            </div>
          </SectionCard>
        ) : !report ? (
          <SectionCard title="Report Not Found">
            <EmptyState
              title="Report Record Missing"
              description={`No report found matching canonical ID '${reportId}'.`}
            />
          </SectionCard>
        ) : (
          <div className="space-y-6">
            {/* ══════════════════════════════════════════════════════════════════ */}
            {/* 1. SIF/FPI SCREENING SECTION (PHASE 4)                           */}
            {/* ══════════════════════════════════════════════════════════════════ */}
            <SectionCard
              title="1. SIF / FPI Precursor Screening"
              subtitle="Phase 4 — Deterministic Safety Rules + Structured Facts (No fake fatality probability)"
            >
              {!sifResult ? (
                <div className="p-4 text-center text-xs font-mono text-industrial-500 italic">
                  SIF Screening not yet executed. Click &quot;Run Full Intelligence Pipeline&quot; above.
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="p-3 bg-industrial-950 rounded border border-industrial-800 flex flex-wrap items-center justify-between gap-3">
                    <SifDecisionBadge decision={sifResult.sif_fpi_potential} />
                    <span className="text-xs font-mono text-industrial-400">
                      Confidence: <strong className="text-industrial-200">{Math.round(sifResult.sif_confidence * 100)}%</strong>
                    </span>
                  </div>
                  <p className="text-xs font-sans text-industrial-200 leading-relaxed">
                    {sifResult.screening_reason}
                  </p>
                </div>
              )}
            </SectionCard>

            {/* ══════════════════════════════════════════════════════════════════ */}
            {/* 2. LIFE-SAVING RULE (LSR) MAPPING SECTION (PHASE 5)              */}
            {/* ══════════════════════════════════════════════════════════════════ */}
            <SectionCard
              title="2. Life-Saving Rule (LSR) Mapping"
              subtitle="Phase 5 — Evidence-Backed Mapping to 9 Official Project Rules (Preserves original incident cause)"
            >
              {!lsrResult ? (
                <div className="p-4 text-center text-xs font-mono text-industrial-500 italic">
                  LSR Mapping not yet executed. Click &quot;Run Full Intelligence Pipeline&quot; above.
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-4 bg-industrial-950 rounded border border-industrial-800 space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <BookOpen className="w-5 h-5 text-purple-400" />
                        <div>
                          <span className="text-[10px] font-mono text-industrial-500 uppercase block">Primary Life-Saving Rule</span>
                          <span className="text-sm font-mono font-bold text-purple-200">
                            {lsrResult.primary_life_saving_rule}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <EvidenceBadge status={lsrResult.lsr_evidence_status} />
                        <span className="text-xs font-mono text-industrial-400">
                          Mapping Confidence: <strong className="text-industrial-200">{Math.round(lsrResult.lsr_confidence * 100)}%</strong>
                        </span>
                      </div>
                    </div>

                    {lsrResult.secondary_life_saving_rules && lsrResult.secondary_life_saving_rules.length > 0 && (
                      <div className="pt-2 border-t border-industrial-800 flex items-center gap-2">
                        <span className="text-[10px] font-mono text-industrial-400 uppercase">Secondary Rules:</span>
                        {lsrResult.secondary_life_saving_rules.map((sec) => (
                          <span key={sec} className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-950/60 text-purple-300 border border-purple-800">
                            {sec}
                          </span>
                        ))}
                      </div>
                    )}

                    <p className="text-xs font-sans text-industrial-200 leading-relaxed">
                      {lsrResult.lsr_reason}
                    </p>

                    {lsrResult.lsr_evidence && (
                      <div className="p-2.5 bg-industrial-900/60 rounded border border-industrial-800 text-xs font-mono text-purple-300/90 italic">
                        Evidence Quote: &quot;{lsrResult.lsr_evidence}&quot;
                      </div>
                    )}

                    {report.incident_cause && (
                      <div className="text-[10px] font-mono text-industrial-500 pt-1 border-t border-industrial-800">
                        Source Incident Cause Preserved: <strong className="text-emerald-400">{report.incident_cause}</strong>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </SectionCard>

            {/* ══════════════════════════════════════════════════════════════════ */}
            {/* 3. HSE PRIORITY ENGINE SECTION (PHASE 5)                         */}
            {/* ══════════════════════════════════════════════════════════════════ */}
            <SectionCard
              title="3. HSE Triage Priority Engine"
              subtitle="Phase 5 — 0–100 Prioritisation Ranking Score for HSE Attention (Ranking metric, NOT death probability)"
            >
              {!priorityResult ? (
                <div className="p-4 text-center text-xs font-mono text-industrial-500 italic">
                  HSE Priority calculation not yet run. Click &quot;Run Full Intelligence Pipeline&quot; above.
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Top score & level row */}
                  <div className="p-4 bg-industrial-950 rounded border border-industrial-800 flex flex-wrap items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-industrial-900 border border-industrial-700 rounded text-center min-w-[90px]">
                        <span className="text-[9px] font-mono text-industrial-400 block uppercase">PRIORITY SCORE</span>
                        <span className="text-2xl font-mono font-bold text-industrial-100">{priorityResult.priority_score}</span>
                        <span className="text-[9px] font-mono text-industrial-500 block">/ 100</span>
                      </div>
                      <div>
                        <span className="text-[10px] font-mono text-industrial-400 uppercase block mb-1">Priority Level</span>
                        <PriorityLevelBadge level={priorityResult.priority_level} />
                      </div>
                    </div>

                    {priorityResult.priority_override && (
                      <div className="px-3 py-1.5 bg-red-950/80 border border-red-800 rounded text-xs font-mono text-red-300 flex items-center gap-1.5">
                        <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                        <span>CRITICAL SAFETY OVERRIDE ACTIVE</span>
                      </div>
                    )}
                  </div>

                  {/* Why Prioritized & Unavailable components split */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Why Prioritized */}
                    <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-2">
                      <span className="text-[10px] font-mono font-bold text-industrial-400 uppercase tracking-wider block">
                        Why Prioritized
                      </span>
                      {priorityResult.why_prioritized && priorityResult.why_prioritized.length > 0 ? (
                        <ul className="space-y-1 text-xs font-sans text-industrial-200">
                          {priorityResult.why_prioritized.map((reason, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <span className="text-emerald-400 font-mono font-bold">✓</span>
                              <span>{reason}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs font-mono text-industrial-500 italic">Standard routine monitoring score.</p>
                      )}
                    </div>

                    {/* Phase 6 Component Availability */}
                    <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-2">
                      <span className="text-[10px] font-mono font-bold text-industrial-400 uppercase tracking-wider block">
                        Phase 6 Component Status
                      </span>
                      <ul className="space-y-1 text-xs font-mono text-industrial-500">
                        {priorityResult.unavailable_components && priorityResult.unavailable_components.map((comp, idx) => (
                          <li key={idx} className="flex items-center gap-1.5">
                            <span className="w-2 h-2 rounded-full bg-industrial-700 inline-block" />
                            <span>{comp}: <strong className="text-industrial-600 uppercase">NOT YET AVAILABLE</strong></span>
                          </li>
                        ))}
                      </ul>
                      <p className="text-[10px] font-mono text-industrial-600 pt-1 border-t border-industrial-800">
                        (Recurrence, novelty, and anomaly scoring will populate in Phase 6)
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </SectionCard>

            {/* ══════════════════════════════════════════════════════════════════ */}
            {/* 4 & 5. SOURCE REPORT & SAFETY FACTS GRID                         */}
            {/* ══════════════════════════════════════════════════════════════════ */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* LEFT: Raw Source Report */}
              <SectionCard
                title="4. Original Source Safety Report"
                subtitle="Immutable source records — AI analysis never overwrites these"
              >
                <div className="space-y-3 text-xs font-mono">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-2.5 bg-industrial-950 rounded border border-industrial-800">
                      <span className="text-industrial-500 block text-[10px] uppercase">Report ID</span>
                      <span className="text-industrial-100 font-semibold">{report.report_id}</span>
                    </div>
                    <div className="p-2.5 bg-industrial-950 rounded border border-industrial-800">
                      <span className="text-industrial-500 block text-[10px] uppercase">Report Date</span>
                      <span className="text-industrial-100 font-semibold">{report.report_date ? String(report.report_date) : 'NULL'}</span>
                    </div>
                  </div>

                  <div className="p-2.5 bg-industrial-950 rounded border border-industrial-800">
                    <span className="text-industrial-500 block text-[10px] uppercase">Incident Cause (Source)</span>
                    <span className="text-emerald-400 font-semibold font-mono">{report.incident_cause || 'NULL'}</span>
                  </div>

                  <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-2">
                    <span className="text-industrial-400 text-[10px] uppercase font-mono block">
                      Verbatim Safety Event Narrative
                    </span>
                    <NarrativeWithHighlights
                      narrative={report.narrative}
                      evidenceItems={analysis?.evidence_items ?? []}
                      hoveredEvidence={hoveredEvidence}
                    />
                  </div>
                </div>
              </SectionCard>

              {/* RIGHT: AI Safety Fact Extraction */}
              <SectionCard
                title="5. AI Safety Fact Extraction"
                subtitle="Phase 3 — 9 Structured Safety Facts + Evidence Spans"
              >
                {!analysis ? (
                  <div className="p-6 text-center text-xs font-mono text-industrial-500 italic">
                    Safety facts not yet extracted. Click &quot;Run Full Intelligence Pipeline&quot; above.
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="grid grid-cols-1 gap-2">
                      {factDefs.map(({ label, icon, field }) => {
                        const value = analysis[field];
                        const evidence = analysis[`${field}_evidence` as keyof SafetyAnalysisResult] as string | undefined;
                        const evidenceStatus = analysis[`${field}_evidence_status` as keyof SafetyAnalysisResult] as EvidenceStatus | undefined;
                        const confidence = analysis[`${field}_confidence` as keyof SafetyAnalysisResult] as number | undefined;
                        return (
                          <FactCard
                            key={field}
                            label={label}
                            icon={icon}
                            value={value as string | null}
                            evidence={evidence}
                            evidenceStatus={evidenceStatus}
                            confidence={confidence}
                            onEvidenceHover={setHoveredEvidence}
                          />
                        );
                      })}
                    </div>
                  </div>
                )}
              </SectionCard>
            </div>

            {/* ══════════════════════════════════════════════════════════════════ */}
            {/* 6. SIMILAR REPORTS SECTION (PHASE 6 RELATIONSHIP INTELLIGENCE)  */}
            {/* ══════════════════════════════════════════════════════════════════ */}
            <SectionCard
              title="6. Related Reports & Shared Precursor Mechanisms"
              subtitle="Phase 6 — Vector embeddings & hybrid similarity matching (Meaning-based retrieval, NOT naive keyword match)"
            >
              {!similarResult || similarResult.similar_reports.length === 0 ? (
                <div className="p-6 text-center text-xs font-mono text-industrial-500 italic">
                  No sufficiently similar precursor reports detected in database yet.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {similarResult.similar_reports.map((sim) => (
                    <div key={sim.report_id} className="p-3.5 bg-industrial-950 rounded border border-industrial-800 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <Link href={`/reports/${sim.report_id}`} className="font-mono text-xs font-bold text-blue-400 hover:underline">
                          {sim.report_id}
                        </Link>
                        <div className="flex items-center gap-1.5">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-950 text-blue-300 border border-blue-800">
                            {Math.round(sim.similarity_score * 100)}% Similarity
                          </span>
                          <span className="text-[9px] font-mono text-industrial-500 uppercase">{sim.similarity_band.replace('_', ' ')}</span>
                        </div>
                      </div>

                      <p className="text-xs font-sans text-industrial-200 line-clamp-2 italic">
                        &quot;{sim.narrative_snippet}&quot;
                      </p>

                      {/* Shared details breakdown */}
                      <div className="pt-2 border-t border-industrial-800/80 text-[10px] font-mono space-y-1 text-industrial-400">
                        {sim.shared_details.shared_hazard && (
                          <div className="flex items-center gap-1 text-amber-300">
                            <span className="text-industrial-500">Shared Hazard:</span>
                            <span>{sim.shared_details.shared_hazard}</span>
                          </div>
                        )}
                        {sim.shared_details.shared_exposure && (
                          <div className="flex items-center gap-1 text-orange-300">
                            <span className="text-industrial-500">Shared Exposure:</span>
                            <span>{sim.shared_details.shared_exposure}</span>
                          </div>
                        )}
                        {sim.shared_details.shared_barrier && (
                          <div className="flex items-center gap-1 text-emerald-300">
                            <span className="text-industrial-500">Shared Barrier:</span>
                            <span>{sim.shared_details.shared_barrier}</span>
                          </div>
                        )}
                        {sim.shared_details.shared_lsr && (
                          <div className="flex items-center gap-1 text-purple-300">
                            <span className="text-industrial-500">Shared LSR:</span>
                            <span>{sim.shared_details.shared_lsr}</span>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center justify-between pt-1 text-[9px] font-mono text-industrial-500">
                        <span>Date: {sim.report_date ? String(sim.report_date) : 'N/A'}</span>
                        <Link href={`/reports/${sim.report_id}`} className="text-blue-400 hover:text-blue-300 font-semibold">
                          View Report →
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>

            {/* ══════════════════════════════════════════════════════════════════ */}
            {/* 7. HSE HUMAN-IN-THE-LOOP REVIEW WORKFLOW (PHASE 8)               */}
            {/* ══════════════════════════════════════════════════════════════════ */}
            <div id="review" className="space-y-6">
              {/* SIDE-BY-SIDE: AI ASSESSMENT VS HUMAN-REVIEWED ASSESSMENT */}
              <SectionCard
                title="7. AI Assessment vs. Human Review Comparison"
                subtitle="Dual-state transparency: Human reviewer decisions are stored separately and never overwrite original AI outputs"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* AI Output Card */}
                  <div className="p-4 bg-industrial-950 rounded border border-blue-900/60 space-y-3">
                    <div className="flex items-center justify-between border-b border-industrial-800 pb-2">
                      <span className="text-xs font-mono font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5" />
                        Original AI Assessment
                      </span>
                      <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-blue-950 text-blue-300 border border-blue-800">
                        AUTOMATED
                      </span>
                    </div>

                    <div className="space-y-2 text-xs font-mono">
                      <div className="flex justify-between py-1 border-b border-industrial-900">
                        <span className="text-industrial-500 uppercase text-[10px]">SIF Potential</span>
                        <span className="font-bold text-industrial-200">
                          {sifResult?.sif_fpi_potential || report?.sif_fpi_potential || 'NOT ANALYZED'}
                        </span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-industrial-900">
                        <span className="text-industrial-500 uppercase text-[10px]">Life-Saving Rule</span>
                        <span className="font-bold text-purple-300">
                          {lsrResult?.primary_life_saving_rule || report?.primary_life_saving_rule || 'NONE'}
                        </span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-industrial-900">
                        <span className="text-industrial-500 uppercase text-[10px]">Priority Level</span>
                        <span className="font-bold text-orange-300">
                          {priorityResult?.priority_level?.replace('_PRECURSOR', '') || report?.priority_level?.replace('_PRECURSOR', '') || 'ROUTINE'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Human-Reviewed Card */}
                  <div className="p-4 bg-industrial-950 rounded border border-emerald-900/60 space-y-3">
                    <div className="flex items-center justify-between border-b border-industrial-800 pb-2">
                      <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                        <UserCheck className="w-3.5 h-3.5" />
                        Human Safety Review
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase border ${
                          review
                            ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                            : 'bg-industrial-900 text-industrial-500 border-industrial-700'
                        }`}
                      >
                        {review ? review.review_status : 'PENDING REVIEW'}
                      </span>
                    </div>

                    {review ? (
                      <div className="space-y-2 text-xs font-mono">
                        <div className="flex justify-between py-1 border-b border-industrial-900">
                          <span className="text-industrial-500 uppercase text-[10px]">Reviewed SIF</span>
                          <span className="font-bold text-emerald-400">
                            {review.final_sif_potential || '—'}
                          </span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-industrial-900">
                          <span className="text-industrial-500 uppercase text-[10px]">Reviewed LSR</span>
                          <span className="font-bold text-emerald-300">
                            {review.final_lsr || '—'}
                          </span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-industrial-900">
                          <span className="text-industrial-500 uppercase text-[10px]">Reviewed Priority</span>
                          <span className="font-bold text-emerald-400">
                            {review.final_priority?.replace('_PRECURSOR', '') || '—'}
                          </span>
                        </div>
                        {review.reviewer_comment && (
                          <div className="pt-1 text-[11px] font-sans text-industrial-300 italic">
                            Rationale: &quot;{review.reviewer_comment}&quot;
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="py-6 text-center text-xs font-mono text-industrial-500 italic">
                        No human review completed yet. Submit a decision below.
                      </div>
                    )}
                  </div>
                </div>
              </SectionCard>

              {/* HSE REVIEW ACTION PANEL */}
              <SectionCard
                title="HSE Review Action Panel"
                subtitle="Inspect findings, confirm AI assessments, override conclusions, reject invalid items, or request more information."
              >
                {reviewFeedback && (
                  <div
                    className={`p-3 rounded text-xs font-mono mb-4 border ${
                      reviewFeedback.type === 'success'
                        ? 'bg-emerald-950/60 border-emerald-800 text-emerald-300'
                        : 'bg-red-950/60 border-red-800 text-red-300'
                    }`}
                  >
                    {reviewFeedback.message}
                  </div>
                )}

                <form onSubmit={handleReviewSubmit} className="space-y-5">
                  {/* Decision Selector Buttons */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-mono text-industrial-400 uppercase tracking-wider block">
                      Select Review Action
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
                      <button
                        type="button"
                        onClick={() => setSelectedDecision('CONFIRM_AI')}
                        className={`p-3 rounded border text-left transition-all ${
                          selectedDecision === 'CONFIRM_AI'
                            ? 'bg-blue-950/80 border-blue-500 text-white shadow-sm'
                            : 'bg-industrial-950 border-industrial-800 text-industrial-300 hover:border-industrial-700'
                        }`}
                      >
                        <div className="flex items-center gap-1.5 font-mono text-xs font-bold">
                          <ThumbsUp className="w-3.5 h-3.5 text-blue-400" />
                          <span>Confirm AI</span>
                        </div>
                        <p className="text-[10px] text-industrial-400 mt-1">Accept AI conclusions as valid</p>
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedDecision('OVERRIDE')}
                        className={`p-3 rounded border text-left transition-all ${
                          selectedDecision === 'OVERRIDE'
                            ? 'bg-amber-950/80 border-amber-500 text-white shadow-sm'
                            : 'bg-industrial-950 border-industrial-800 text-industrial-300 hover:border-industrial-700'
                        }`}
                      >
                        <div className="flex items-center gap-1.5 font-mono text-xs font-bold">
                          <Flame className="w-3.5 h-3.5 text-amber-400" />
                          <span>Override AI</span>
                        </div>
                        <p className="text-[10px] text-industrial-400 mt-1">Modify SIF, LSR, or Priority</p>
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedDecision('REJECT')}
                        className={`p-3 rounded border text-left transition-all ${
                          selectedDecision === 'REJECT'
                            ? 'bg-red-950/80 border-red-500 text-white shadow-sm'
                            : 'bg-industrial-950 border-industrial-800 text-industrial-300 hover:border-industrial-700'
                        }`}
                      >
                        <div className="flex items-center gap-1.5 font-mono text-xs font-bold">
                          <AlertOctagon className="w-3.5 h-3.5 text-red-400" />
                          <span>Reject Finding</span>
                        </div>
                        <p className="text-[10px] text-industrial-400 mt-1">Mark as false positive / invalid</p>
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedDecision('NEEDS_MORE_INFORMATION')}
                        className={`p-3 rounded border text-left transition-all ${
                          selectedDecision === 'NEEDS_MORE_INFORMATION'
                            ? 'bg-purple-950/80 border-purple-500 text-white shadow-sm'
                            : 'bg-industrial-950 border-industrial-800 text-industrial-300 hover:border-industrial-700'
                        }`}
                      >
                        <div className="flex items-center gap-1.5 font-mono text-xs font-bold">
                          <HelpCircle className="w-3.5 h-3.5 text-purple-400" />
                          <span>Needs More Info</span>
                        </div>
                        <p className="text-[10px] text-industrial-400 mt-1">Flag missing report evidence</p>
                      </button>
                    </div>
                  </div>

                  {/* OVERRIDE FIELDS */}
                  {selectedDecision === 'OVERRIDE' && (
                    <div className="p-4 bg-industrial-950 rounded border border-amber-900/60 space-y-3">
                      <span className="text-xs font-mono font-bold text-amber-300 uppercase block">
                        Specify Overridden Values
                      </span>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div>
                          <label className="text-[10px] font-mono uppercase text-industrial-400 block mb-1">
                            SIF / FPI Potential
                          </label>
                          <select
                            value={overrideSif}
                            onChange={(e) => setOverrideSif(e.target.value)}
                            className="w-full bg-industrial-900 border border-industrial-700 rounded px-2.5 py-1.5 text-xs font-mono text-industrial-200"
                          >
                            <option value="">Keep AI Value</option>
                            <option value="YES">YES — SIF Precursor</option>
                            <option value="UNCERTAIN">UNCERTAIN — Needs Clarification</option>
                            <option value="NO">NO — Non-SIF</option>
                          </select>
                        </div>

                        <div>
                          <label className="text-[10px] font-mono uppercase text-industrial-400 block mb-1">
                            Life-Saving Rule
                          </label>
                          <select
                            value={overrideLsr}
                            onChange={(e) => setOverrideLsr(e.target.value)}
                            className="w-full bg-industrial-900 border border-industrial-700 rounded px-2.5 py-1.5 text-xs font-mono text-industrial-200"
                          >
                            <option value="">Keep AI Value</option>
                            <option value="Line of Fire">Line of Fire</option>
                            <option value="Energy Isolation">Energy Isolation</option>
                            <option value="Safe Mechanical Lifting">Safe Mechanical Lifting</option>
                            <option value="Confined Space">Confined Space</option>
                            <option value="Driving">Driving</option>
                            <option value="Hot Work">Hot Work</option>
                            <option value="Bypassing Safety Controls">Bypassing Safety Controls</option>
                            <option value="Work Authorisation">Work Authorisation</option>
                            <option value="Working at Height">Working at Height</option>
                          </select>
                        </div>

                        <div>
                          <label className="text-[10px] font-mono uppercase text-industrial-400 block mb-1">
                            HSE Priority Level
                          </label>
                          <select
                            value={overridePriority}
                            onChange={(e) => setOverridePriority(e.target.value)}
                            className="w-full bg-industrial-900 border border-industrial-700 rounded px-2.5 py-1.5 text-xs font-mono text-industrial-200"
                          >
                            <option value="">Keep AI Value</option>
                            <option value="CRITICAL">Critical Override</option>
                            <option value="HIGH_PRIORITY_SIF_FPI_PRECURSOR">High Priority</option>
                            <option value="SAFETY_REVIEW">Safety Review</option>
                            <option value="ROUTINE">Routine</option>
                            <option value="UNCERTAIN">Uncertain</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* REJECT FIELDS */}
                  {selectedDecision === 'REJECT' && (
                    <div className="p-4 bg-industrial-950 rounded border border-red-900/60 space-y-3">
                      <span className="text-xs font-mono font-bold text-red-300 uppercase block">
                        Rejection Justification
                      </span>
                      <div>
                        <label className="text-[10px] font-mono uppercase text-industrial-400 block mb-1">
                          Primary Rejection Reason
                        </label>
                        <select
                          value={rejectionReason}
                          onChange={(e) => setRejectionReason(e.target.value)}
                          className="w-full md:w-1/2 bg-industrial-900 border border-industrial-700 rounded px-2.5 py-1.5 text-xs font-mono text-industrial-200"
                        >
                          <option value="FALSE_POSITIVE">False Positive Extraction</option>
                          <option value="INSUFFICIENT_EVIDENCE">Insufficient Evidence for SIF</option>
                          <option value="DUPLICATE_OBSERVATION">Duplicate Observation</option>
                          <option value="INCORRECT_INTERPRETATION">Incorrect Narrative Interpretation</option>
                          <option value="NOT_A_SIF_PRECURSOR">Not a Valid SIF/FPI Precursor</option>
                          <option value="OTHER">Other Reason</option>
                        </select>
                      </div>
                    </div>
                  )}

                  {/* NEEDS MORE INFO FIELDS */}
                  {selectedDecision === 'NEEDS_MORE_INFORMATION' && (
                    <div className="p-4 bg-industrial-950 rounded border border-purple-900/60 space-y-3">
                      <span className="text-xs font-mono font-bold text-purple-300 uppercase block">
                        Specify Missing Report Information
                      </span>
                      <div>
                        <label className="text-[10px] font-mono uppercase text-industrial-400 block mb-1">
                          Missing Fields (comma-separated, e.g. exposure_duration, barrier_condition, energy_level)
                        </label>
                        <input
                          type="text"
                          value={missingFieldsInput}
                          onChange={(e) => setMissingFieldsInput(e.target.value)}
                          className="w-full bg-industrial-900 border border-industrial-700 rounded px-2.5 py-1.5 text-xs font-mono text-industrial-200"
                          placeholder="exposure_duration, barrier_condition, personnel_location"
                        />
                      </div>
                    </div>
                  )}

                  {/* REVIEWER COMMENT (MANDATORY/RECOMMENDED) */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-mono uppercase text-industrial-400 block">
                      Reviewer Rationale & Audit Justification
                    </label>
                    <textarea
                      rows={3}
                      value={reviewerComment}
                      onChange={(e) => setReviewerComment(e.target.value)}
                      placeholder="Enter technical safety rationale for this review decision..."
                      className="w-full bg-industrial-900 border border-industrial-700 rounded p-2.5 text-xs font-mono text-industrial-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  {/* SUBMIT BUTTON */}
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={submittingReview}
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-semibold uppercase tracking-wider transition-colors disabled:opacity-50"
                    >
                      {submittingReview ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Save className="w-3.5 h-3.5" />
                      )}
                      Persist Review Decision
                    </button>
                  </div>
                </form>
              </SectionCard>

              {/* REVIEW AUDIT TRAIL HISTORY */}
              <SectionCard
                title="Review Audit Trail & Decision History"
                subtitle="Complete chronological audit record: WHO, WHAT, WHEN, and WHY for every human safety officer action"
              >
                {reviewHistory.length === 0 ? (
                  <div className="p-6 text-center text-xs font-mono text-industrial-500 italic">
                    No review history recorded yet for this safety report.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {reviewHistory.map((item) => (
                      <div
                        key={item.id}
                        className="p-3.5 bg-industrial-950 rounded border border-industrial-800 space-y-2 text-xs font-mono"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-industrial-800/80 pb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-industrial-100">{item.reviewer_id}</span>
                            <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-industrial-900 text-industrial-300 border border-industrial-700">
                              {item.review_decision}
                            </span>
                          </div>
                          <span className="text-[10px] text-industrial-500">{item.reviewed_at}</span>
                        </div>

                        {item.review_decision === 'OVERRIDE' && (
                          <div className="text-[11px] text-amber-300">
                            Overridden: SIF={item.final_sif_potential || 'N/A'}, LSR={item.final_lsr || 'N/A'}, Priority={item.final_priority || 'N/A'}
                          </div>
                        )}

                        {item.review_decision === 'REJECT' && (
                          <div className="text-[11px] text-red-300">
                            Rejection Reason: {item.rejection_reason || 'Unspecified'}
                          </div>
                        )}

                        {item.missing_information_fields && item.missing_information_fields.length > 0 && (
                          <div className="text-[11px] text-purple-300">
                            Missing Information: {item.missing_information_fields.join(', ')}
                          </div>
                        )}

                        {item.reviewer_comment && (
                          <p className="text-xs font-sans text-industrial-300 italic pt-1">
                            &quot;{item.reviewer_comment}&quot;
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

