from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.schemas.enums import ReviewStatus, ReviewDecision


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True)

    reviewer_id = Column(String(100), default="HSE Reviewer #1", nullable=False)  # User ID or username
    review_status = Column(
        SQLEnum(ReviewStatus, name="review_status_enum", create_constraint=False),
        default=ReviewStatus.REVIEWED,
        nullable=False,
        index=True
    )
    review_decision = Column(
        SQLEnum(ReviewDecision, name="review_decision_enum", create_constraint=False),
        nullable=False,
        index=True
    )

    # Preserved Original AI Assessment
    original_ai_sif_potential = Column(String(50), nullable=True)
    original_ai_lsr = Column(String(100), nullable=True)
    original_ai_priority = Column(String(100), nullable=True)

    # Final Human-Reviewed Assessment
    final_sif_potential = Column(String(50), nullable=True)
    final_lsr = Column(String(100), nullable=True)
    final_priority = Column(String(100), nullable=True)

    # Reviewer Rationale & Audit Details
    reviewer_comment = Column(Text, nullable=True)
    rejection_reason = Column(String(100), nullable=True)
    missing_information_fields = Column(Text, nullable=True)  # JSON-serialized list of missing field names

    reviewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    report = relationship("Report", back_populates="reviews")
    alert = relationship("Alert", back_populates="reviews")
