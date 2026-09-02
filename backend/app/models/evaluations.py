"""
Phase 9 — Evaluation Run Model

Persistent model for storing reproducible evaluation benchmarking runs.
"""

from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, func
from app.database import Base


class EvaluationRun(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_name = Column(String(200), nullable=False, default="Synthetic Demo Reference Dataset")
    dataset_version = Column(String(50), nullable=False, default="v1.0-synthetic")
    pipeline_version = Column(String(50), nullable=False, default="oil-sentinel-v1")

    sample_count = Column(Integer, nullable=False, default=0)

    # Classification Metrics
    precision = Column(Float, nullable=False, default=0.0)
    recall = Column(Float, nullable=False, default=0.0)
    f1 = Column(Float, nullable=False, default=0.0)
    f2 = Column(Float, nullable=False, default=0.0)
    pr_auc = Column(Float, nullable=False, default=0.0)

    # Confusion Matrix
    true_positives = Column(Integer, nullable=False, default=0)
    false_positives = Column(Integer, nullable=False, default=0)
    true_negatives = Column(Integer, nullable=False, default=0)
    false_negatives = Column(Integer, nullable=False, default=0)

    # Safety-Critical Misses & Abstention
    critical_misses = Column(Integer, nullable=False, default=0)
    uncertain_count = Column(Integer, nullable=False, default=0)
    uncertain_pct = Column(Float, nullable=False, default=0.0)

    # LSR & Robustness
    lsr_accuracy = Column(Float, nullable=False, default=0.0)
    per_rule_metrics = Column(Text, nullable=True)  # JSON-serialized per-rule metrics
    leakage_check_passed = Column(Boolean, nullable=False, default=True)
    robustness_score = Column(Float, nullable=False, default=0.0)

    run_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
