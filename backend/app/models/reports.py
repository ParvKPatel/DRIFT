from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import date, time, datetime
from sqlalchemy import Integer, String, Float, Text, Date, Time, DateTime, Enum as SQLEnum, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.schemas.enums import ProvenanceType, AnalysisStatus

if TYPE_CHECKING:
    from app.models.safety_analysis import SafetyAnalysis
    from app.models.evidence import Evidence
    from app.models.embeddings import ReportEmbedding
    from app.models.similar_reports import SimilarReport
    from app.models.clusters import ClusterMember
    from app.models.alerts import Alert
    from app.models.reviews import Review


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    source_system_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    report_date: Mapped[Optional[date]] = mapped_column(Date, index=True, nullable=True)
    report_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    site: Mapped[Optional[str]] = mapped_column(String(150), index=True, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(150), index=True, nullable=True)
    shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    functional_location: Mapped[Optional[str]] = mapped_column(String(200), index=True, nullable=True)
    functional_location_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    item_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    incident_type: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    incident_sub_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    incident_cause: Mapped[Optional[str]] = mapped_column(String(200), index=True, nullable=True)
    fixed_short_description: Mapped[Optional[str]] = mapped_column(Text, index=True, nullable=True)
    line_item: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    corrective_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preventive_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    man_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lost_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    operational_time_lost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    financial_implication: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), default="INR", nullable=True)
    affected_person_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    employee_or_contractor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contractor_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    actual_outcome: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    # Phase 3: AI Analysis Status (NOT_ANALYZED by default — not the same as 'AI found no hazard')
    analysis_status: Mapped[AnalysisStatus] = mapped_column(
        SQLEnum(AnalysisStatus, name="analysis_status_enum"),
        default=AnalysisStatus.NOT_ANALYZED,
        index=True,
        nullable=False
    )

    source_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    provenance: Mapped[ProvenanceType] = mapped_column(SQLEnum(ProvenanceType, name="provenance_type_enum"), default=ProvenanceType.OIL_EXPORT, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_reports_site_date", "site", "report_date"),
        Index("idx_reports_incident_cause_type", "incident_cause", "incident_type"),
    )

    safety_analysis: Mapped[Optional[SafetyAnalysis]] = relationship("SafetyAnalysis", back_populates="report", uselist=False, cascade="all, delete-orphan")
    evidence: Mapped[List[Evidence]] = relationship("Evidence", back_populates="report", cascade="all, delete-orphan")
    embeddings: Mapped[List[ReportEmbedding]] = relationship("ReportEmbedding", back_populates="report", cascade="all, delete-orphan")
    similar_reports_source: Mapped[List[SimilarReport]] = relationship("SimilarReport", foreign_keys="SimilarReport.report_id", back_populates="report", cascade="all, delete-orphan")
    cluster_memberships: Mapped[List[ClusterMember]] = relationship("ClusterMember", back_populates="report", cascade="all, delete-orphan")
    alerts: Mapped[List[Alert]] = relationship("Alert", back_populates="report")
    reviews: Mapped[List[Review]] = relationship("Review", back_populates="report")
