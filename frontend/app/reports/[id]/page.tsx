'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { StatusBadge } from '@/components/ui/StatusBadge';
import {
  SourceReport,
  SafetyAnalysisResult,
  SifScreeningResult,
  LsrMappingResult,
  PriorityResult,
  SimilarReportResponse,
  ReviewResponse,
  ReviewDecision,
} from '@/types';
import { ArrowLeft, Sparkles, RefreshCw, CheckCircle2, AlertTriangle, ShieldAlert, BookOpen, Activity, Wrench, Shield, User, MapPin, Zap, Save, Check } from 'lucide-react';
import Link from 'next/link';

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

  const [loading, setLoading] = useState(true);
  const [runningPipeline, setRunningPipeline] = useState(false);

  // Review Form
  const [selectedDecision, setSelectedDecision] = useState<ReviewDecision>('CONFIRM_AI');
  const [reviewerComment, setReviewerComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewFeedback, setReviewFeedback] = useState<{ type: string; message: string } | null>(null);
  const [isEditingReview, setIsEditingReview] = useState(false);

  const loadIntelligence = useCallback(async () => {
    if (!reportId) return;
    try {
      const [repRes, anRes, sifRes, lsrRes, prioRes, simRes, revRes] = await Promise.all([
        fetch(`/api/v1/reports/${encodeURIComponent(reportId)}`).catch(() => null),
        fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/analysis`).catch(() => null),
        fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/sif-analysis`).catch(() => null),
        fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/lsr`).catch(() => null),
        fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/priority`).catch(() => null),
        fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/similar?top_k=3&min_threshold=0.5`).catch(() => null),
        fetch(`/api/v1/reviews/${encodeURIComponent(reportId)}?t=${Date.now()}`).catch(() => null),
      ]);

      if (repRes?.ok) setReport(await repRes.json());
      if (anRes?.ok) setAnalysis(await anRes.json());
      if (sifRes?.ok) setSifResult(await sifRes.json());
      if (lsrRes?.ok) setLsrResult(await lsrRes.json());
      if (prioRes?.ok) setPriorityResult(await prioRes.json());
      if (simRes?.ok) setSimilarResult(await simRes.json());
      if (revRes?.ok) {
        const revData = await revRes.json();
        setReview(revData);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    loadIntelligence();
  }, [loadIntelligence]);

  const runFullPipeline = async () => {
    setRunningPipeline(true);
    try {
      await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/intelligence`, { method: 'POST' });
      await loadIntelligence();
    } catch (err) {
      console.error(err);
    } finally {
      setRunningPipeline(false);
    }
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingReview(true);
    try {
      const res = await fetch(`/api/v1/reviews/${encodeURIComponent(reportId)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer_id: 'HSE Safety Officer',
          review_decision: selectedDecision,
          reviewer_comment: reviewerComment,
        }),
      });
      if (res.ok) {
        setReviewFeedback({ type: 'success', message: 'Review saved successfully.' });
        setIsEditingReview(false);
        loadIntelligence();
      }
    } catch (err) {
      setReviewFeedback({ type: 'error', message: 'Failed to save review.' });
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleEditClick = () => {
    if (review) {
      setSelectedDecision(review.review_decision);
      setReviewerComment(review.reviewer_comment || '');
    }
    setIsEditingReview(true);
  };

  const formatDecision = (decision: string) => {
    switch (decision) {
      case 'CONFIRM_AI': return 'CONFIRMED';
      case 'OVERRIDE': return 'OVERRIDDEN';
      case 'REJECT': return 'REJECTED';
      case 'NEEDS_MORE_INFORMATION': return 'NEEDS INFO';
      default: return decision;
    }
  };

  if (loading) {
    return (
      <AppShell title={`Report: ${reportId}`}>
        <div className="p-8 text-center text-[13px] text-industrial-500">Loading safety report...</div>
      </AppShell>
    );
  }

  if (!report) {
    return (
      <AppShell title="Report Not Found">
        <EmptyState title="Missing Report" description={`Cannot find report ${reportId}`} />
      </AppShell>
    );
  }

  const isAnalyzed = !!sifResult;

  return (
    <AppShell title={`Report Detail`}>
      <div className="space-y-8 max-w-4xl mx-auto pb-12">
        {/* Navigation & Header Status */}
        <div className="flex items-center justify-between border-b border-industrial-850 pb-6">
          <div className="space-y-3">
            <Link href="/reports" className="text-[12px] text-industrial-500 hover:text-industrial-300 transition-colors flex items-center gap-1.5">
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Register
            </Link>
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-semibold text-industrial-100">{report.report_id}</h1>
              <div className="flex items-center gap-2">
                <PriorityBadge level={priorityResult?.priority_level || report.priority_level} />
                <StatusBadge status={sifResult?.sif_fpi_potential || report.sif_fpi_potential} />
              </div>
            </div>
            <p className="text-[13px] text-industrial-500">
              {report.site || 'Unknown Site'} • {report.report_date ? String(report.report_date).substring(0,10) : report.created_at ? String(report.created_at).substring(0,10) : 'No Date'}
            </p>
          </div>

          <button
            onClick={runFullPipeline}
            disabled={runningPipeline}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-[12px] font-medium transition-colors disabled:opacity-50"
          >
            {runningPipeline ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            Analyze Report
          </button>
        </div>

        {/* 1. Summary Section */}
        <section className="space-y-4">
          <h2 className="text-[11px] font-medium uppercase tracking-wider text-industrial-600">Event Summary</h2>
          <div className="p-5 bg-industrial-950 border border-industrial-850 rounded text-[14px] leading-relaxed text-industrial-200 whitespace-pre-wrap">
            {report.narrative}
          </div>
        </section>

        {isAnalyzed && (
          <>
            {/* 2. Risk & Priority */}
            <section className="space-y-4 pt-4 border-t border-industrial-900/50">
              <h2 className="text-[11px] font-medium uppercase tracking-wider text-industrial-600">Risk Profile</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-industrial-900/30 border border-industrial-850 rounded">
                  <div className="text-[11px] uppercase text-industrial-500 mb-1">Priority Score</div>
                  <div className="text-3xl font-semibold text-industrial-100">{priorityResult?.priority_score || '—'}</div>
                </div>
                <div className="p-4 bg-industrial-900/30 border border-industrial-850 rounded">
                  <div className="text-[11px] uppercase text-industrial-500 mb-1">Life-Saving Rule</div>
                  <div className="text-[15px] font-medium text-purple-400 mt-2">{lsrResult?.primary_life_saving_rule || 'None'}</div>
                </div>
                <div className="p-4 bg-industrial-900/30 border border-industrial-850 rounded">
                  <div className="text-[11px] uppercase text-industrial-500 mb-1">SIF Potential</div>
                  <div className="text-[15px] font-medium text-amber-500 mt-2">{sifResult?.sif_fpi_potential || 'Uncertain'}</div>
                </div>
              </div>
            </section>

            {/* 3. Evidence */}
            <section className="space-y-4 pt-4 border-t border-industrial-900/50">
              <h2 className="text-[11px] font-medium uppercase tracking-wider text-industrial-600">Extracted Facts</h2>
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {[
                  { label: 'Activity', val: analysis?.activity },
                  { label: 'Equipment', val: analysis?.equipment },
                  { label: 'Hazard', val: analysis?.hazard },
                  { label: 'Exposure', val: analysis?.exposure },
                  { label: 'Barrier', val: analysis?.barrier },
                  { label: 'Consequence', val: analysis?.potential_consequence },
                ].map((fact) => (
                  <div key={fact.label} className="p-3 bg-industrial-900/30 border border-industrial-850 rounded">
                    <div className="text-[10px] uppercase text-industrial-600 mb-1">{fact.label}</div>
                    <div className="text-[13px] text-industrial-200">{fact.val || '—'}</div>
                  </div>
                ))}
              </div>
            </section>

            {/* 3.5 AI Suggested Actions (Progressive Disclosure) */}
            {analysis?.suggested_actions && (
              <section className="space-y-4 pt-8 border-t border-industrial-850">
                <div className="flex items-center gap-2">
                  <h2 className="text-[11px] font-medium uppercase tracking-wider text-industrial-600">AI Suggested Actions</h2>
                  <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 text-[10px] uppercase tracking-wider">Advisory</span>
                </div>
                
                <div className="p-5 bg-industrial-900/50 border border-blue-900/30 rounded space-y-4">
                  <div className="flex items-start gap-3">
                    <ShieldAlert className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                    <div className="space-y-3 flex-1">
                      <p className="text-[12px] text-industrial-400 font-medium">
                        These actions are AI-generated based on extracted facts. Final decisions remain with the HSE professional.
                      </p>
                      
                      <ul className="space-y-2">
                        {(() => {
                          try {
                            const actions = JSON.parse(analysis.suggested_actions || "[]");
                            return (actions as string[]).map((act, i) => (
                              <li key={i} className="flex items-start gap-2 text-[13px] text-industrial-200">
                                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                                <span>{act}</span>
                              </li>
                            ));
                          } catch(e) {
                            return <li className="text-[13px] text-industrial-200">{analysis.suggested_actions}</li>;
                          }
                        })()}
                      </ul>
                      
                      {analysis.suggested_actions_reasoning && (
                        <details className="group mt-4">
                          <summary className="text-[12px] text-blue-400 cursor-pointer select-none hover:text-blue-300 transition-colors list-none flex items-center gap-1.5">
                            <span className="group-open:hidden">▶</span>
                            <span className="hidden group-open:inline">▼</span>
                            Why these suggestions?
                          </summary>
                          <div className="mt-2 pl-3 border-l-2 border-blue-900/50 text-[12.5px] leading-relaxed text-industrial-400 italic">
                            {analysis.suggested_actions_reasoning}
                          </div>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              </section>
            )}
          </>
        )}

        {/* 4. Action & Review */}
        <section className="space-y-4 pt-8 border-t border-industrial-850">
          <h2 className="text-[11px] font-medium uppercase tracking-wider text-industrial-600">Safety Review Action</h2>
          
          <div className="p-5 bg-industrial-900/50 border border-industrial-800 rounded">
            {review && !isEditingReview ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-[13px] text-industrial-200">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  <span>Reviewed by <strong>{review.reviewer_id}</strong> on {review.reviewed_at?.substring(0, 10) || 'Recently'}</span>
                  <span className="ml-auto px-2 py-1 bg-industrial-800 rounded text-[11px] font-medium uppercase">{formatDecision(review.review_decision)}</span>
                  <button onClick={handleEditClick} className="px-3 py-1 bg-industrial-800 hover:bg-industrial-700 text-industrial-300 rounded text-[11px] font-medium transition-colors">Edit</button>
                </div>
                <div className="pl-8 text-[13px] text-industrial-400 italic border-l-2 border-industrial-800 ml-2.5">
                  "{review.reviewer_comment || 'No additional comments provided.'}"
                </div>
              </div>
            ) : (
              <form onSubmit={handleReviewSubmit} className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {[
                    { val: 'CONFIRM_AI', label: 'Confirm AI' },
                    { val: 'OVERRIDE', label: 'Override' },
                    { val: 'REJECT', label: 'Reject' },
                    { val: 'NEEDS_MORE_INFORMATION', label: 'Needs Info' },
                  ].map((opt) => (
                    <button
                      key={opt.val}
                      type="button"
                      onClick={() => setSelectedDecision(opt.val as ReviewDecision)}
                      className={`p-2.5 rounded border text-center text-[12px] font-medium transition-all ${
                        selectedDecision === opt.val
                          ? 'bg-blue-600/20 border-blue-500 text-blue-400'
                          : 'bg-industrial-950 border-industrial-800 text-industrial-500'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                
                <textarea
                  rows={2}
                  value={reviewerComment}
                  onChange={(e) => setReviewerComment(e.target.value)}
                  placeholder="Review rationale..."
                  className="w-full bg-industrial-950 border border-industrial-800 rounded p-3 text-[13px] text-industrial-200 focus:border-blue-500 focus:outline-none"
                />
                
                <div className="flex justify-end gap-2">
                  {review && (
                    <button
                      type="button"
                      onClick={() => setIsEditingReview(false)}
                      className="px-4 py-2 bg-industrial-900 hover:bg-industrial-800 text-industrial-300 rounded text-[12px] font-medium transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                  <button
                    type="submit"
                    disabled={submittingReview}
                    className="px-4 py-2 bg-industrial-800 hover:bg-industrial-700 text-industrial-200 rounded text-[12px] font-medium transition-colors disabled:opacity-50"
                  >
                    {submittingReview ? 'Saving...' : (review ? 'Update Review' : 'Submit Review')}
                  </button>
                </div>
                
                {reviewFeedback && (
                  <div className={`text-[12px] ${reviewFeedback.type === 'success' ? 'text-emerald-500' : 'text-red-500'}`}>
                    {reviewFeedback.message}
                  </div>
                )}
              </form>
            )}
          </div>
        </section>

      </div>
    </AppShell>
  );
}
