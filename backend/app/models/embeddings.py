from __future__ import annotations
from typing import Optional, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

try:
    from pgvector.sqlalchemy import Vector  # type: ignore
    HAS_PGVECTOR = True
except ImportError:
    Vector = None
    HAS_PGVECTOR = False

if TYPE_CHECKING:
    from app.models.reports import Report


class ReportEmbedding(Base):
    __tablename__ = "report_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(100), ForeignKey("reports.report_id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Use Vector if pgvector is available, otherwise fallback to JSON
    if HAS_PGVECTOR and Vector is not None:
        embedding: Mapped[Optional[Any]] = mapped_column(Vector(768), nullable=True)
    else:
        embedding: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    canonical_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), default="sentence-transformers/all-mpnet-base-v2", nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, default=768, nullable=False)
    representation_version: Mapped[str] = mapped_column(String(50), default="v1", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    report: Mapped[Optional[Report]] = relationship("Report", back_populates="embeddings")
