from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.schemas.enums import EvidenceStatus

if TYPE_CHECKING:
    from app.models.reports import Report
    from app.models.safety_analysis import SafetyAnalysis


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), index=True, nullable=False)
    analysis_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("safety_analysis.id", ondelete="CASCADE"), nullable=True)
    
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)  # hazard, energy_source, exposure, barrier, etc.
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    start_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evidence_status: Mapped[EvidenceStatus] = mapped_column(SQLEnum(EvidenceStatus, name="evidence_status_enum"), default=EvidenceStatus.UNKNOWN, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    report: Mapped[Optional[Report]] = relationship("Report", back_populates="evidence")
    safety_analysis: Mapped[Optional[SafetyAnalysis]] = relationship("SafetyAnalysis", back_populates="evidence_items")
