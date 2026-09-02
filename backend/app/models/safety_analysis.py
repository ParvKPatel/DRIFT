from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Index, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.schemas.enums import EvidenceStatus, SifDecision, BarrierCondition, PriorityLevel, EnergySource, AnalysisStatus, ScreeningStatus


class SafetyAnalysis(Base):
    __tablename__ = "safety_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    
    activity = Column(String(200), nullable=True)
    equipment = Column(String(200), nullable=True)
    hazard = Column(Text, nullable=True)
    energy_source = Column(SQLEnum(EnergySource, name="energy_source_enum"), default=EnergySource.UNKNOWN, nullable=True)
    exposure = Column(Text, nullable=True)
    exposure_location = Column(String(200), nullable=True)
    barrier = Column(String(150), nullable=True)
    barrier_condition = Column(SQLEnum(BarrierCondition, name="barrier_condition_enum"), default=BarrierCondition.UNKNOWN, nullable=True)
    potential_consequence = Column(Text, nullable=True)
    
    sif_fpi_potential = Column(SQLEnum(SifDecision, name="sif_decision_enum"), default=SifDecision.UNCERTAIN, index=True, nullable=True)
    sif_confidence = Column(Float, nullable=True)
    evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum"), default=EvidenceStatus.UNKNOWN, nullable=True)
    evidence_span = Column(Text, nullable=True)
    reason_code = Column(String(100), nullable=True)
    life_saving_rule = Column(String(50), index=True, nullable=True)
    novelty_score = Column(Float, nullable=True)
    review_required = Column(Boolean, default=False, index=True, nullable=False)
    review_reason = Column(Text, nullable=True)

    # Phase 4: SIF Screening Metadata & Transparent Signals
    screening_version = Column(String(50), default="sif-engine-v1", nullable=True)
    screened_at = Column(DateTime(timezone=True), nullable=True)
    screening_reason = Column(Text, nullable=True)
    rule_ids_triggered = Column(Text, nullable=True)  # JSON-serialized list of rule IDs
    screening_status = Column(
        SQLEnum(ScreeningStatus, name="screening_status_enum", create_constraint=False),
        default=ScreeningStatus.NOT_SCREENED,
        nullable=True
    )
    mechanism_signal = Column(Float, nullable=True)
    exposure_signal = Column(Float, nullable=True)
    consequence_signal = Column(Float, nullable=True)

    # Phase 5: Life-Saving Rule (LSR) Mapping
    primary_life_saving_rule = Column(String(100), index=True, nullable=True)
    secondary_life_saving_rules = Column(Text, nullable=True)  # JSON-serialized list of secondary LSR strings
    lsr_confidence = Column(Float, nullable=True)
    lsr_evidence = Column(Text, nullable=True)
    lsr_evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    lsr_reason = Column(Text, nullable=True)
    lsr_mapping_version = Column(String(50), default="lsr-engine-v1", nullable=True)

    # Calculated priority and intelligence scores (Phase 5)
    sif_evidence_score = Column(Float, nullable=True)
    barrier_score = Column(Float, nullable=True)
    recurrence_score = Column(Float, nullable=True)
    escalation_score = Column(Float, nullable=True)
    reporting_anomaly_score = Column(Float, nullable=True)
    priority_score = Column(Float, nullable=True)
    priority_level = Column(SQLEnum(PriorityLevel, name="priority_level_enum"), default=PriorityLevel.UNCERTAIN, index=True, nullable=True)
    priority_reason_codes = Column(Text, nullable=True)  # JSON-serialized list of priority reason codes
    priority_override = Column(Boolean, default=False, nullable=True)
    priority_version = Column(String(50), default="priority-engine-v1", nullable=True)
    priority_calculated_at = Column(DateTime(timezone=True), nullable=True)

    # AI Model Provenance & Traceability
    analysis_version = Column(String(50), default="3.0.0", nullable=False)
    model_name = Column(String(100), nullable=True)
    provider_name = Column(String(100), nullable=True)  # "openai", "mock", etc.
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    is_mock = Column(Boolean, default=False, nullable=False)
    analysis_status = Column(
        SQLEnum(AnalysisStatus, name="analysis_status_enum", create_constraint=False),
        default=AnalysisStatus.COMPLETED,
        nullable=False
    )

    # Per-field confidence and evidence status (Phase 3)
    activity_evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    activity_confidence = Column(Float, nullable=True)
    equipment_evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    equipment_confidence = Column(Float, nullable=True)
    hazard_evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    hazard_confidence = Column(Float, nullable=True)
    energy_source_evidence = Column(Text, nullable=True)
    energy_source_evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    energy_source_confidence = Column(Float, nullable=True)
    exposure_evidence = Column(Text, nullable=True)
    exposure_evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    exposure_confidence = Column(Float, nullable=True)
    exposure_location_evidence = Column(Text, nullable=True)
    exposure_location_evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    exposure_location_confidence = Column(Float, nullable=True)
    barrier_evidence = Column(Text, nullable=True)
    barrier_evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    barrier_confidence = Column(Float, nullable=True)
    barrier_condition_evidence = Column(Text, nullable=True)
    barrier_condition_evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    barrier_condition_confidence = Column(Float, nullable=True)
    potential_consequence_evidence = Column(Text, nullable=True)
    potential_consequence_evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum", create_constraint=False), nullable=True)
    potential_consequence_confidence = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_safety_analysis_sif_priority", "sif_fpi_potential", "priority_level"),
    )

    report = relationship("Report", back_populates="safety_analysis")
    evidence_items = relationship("Evidence", back_populates="safety_analysis", cascade="all, delete-orphan")
