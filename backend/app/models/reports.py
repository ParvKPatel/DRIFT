from sqlalchemy import Column, Integer, String, Float, Text, Date, Time, DateTime, Enum as SQLEnum, UniqueConstraint, Index, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.schemas.enums import ProvenanceType, AnalysisStatus


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(String(100), unique=True, index=True, nullable=False)
    source_system_id = Column(String(100), nullable=True)
    report_date = Column(Date, index=True, nullable=True)
    report_time = Column(Time, nullable=True)
    site = Column(String(150), index=True, nullable=True)
    unit = Column(String(150), index=True, nullable=True)
    shift = Column(String(50), nullable=True)
    functional_location = Column(String(200), index=True, nullable=True)
    functional_location_description = Column(Text, nullable=True)
    item_no = Column(String(100), nullable=True)
    incident_type = Column(String(100), index=True, nullable=True)
    incident_sub_type = Column(String(100), nullable=True)
    incident_cause = Column(String(200), index=True, nullable=True)
    fixed_short_description = Column(Text, index=True, nullable=True)
    line_item = Column(String(50), nullable=True)
    narrative = Column(Text, nullable=False)
    corrective_action = Column(Text, nullable=True)
    preventive_action = Column(Text, nullable=True)
    man_hours = Column(Float, nullable=True)
    lost_time = Column(Float, nullable=True)
    operational_time_lost = Column(Float, nullable=True)
    financial_implication = Column(Float, nullable=True)
    currency = Column(String(10), default="INR", nullable=True)
    affected_person_type = Column(String(50), nullable=True)
    employee_or_contractor = Column(String(50), nullable=True)
    designation = Column(String(100), nullable=True)
    contractor_name = Column(String(150), nullable=True)
    actual_outcome = Column(String(150), nullable=True)

    # Phase 3: AI Analysis Status (NOT_ANALYZED by default — not the same as 'AI found no hazard')
    analysis_status = Column(
        SQLEnum(AnalysisStatus, name="analysis_status_enum"),
        default=AnalysisStatus.NOT_ANALYZED,
        index=True,
        nullable=False
    )

    source_file = Column(String(255), nullable=True)
    source_row_number = Column(Integer, nullable=True)
    provenance = Column(SQLEnum(ProvenanceType, name="provenance_type_enum"), default=ProvenanceType.OIL_EXPORT, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_reports_site_date", "site", "report_date"),
        Index("idx_reports_incident_cause_type", "incident_cause", "incident_type"),
    )

    safety_analysis = relationship("SafetyAnalysis", back_populates="report", uselist=False, cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="report", cascade="all, delete-orphan")
    embeddings = relationship("ReportEmbedding", back_populates="report", cascade="all, delete-orphan")
    similar_reports_source = relationship("SimilarReport", foreign_keys="SimilarReport.report_id", back_populates="report", cascade="all, delete-orphan")
    cluster_memberships = relationship("ClusterMember", back_populates="report", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="report")
    reviews = relationship("Review", back_populates="report")
