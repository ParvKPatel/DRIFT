from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.schemas.enums import ReviewStatus, ReviewDecision

if TYPE_CHECKING:
    from app.models.reports import Report
    from app.models.alerts import Alert


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False, index=True)
    alert_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True)

    reviewer_id: Mapped[str] = mapped_column(String(100), default="HSE Reviewer #1", nullable=False)  # User ID or username
    review_status: Mapped[ReviewStatus] = mapped_column(
        SQLEnum(ReviewStatus, name="review_status_enum", create_constraint=False),
        default=ReviewStatus.REVIEWED,
        nullable=False,
        index=True
    )
    review_decision: Mapped[ReviewDecision] = mapped_column(
        SQLEnum(ReviewDecision, name="review_decision_enum", create_constraint=False),
        nullable=False,
        index=True
    )

    # Preserved Original AI Assessment
    original_ai_sif_potential: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    original_ai_lsr: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    original_ai_priority: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Final Human-Reviewed Assessment
    final_sif_potential: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    final_lsr: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    final_priority: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Reviewer Rationale & Audit Details
    reviewer_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    missing_information_fields: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-serialized list of missing field names

    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    report: Mapped[Optional[Report]] = relationship("Report", back_populates="reviews")
    alert: Mapped[Optional[Alert]] = relationship("Alert", back_populates="reviews")
