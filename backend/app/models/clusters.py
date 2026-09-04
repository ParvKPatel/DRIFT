from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey, UniqueConstraint, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.schemas.enums import EscalationBand

if TYPE_CHECKING:
    from app.models.reports import Report
    from app.models.alerts import Alert


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    cluster_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    common_mechanism: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    common_asset: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    common_hazard: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    common_activity: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    common_equipment: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    common_barrier: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    common_lsr: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    recurrence_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    escalation_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    escalation_band: Mapped[Optional[EscalationBand]] = mapped_column(SQLEnum(EscalationBand, name="escalation_band_enum", create_constraint=False), default=EscalationBand.LOW, nullable=True)
    systemic_pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    members: Mapped[List[ClusterMember]] = relationship("ClusterMember", back_populates="cluster", cascade="all, delete-orphan")
    alerts: Mapped[List[Alert]] = relationship("Alert", back_populates="cluster")


class ClusterMember(Base):
    __tablename__ = "cluster_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    cluster_id: Mapped[int] = mapped_column(Integer, ForeignKey("clusters.id", ondelete="CASCADE"), index=True, nullable=False)
    report_id: Mapped[str] = mapped_column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), index=True, nullable=False)
    
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("cluster_id", "report_id", name="uq_cluster_member"),
    )

    cluster: Mapped[Optional[Cluster]] = relationship("Cluster", back_populates="members")
    report: Mapped[Optional[Report]] = relationship("Report", back_populates="cluster_memberships")
