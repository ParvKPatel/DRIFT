from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.reports import Report


class SimilarReport(Base):
    __tablename__ = "similar_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), index=True, nullable=False)
    similar_report_id: Mapped[str] = mapped_column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), index=True, nullable=False)
    
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-serialized explanation payload
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("report_id", "similar_report_id", name="uq_similar_report_pair"),
    )

    report: Mapped[Optional[Report]] = relationship("Report", foreign_keys=[report_id], back_populates="similar_reports_source")
    similar_report: Mapped[Optional[Report]] = relationship("Report", foreign_keys=[similar_report_id])
