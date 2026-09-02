from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, UniqueConstraint, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.schemas.enums import EscalationBand


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cluster_name = Column(String(200), nullable=False)
    
    common_mechanism = Column(Text, nullable=True)
    common_asset = Column(String(150), nullable=True)
    common_hazard = Column(String(200), nullable=True)
    common_activity = Column(String(200), nullable=True)
    common_equipment = Column(String(150), nullable=True)
    common_barrier = Column(String(150), nullable=True)
    common_lsr = Column(String(100), nullable=True)
    
    recurrence_count = Column(Integer, default=1, nullable=False)
    escalation_score = Column(Float, default=0.0, nullable=False)
    escalation_band = Column(SQLEnum(EscalationBand, name="escalation_band_enum", create_constraint=False), default=EscalationBand.LOW, nullable=True)
    systemic_pattern = Column(Text, nullable=True)
    
    first_seen = Column(DateTime(timezone=True), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    members = relationship("ClusterMember", back_populates="cluster", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="cluster")


class ClusterMember(Base):
    __tablename__ = "cluster_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="CASCADE"), index=True, nullable=False)
    report_id = Column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), index=True, nullable=False)
    
    similarity_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("cluster_id", "report_id", name="uq_cluster_member"),
    )

    cluster = relationship("Cluster", back_populates="members")
    report = relationship("Report", back_populates="cluster_memberships")
