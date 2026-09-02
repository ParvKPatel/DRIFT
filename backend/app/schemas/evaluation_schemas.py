"""
Phase 9 — Evaluation Schemas

Pydantic schemas for the model evaluation, benchmarking, and leakage audit system.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class ConfusionMatrixData(BaseModel):
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int


class LsrRuleMetric(BaseModel):
    rule: str
    sample_count: int
    correct_count: int
    accuracy_pct: float


class EvaluationRunResponse(BaseModel):
    id: int
    dataset_name: str
    dataset_version: str
    pipeline_version: str
    sample_count: int

    # Core Metrics
    precision: float
    recall: float
    f1: float
    f2: float
    pr_auc: float

    # Confusion matrix
    confusion_matrix: ConfusionMatrixData

    # Safety metrics
    critical_misses: int
    uncertain_count: int
    uncertain_pct: float

    # LSR accuracy & breakdown
    lsr_accuracy: float
    per_rule_metrics: List[LsrRuleMetric] = Field(default_factory=list)

    # Audits
    leakage_check_passed: bool
    robustness_score: float
    run_timestamp: datetime
