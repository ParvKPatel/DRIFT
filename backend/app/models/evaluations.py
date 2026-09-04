"""
Phase 9 — Evaluation Run Model

Persistent model for storing reproducible evaluation benchmarking runs.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class EvaluationRun(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_name: Mapped[str] = mapped_column(String(200), nullable=False, default="Synthetic Demo Reference Dataset")
    dataset_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0-synthetic")
    pipeline_version: Mapped[str] = mapped_column(String(50), nullable=False, default="drift-v1")

    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Classification Metrics
    precision: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recall: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    f1: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    f2: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pr_auc: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Confusion Matrix
    true_positives: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    false_positives: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    true_negatives: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    false_negatives: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Safety-Critical Misses & Abstention
    critical_misses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uncertain_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uncertain_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # LSR & Robustness
    lsr_accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    per_rule_metrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-serialized per-rule metrics
    leakage_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    robustness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    run_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
