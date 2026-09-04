from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.schemas.enums import (
    EvidenceStatus,
    SifDecision,
    BarrierCondition,
    PriorityLevel,
    EnergySource,
    AnalysisStatus,
    ScreeningStatus,
)

if TYPE_CHECKING:
    from app.models.reports import Report
    from app.models.evidence import Evidence


class SafetyAnalysis(Base):
    __tablename__ = "safety_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    
    activity: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    equipment: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    hazard: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    energy_source: Mapped[Optional[EnergySource]] = mapped_column(SQLEnum(EnergySource, name="energy_source_enum"), default=EnergySource.UNKNOWN, nullable=True)
    exposure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exposure_location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    barrier: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    barrier_condition: Mapped[Optional[BarrierCondition]] = mapped_column(SQLEnum(BarrierCondition, name="barrier_condition_enum"), default=BarrierCondition.UNKNOWN, nullable=True)
    potential_consequence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    sif_fpi_potential: Mapped[Optional[SifDecision]] = mapped_column(SQLEnum(SifDecision, name="sif_decision_enum"), default=SifDecision.UNCERTAIN, index=True, nullable=True)
    sif_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evidence_status: Mapped[Optional[EvidenceStatus]] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum"), default=EvidenceStatus.UNKNOWN, nullable=True)
    evidence_span: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    life_saving_rule: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    novelty_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    review_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Phase 4: SIF Screening Metadata & Transparent Signals
    screening_version: Mapped[Optional[str]] = mapped_column(String(50), default="sif-engine-v1", nullable=True)
    screened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    screening_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rule_ids_triggered: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-serialized list of rule IDs
    screening_status: Mapped[Optional[ScreeningStatus]] = mapped_column(
        SQLEnum(ScreeningStatus, name="screening_status_enum", create_constraint=False),
        default=ScreeningStatus.NOT_SCREENED,
        nullable=True
    )
    mechanism_signal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exposure_signal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consequence_signal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Phase 5: Life-Saving Rule (LSR) Mapping
    primary_life_saving_rule: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    secondary_life_saving_rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-serialized list of secondary LSR strings
    lsr_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lsr_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lsr_evidence_status: Mapped[Optional[EvidenceStatus]] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    lsr_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lsr_mapping_version: Mapped[Optional[str]] = mapped_column(String(50), default="lsr-engine-v1", nullable=True)

    # Calculated priority and intelligence scores (Phase 5)
    sif_evidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    barrier_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recurrence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    escalation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reporting_anomaly_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    priority_level: Mapped[Optional[PriorityLevel]] = mapped_column(SQLEnum(PriorityLevel, name="priority_level_enum"), default=PriorityLevel.UNCERTAIN, index=True, nullable=True)
    priority_reason_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-serialized list of priority reason codes
    priority_override: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    priority_version: Mapped[Optional[str]] = mapped_column(String(50), default="priority-engine-v1", nullable=True)
    priority_calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # AI Model Provenance & Traceability
    analysis_version: Mapped[str] = mapped_column(String(50), default="3.0.0", nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    provider_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "openai", "mock", etc.
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    analysis_status: Mapped[AnalysisStatus] = mapped_column(
        SQLEnum(AnalysisStatus, name="analysis_status_enum", create_constraint=False),
        default=AnalysisStatus.COMPLETED,
        nullable=False
    )

    # Phase 9: AI Suggested Actions
    suggested_actions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-serialized list of strings
    suggested_actions_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


    # Per-field confidence and evidence status (Phase 3)
    activity_evidence_status: Mapped[Optional[EvidenceStatus]] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    activity_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equipment_evidence_status: Mapped[Optional[EvidenceStatus]] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    equipment_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hazard_evidence_status: Mapped[Optional[EvidenceStatus]] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    hazard_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    energy_source_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    energy_source_evidence_status: Mapped[Optional[EvidenceStatus]] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    energy_source_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exposure_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exposure_evidence_status: Mapped[Optional[EvidenceStatus]] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    exposure_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exposure_location_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exposure_location_evidence_status: Mapped[Optional[EvidenceStatus]] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    exposure_location_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    barrier_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    barrier_evidence_status: Mapped[Optional[EvidenceStatus]] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    barrier_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    barrier_condition_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    barrier_condition_evidence_status: Mapped[Optional[EvidenceStatus]] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    barrier_condition_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    potential_consequence_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    potential_consequence_evidence_status: Mapped[Optional[EvidenceStatus]] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    potential_consequence_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_safety_analysis_sif_priority", "sif_fpi_potential", "priority_level"),
    )

    report: Mapped[Optional[Report]] = relationship("Report", back_populates="safety_analysis")
    evidence_items: Mapped[List[Evidence]] = relationship("Evidence", back_populates="safety_analysis", cascade="all, delete-orphan")
