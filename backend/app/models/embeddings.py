from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base

try:
    from pgvector.sqlalchemy import Vector  # type: ignore
    HAS_PGVECTOR = True
except ImportError:
    Vector = None
    HAS_PGVECTOR = False


class ReportEmbedding(Base):
    __tablename__ = "report_embeddings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Use Vector if pgvector is available, otherwise fallback to JSON
    if HAS_PGVECTOR and Vector is not None:
        embedding = Column(Vector(768), nullable=True)
    else:
        embedding = Column(JSON, nullable=True)

    canonical_text = Column(Text, nullable=True)
    model_name = Column(String(100), default="sentence-transformers/all-mpnet-base-v2", nullable=False)
    embedding_dimension = Column(Integer, default=768, nullable=False)
    representation_version = Column(String(50), default="v1", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    report = relationship("Report", back_populates="embeddings")
