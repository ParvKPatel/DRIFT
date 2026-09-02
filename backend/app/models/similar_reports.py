from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.database import Base


class SimilarReport(Base):
    __tablename__ = "similar_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), index=True, nullable=False)
    similar_report_id = Column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), index=True, nullable=False)
    
    similarity_score = Column(Float, nullable=False)
    explanation_json = Column(Text, nullable=True)  # JSON-serialized explanation payload
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("report_id", "similar_report_id", name="uq_similar_report_pair"),
    )

    report = relationship("Report", foreign_keys=[report_id], back_populates="similar_reports_source")
    similar_report = relationship("Report", foreign_keys=[similar_report_id])
