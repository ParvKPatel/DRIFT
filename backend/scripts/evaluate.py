"""
Phase 9 — Reproducible Evaluation Runner CLI Script

Usage:
  python3 scripts/evaluate.py

Executes the model evaluation benchmark against reference cases,
calculates precision, recall, F1, F2, confusion matrix, critical misses,
audits data leakage, and outputs formatted evaluation report.
"""

import sys
import os
import asyncio

# Ensure backend root and project root are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.evaluation_service import EvaluationService


async def main():
    print("=" * 70)
    print("OIL SENTINEL — Model Evaluation & Benchmarking Suite")
    print("Dataset: SYNTHETIC / DEMO EVALUATION DATA (Reference Standard)")
    print("=" * 70)

    res = await EvaluationService.run_evaluation(db=None)

    print(f"\nEvaluation Overview:")
    print(f"  Dataset Name:        {res.dataset_name}")
    print(f"  Dataset Version:     {res.dataset_version}")
    print(f"  Pipeline Version:    {res.pipeline_version}")
    print(f"  Total Samples:       {res.sample_count}")

    print(f"\nClassification Metrics (SIF / FPI Screening):")
    print(f"  Precision:           {res.precision:.4f}")
    print(f"  Recall:              {res.recall:.4f}")
    print(f"  F1 Score:            {res.f1:.4f}")
    print(f"  F2 Score (Safety):   {res.f2:.4f}")
    print(f"  PR-AUC:              {res.pr_auc:.4f}")

    print(f"\nConfusion Matrix:")
    print(f"  True Positives (TP):   {res.confusion_matrix.true_positives}")
    print(f"  False Positives (FP):  {res.confusion_matrix.false_positives}")
    print(f"  True Negatives (TN):   {res.confusion_matrix.true_negatives}")
    print(f"  False Negatives (FN):  {res.confusion_matrix.false_negatives}")

    print(f"\nSafety-Critical Misses & Abstention:")
    print(f"  Critical Misses:       {res.critical_misses} (SIF cases classified as Non-SIF)")
    print(f"  Uncertain Predictions: {res.uncertain_count} ({res.uncertain_pct}%)")

    print(f"\nLife-Saving Rules (LSR) Accuracy:")
    print(f"  Overall LSR Accuracy:  {res.lsr_accuracy}%")
    print("  Per-Rule Breakdown:")
    for r in res.per_rule_metrics:
        print(f"    - {r.rule:28s}: {r.accuracy_pct}% ({r.correct_count}/{r.sample_count})")

    print(f"\nAudits & Robustness:")
    print(f"  Data Leakage Audit:    {'PASSED (Label-leaking fields excluded)' if res.leakage_check_passed else 'FAILED'}")
    print(f"  Synonym Robustness:    {res.robustness_score}%")
    print("=" * 70)
    print("Evaluation benchmark completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
