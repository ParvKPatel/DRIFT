'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { SectionCard } from '@/components/ui/SectionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { EvaluationRunResponse } from '@/types';
import { RefreshCw, AlertTriangle, ChevronDown, ChevronUp, CheckCircle2, Info, Activity } from 'lucide-react';

export default function EvaluationPage() {
  const [evaluation, setEvaluation] = useState<EvaluationRunResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

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
      const res = await fetch('/api/v1/evaluations/run', { method: 'POST' });
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
    <AppShell title="System Health & Evaluation">
      <div className="space-y-8 max-w-5xl mx-auto pb-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-industrial-850 pb-6 gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-industrial-100">AI Safety Evaluator</h1>
            <p className="text-[13px] text-industrial-500 mt-1">Monitor the AI pipeline's accuracy against expert-annotated reference standards.</p>
          </div>
          <button
            onClick={triggerEvaluation}
            disabled={running}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white text-[12px] font-medium transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${running ? 'animate-spin' : ''}`} />
            {running ? 'Running Benchmark...' : 'Run New Evaluation'}
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-950/40 border border-red-800 rounded flex items-center gap-3 text-[13px] text-red-400">
            <AlertTriangle className="w-5 h-5 shrink-0" /> {error}
          </div>
        )}

        {loading ? (
          <div className="py-12 text-center text-[12px] text-industrial-500 flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
            Loading latest evaluation run...
          </div>
        ) : !evaluation ? (
          <EmptyState
            title="No Evaluation Data"
            description="Run the evaluation suite to measure AI performance against reference safety cases."
          />
        ) : (
          <div className="space-y-6">
            {/* High-Level Overview */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-5 bg-industrial-950 border border-industrial-850 rounded text-center">
                <div className="text-[11px] uppercase text-industrial-500 mb-1">Precision</div>
                <div className="text-3xl font-semibold text-emerald-500">{Math.round(evaluation.precision * 100)}%</div>
                <div className="text-[11px] text-industrial-600 mt-1">Accuracy of flags</div>
              </div>
              <div className="p-5 bg-industrial-950 border border-industrial-850 rounded text-center">
                <div className="text-[11px] uppercase text-industrial-500 mb-1">Recall</div>
                <div className="text-3xl font-semibold text-blue-500">{Math.round(evaluation.recall * 100)}%</div>
                <div className="text-[11px] text-industrial-600 mt-1">Missed cases caught</div>
              </div>
              <div className="p-5 bg-industrial-950 border border-industrial-850 rounded text-center">
                <div className="text-[11px] uppercase text-industrial-500 mb-1">Critical Misses</div>
                <div className="text-3xl font-semibold text-red-500">{evaluation.critical_misses}</div>
                <div className="text-[11px] text-industrial-600 mt-1">Safety incidents ignored</div>
              </div>
              <div className="p-5 bg-industrial-950 border border-industrial-850 rounded text-center">
                <div className="text-[11px] uppercase text-industrial-500 mb-1">Abstentions</div>
                <div className="text-3xl font-semibold text-amber-500">{evaluation.uncertain_count}</div>
                <div className="text-[11px] text-industrial-600 mt-1">Cases sent for review</div>
              </div>
            </div>

            <div className="flex justify-center mt-6">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-industrial-900 border border-industrial-800 text-[12px] font-medium text-industrial-300 hover:text-industrial-100 hover:bg-industrial-800 transition-colors"
              >
                {showDetails ? 'Hide Detailed Technical Logs' : 'View Detailed Technical Logs'}
                {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            </div>

            {showDetails && (
              <div className="space-y-6 pt-4 border-t border-industrial-850 animate-in fade-in slide-in-from-top-4 duration-300">
                {/* Technical Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Confusion Matrix */}
                  <div className="p-5 bg-industrial-950 border border-industrial-850 rounded">
                    <h3 className="text-[13px] font-semibold text-industrial-200 mb-4 flex items-center gap-2">
                      <Activity className="w-4 h-4" /> Confusion Matrix
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 bg-industrial-900 rounded border border-industrial-800">
                        <div className="text-[10px] uppercase text-emerald-500 mb-1">True Positives</div>
                        <div className="text-xl font-semibold text-industrial-200">{evaluation.confusion_matrix.true_positives}</div>
                      </div>
                      <div className="p-3 bg-industrial-900 rounded border border-industrial-800">
                        <div className="text-[10px] uppercase text-amber-500 mb-1">False Positives</div>
                        <div className="text-xl font-semibold text-industrial-200">{evaluation.confusion_matrix.false_positives}</div>
                      </div>
                      <div className="p-3 bg-industrial-900 rounded border border-industrial-800">
                        <div className="text-[10px] uppercase text-red-500 mb-1">False Negatives</div>
                        <div className="text-xl font-semibold text-industrial-200">{evaluation.confusion_matrix.false_negatives}</div>
                      </div>
                      <div className="p-3 bg-industrial-900 rounded border border-industrial-800">
                        <div className="text-[10px] uppercase text-blue-500 mb-1">True Negatives</div>
                        <div className="text-xl font-semibold text-industrial-200">{evaluation.confusion_matrix.true_negatives}</div>
                      </div>
                    </div>
                  </div>

                  {/* Audit Logs */}
                  <div className="p-5 bg-industrial-950 border border-industrial-850 rounded">
                    <h3 className="text-[13px] font-semibold text-industrial-200 mb-4 flex items-center gap-2">
                      <Info className="w-4 h-4" /> Integrity Audits
                    </h3>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center pb-3 border-b border-industrial-900">
                        <span className="text-[12px] text-industrial-400">Data Leakage Audit</span>
                        {evaluation.leakage_check_passed ? (
                          <span className="px-2 py-1 rounded bg-emerald-900/30 text-emerald-500 text-[10px] uppercase font-medium">Passed</span>
                        ) : (
                          <span className="px-2 py-1 rounded bg-red-900/30 text-red-500 text-[10px] uppercase font-medium">Failed</span>
                        )}
                      </div>
                      <div className="flex justify-between items-center pb-3 border-b border-industrial-900">
                        <span className="text-[12px] text-industrial-400">Robustness Score</span>
                        <span className="text-[12px] font-medium text-industrial-200">{evaluation.robustness_score}%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-[12px] text-industrial-400">LSR Mapping Accuracy</span>
                        <span className="text-[12px] font-medium text-purple-400">{evaluation.lsr_accuracy}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
