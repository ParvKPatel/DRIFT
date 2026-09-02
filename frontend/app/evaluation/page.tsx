'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { EvaluationRunResponse } from '@/types';
import {
  BarChart3,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  ShieldCheck,
  Flame,
  Info,
  Layers,
  ArrowUpRight,
} from 'lucide-react';

export default function EvaluationPage() {
  const [evaluation, setEvaluation] = useState<EvaluationRunResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLatestEvaluation = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/evaluations/latest');
      if (res.ok) {
        const data = await res.json();
        setEvaluation(data);
      } else {
        setEvaluation(null);
      }
    } catch (err) {
      console.error('Failed to fetch latest evaluation:', err);
      setError('Unable to connect to evaluation API service.');
    } finally {
      setLoading(false);
    }
  }, []);

  const triggerEvaluation = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/evaluations/run', {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setEvaluation(data);
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || 'Failed to execute evaluation benchmark.');
      }
    } catch (err) {
      console.error('Failed to trigger evaluation run:', err);
      setError('Error communicating with backend during evaluation run.');
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    fetchLatestEvaluation();
  }, [fetchLatestEvaluation]);

  return (
    <AppShell title="Model Benchmarking & Safety Evaluation">
      <div className="space-y-6 max-w-7xl mx-auto">
        {/* Synthetic Reference Standard Banner */}
        <div className="p-4 rounded-lg bg-blue-950/40 border border-blue-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-blue-200">
                  SYNTHETIC / DEMO EVALUATION DATA
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-900/60 text-blue-300 border border-blue-700">
                  REFERENCE STANDARD v1.0
                </span>
              </div>
              <p className="text-xs text-blue-300/80 mt-1">
                Evaluation results are computed against an expert-annotated 25-case reference standard.
                Never claimed as real OIL operating statistics. All metrics reflect genuine pipeline execution.
              </p>
            </div>
          </div>
          <button
            onClick={triggerEvaluation}
            disabled={running}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-bold transition-all disabled:opacity-50 shrink-0 shadow-lg shadow-blue-950"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${running ? 'animate-spin' : ''}`} />
            <span>{running ? 'Running Benchmark...' : 'Run Evaluation Suite'}</span>
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-950/60 border border-red-800 rounded text-xs text-red-300 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <SectionCard title="Loading Evaluation Benchmark">
            <div className="p-12 text-center font-mono text-xs text-industrial-400 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              Loading latest evaluation run from database...
            </div>
          </SectionCard>
        ) : !evaluation ? (
          <SectionCard title="Model Evaluation Status">
            <EmptyState
              title="No Evaluation Results Available"
              description="Click 'Run Evaluation Suite' above to execute the reproducible evaluation pipeline and compute genuine precision, recall, and safety metrics."
            />
          </SectionCard>
        ) : (
          <div className="space-y-6">
            {/* Run Metadata Card */}
            <div className="p-3 bg-industrial-900 rounded border border-industrial-800 flex flex-wrap items-center justify-between text-xs font-mono text-industrial-400 gap-2">
              <div>
                Run ID: <span className="text-industrial-200 font-bold">#{evaluation.id}</span> | Pipeline: <span className="text-blue-300">{evaluation.pipeline_version}</span>
              </div>
              <div>
                Dataset: <span className="text-industrial-200">{evaluation.dataset_name} ({evaluation.dataset_version})</span>
              </div>
              <div>
                Evaluated: <span className="text-industrial-300">{new Date(evaluation.run_timestamp).toLocaleString()}</span>
              </div>
            </div>

            {/* Core Classification KPI Metric Cards */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div className="p-4 bg-industrial-900 rounded border border-industrial-800 space-y-1">
                <span className="text-[10px] font-mono text-industrial-400 uppercase tracking-wider">Precision</span>
                <div className="text-2xl font-bold font-mono text-emerald-400">
                  {Math.round(evaluation.precision * 100)}%
                </div>
                <span className="text-[10px] text-industrial-500">True SIF / All Flagged</span>
              </div>

              <div className="p-4 bg-industrial-900 rounded border border-industrial-800 space-y-1">
                <span className="text-[10px] font-mono text-industrial-400 uppercase tracking-wider">Recall</span>
                <div className="text-2xl font-bold font-mono text-blue-400">
                  {Math.round(evaluation.recall * 100)}%
                </div>
                <span className="text-[10px] text-industrial-500">Coverage of Known SIF</span>
              </div>

              <div className="p-4 bg-industrial-900 rounded border border-industrial-800 space-y-1">
                <span className="text-[10px] font-mono text-industrial-400 uppercase tracking-wider">F1 Score</span>
                <div className="text-2xl font-bold font-mono text-cyan-400">
                  {evaluation.f1.toFixed(3)}
                </div>
                <span className="text-[10px] text-industrial-500">Harmonic Mean</span>
              </div>

              <div className="p-4 bg-industrial-900 rounded border border-industrial-800 space-y-1">
                <span className="text-[10px] font-mono text-industrial-400 uppercase tracking-wider">F2 Score</span>
                <div className="text-2xl font-bold font-mono text-purple-400">
                  {evaluation.f2.toFixed(3)}
                </div>
                <span className="text-[10px] text-industrial-500">Safety Recall-Biased</span>
              </div>

              <div className="p-4 bg-industrial-900 rounded border border-red-900/60 space-y-1">
                <span className="text-[10px] font-mono text-red-400 uppercase tracking-wider">Critical Misses</span>
                <div className="text-2xl font-bold font-mono text-red-400">
                  {evaluation.critical_misses}
                </div>
                <span className="text-[10px] text-red-500/80">SIF Marked as Non-SIF</span>
              </div>

              <div className="p-4 bg-industrial-900 rounded border border-amber-900/60 space-y-1">
                <span className="text-[10px] font-mono text-amber-400 uppercase tracking-wider">Abstention</span>
                <div className="text-2xl font-bold font-mono text-amber-400">
                  {evaluation.uncertain_pct}%
                </div>
                <span className="text-[10px] text-amber-500/80">{evaluation.uncertain_count} Uncertain Cases</span>
              </div>
            </div>

            {/* Middle Grid: Confusion Matrix & Data Leakage Audit */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Confusion Matrix */}
              <SectionCard
                title="SIF Precursor Confusion Matrix"
                subtitle="True Positives vs False Alarms vs Missed Precursors"
              >
                <div className="p-4 space-y-4">
                  <div className="grid grid-cols-2 gap-3 max-w-md mx-auto text-center font-mono">
                    <div className="p-4 bg-emerald-950/40 border border-emerald-800 rounded">
                      <div className="text-xs text-emerald-400 uppercase font-semibold">True Positives (TP)</div>
                      <div className="text-2xl font-bold text-emerald-300 mt-1">
                        {evaluation.confusion_matrix.true_positives}
                      </div>
                      <div className="text-[10px] text-industrial-400 mt-1">Correctly Identified SIF</div>
                    </div>

                    <div className="p-4 bg-amber-950/40 border border-amber-800 rounded">
                      <div className="text-xs text-amber-400 uppercase font-semibold">False Positives (FP)</div>
                      <div className="text-2xl font-bold text-amber-300 mt-1">
                        {evaluation.confusion_matrix.false_positives}
                      </div>
                      <div className="text-[10px] text-industrial-400 mt-1">False Alarms</div>
                    </div>

                    <div className="p-4 bg-red-950/40 border border-red-800 rounded">
                      <div className="text-xs text-red-400 uppercase font-semibold">False Negatives (FN)</div>
                      <div className="text-2xl font-bold text-red-300 mt-1">
                        {evaluation.confusion_matrix.false_negatives}
                      </div>
                      <div className="text-[10px] text-industrial-400 mt-1">Missed Precursors</div>
                    </div>

                    <div className="p-4 bg-blue-950/40 border border-blue-800 rounded">
                      <div className="text-xs text-blue-400 uppercase font-semibold">True Negatives (TN)</div>
                      <div className="text-2xl font-bold text-blue-300 mt-1">
                        {evaluation.confusion_matrix.true_negatives}
                      </div>
                      <div className="text-[10px] text-industrial-400 mt-1">Routine Observations</div>
                    </div>
                  </div>
                  <p className="text-[11px] text-industrial-400 text-center italic">
                    Safety Principle: In industrial hazard screening, minimizing False Negatives (FN) is prioritized over minimizing False Positives.
                  </p>
                </div>
              </SectionCard>

              {/* Data Leakage Audit & Robustness Card */}
              <SectionCard
                title="Integrity & Robustness Audits"
                subtitle="Validation of feature isolation and semantic invariance"
              >
                <div className="p-4 space-y-4">
                  <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {evaluation.leakage_check_passed ? (
                          <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <ShieldAlert className="w-4 h-4 text-red-400" />
                        )}
                        <span className="text-xs font-bold text-industrial-200">Data Leakage Audit</span>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        evaluation.leakage_check_passed ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-red-950 text-red-300 border border-red-800'
                      }`}>
                        {evaluation.leakage_check_passed ? 'PASSED — NO LEAKAGE' : 'FAILED LEAKAGE DETECTED'}
                      </span>
                    </div>
                    <p className="text-[11px] text-industrial-400">
                      Verifies that label-leaking fields (<code className="text-industrial-300 font-mono">fixed_short_description</code>, post-incident reviewer determinations, or ground truth labels) are strictly excluded from prediction input features.
                    </p>
                  </div>

                  <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-blue-400" />
                        <span className="text-xs font-bold text-industrial-200">Synonym & Phrasing Invariance</span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-950 text-blue-300 border border-blue-800">
                        {evaluation.robustness_score}% ROBUST
                      </span>
                    </div>
                    <p className="text-[11px] text-industrial-400">
                      Tests rule triggers against varied narrative terminology (e.g. &quot;struck-by&quot; vs &quot;component flew out&quot; vs &quot;pin ejected at speed&quot;) to verify phrasing robustness.
                    </p>
                  </div>

                  <div className="p-3 bg-industrial-950 rounded border border-industrial-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Flame className="w-4 h-4 text-amber-400" />
                        <span className="text-xs font-bold text-industrial-200">Abstention / Uncertainty Capability</span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950 text-amber-300 border border-amber-800">
                        {evaluation.uncertain_count} ABSTENTIONS ({evaluation.uncertain_pct}%)
                      </span>
                    </div>
                    <p className="text-[11px] text-industrial-400">
                      Ambiguous or unverified observations are properly returned as <code className="text-amber-300 font-mono">UNCERTAIN</code> rather than forcing premature YES/NO decisions without evidence.
                    </p>
                  </div>
                </div>
              </SectionCard>
            </div>

            {/* Life-Saving Rules Evaluation Table */}
            <SectionCard
              title={`IOGP Life-Saving Rules Mapping Accuracy (${evaluation.lsr_accuracy}%)`}
              subtitle="Per-rule mapping accuracy across the 9 official Life-Saving Rules"
            >
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-industrial-800 text-industrial-400 bg-industrial-950">
                      <th className="p-3">Life-Saving Rule</th>
                      <th className="p-3">Sample Count</th>
                      <th className="p-3">Correct Mappings</th>
                      <th className="p-3">Accuracy</th>
                      <th className="p-3">Reliability Band</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-industrial-900">
                    {evaluation.per_rule_metrics.map((r) => (
                      <tr key={r.rule} className="hover:bg-industrial-900/50">
                        <td className="p-3 font-semibold text-purple-300">{r.rule}</td>
                        <td className="p-3 text-industrial-300">{r.sample_count}</td>
                        <td className="p-3 text-industrial-300">{r.correct_count}</td>
                        <td className="p-3">
                          <span className={`font-bold ${
                            r.accuracy_pct >= 80 ? 'text-emerald-400' : r.accuracy_pct >= 50 ? 'text-amber-400' : 'text-red-400'
                          }`}>
                            {r.accuracy_pct}%
                          </span>
                        </td>
                        <td className="p-3">
                          {r.sample_count === 0 ? (
                            <span className="text-[10px] text-industrial-500">NO SAMPLES</span>
                          ) : r.accuracy_pct >= 80 ? (
                            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">HIGH</span>
                          ) : r.accuracy_pct >= 50 ? (
                            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-amber-950 text-amber-300 border border-amber-800">MODERATE</span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-red-950 text-red-300 border border-red-800">LOW / REQUIRES TUNING</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </SectionCard>
          </div>
        )}
      </div>
    </AppShell>
  );
}
