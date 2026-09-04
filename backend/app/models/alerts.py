from __future__ import annotations
from typing import Optional, List, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.schemas.enums import AlertType, PriorityLevel

if TYPE_CHECKING:
    from app.models.reports import Report
    from app.models.clusters import Cluster
    from app.models.reviews import Review


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    alert_type: Mapped[AlertType] = mapped_column(SQLEnum(AlertType, name="alert_type_enum"), nullable=False)
    
    report_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("reports.report_id", ondelete="SET NULL"), nullable=True)
    cluster_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True)
    
    score: Mapped[float] = mapped_column(Float, nullable=False)
    priority: Mapped[PriorityLevel] = mapped_column(SQLEnum(PriorityLevel, name="priority_level_enum"), default=PriorityLevel.UNCERTAIN, nullable=False)
    
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_report_ids: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="OPEN", index=True, nullable=False)  # OPEN, IN_REVIEW, RESOLVED, DISMISSED
    reviewer_decision: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reviewer_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    report: Mapped[Optional[Report]] = relationship("Report", back_populates="alerts")
    cluster: Mapped[Optional[Cluster]] = relationship("Cluster", back_populates="alerts")
    reviews: Mapped[List[Review]] = relationship("Review", back_populates="alert")
