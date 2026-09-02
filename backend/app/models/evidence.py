from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.schemas.enums import EvidenceStatus


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), index=True, nullable=False)
    analysis_id = Column(Integer, ForeignKey("safety_analysis.id", ondelete="CASCADE"), nullable=True)
    
    field_name = Column(String(100), nullable=False)  # hazard, energy_source, exposure, barrier, etc.
    evidence_text = Column(Text, nullable=False)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    evidence_status = Column(SQLEnum(EvidenceStatus, name="evidence_status_enum"), default=EvidenceStatus.UNKNOWN, nullable=False)
    confidence = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    report = relationship("Report", back_populates="evidence")
    safety_analysis = relationship("SafetyAnalysis", back_populates="evidence_items")
