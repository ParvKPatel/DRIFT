"""
Phase 6 — Similar Report Retrieval Service

Orchestrates similarity search and caching for report-to-report relationships.
Provides GET /api/v1/reports/{report_id}/similar endpoint logic.
"""

import json
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.models.embeddings import ReportEmbedding
from app.models.similar_reports import SimilarReport
from app.schemas.similarity_schemas import SimilarReportResponse, SimilarReportItem, SharedMechanismDetails
from app.services.embedding_provider import EmbeddingFactory
from app.services.semantic_representation import SemanticRepresentationService
from app.services.similarity_engine import SimilarityEngine
from app.utils.logging import logger


class SimilarityService:
    """Retrieves top-K similar reports and maintains similarity relationships."""

    @classmethod
    async def get_similar_reports(
        cls,
        report_id: str,
        db: AsyncSession,
        top_k: int = 5,
        min_threshold: Optional[float] = None,
    ) -> SimilarReportResponse:
        """
        Retrieves top K similar reports for a target report.
        Generates canonical embeddings dynamically if not yet calculated.
        """
        threshold = min_threshold if min_threshold is not None else settings.SIMILARITY_MIN_THRESHOLD

        # Fetch Target Report & Safety Analysis
        stmt = select(Report).options(selectinload(Report.safety_analysis)).where(Report.report_id == report_id)
        res = await db.execute(stmt)
        target_report = res.scalar_one_or_none()

        if not target_report:
            raise ValueError(f"Report '{report_id}' not found.")

        # Ensure target embedding exists
        target_vec, target_text = await cls._ensure_report_embedding(target_report, target_report.safety_analysis, db)

        # Fetch all candidate reports
        cand_stmt = select(Report).options(selectinload(Report.safety_analysis)).where(Report.report_id != report_id)
        cand_res = await db.execute(cand_stmt)
        candidates = cand_res.scalars().all()

        if not candidates:
            return SimilarReportResponse(
                target_report_id=report_id,
                total_found=0,
                similar_reports=[],
            )

        items: List[SimilarReportItem] = []

        for cand in candidates:
            cand_vec, _ = await cls._ensure_report_embedding(cand, cand.safety_analysis, db)

            sim_score, details = SimilarityEngine.calculate_hybrid_similarity(
                r1=target_report,
                sa1=target_report.safety_analysis,
                v1=target_vec,
                r2=cand,
                sa2=cand.safety_analysis,
                v2=cand_vec,
            )

            if sim_score >= threshold:
                band = SimilarityEngine.map_similarity_band(sim_score)
                sa = cand.safety_analysis
                item = SimilarReportItem(
                    report_id=cand.report_id,
                    report_date=cand.report_date,
                    site=cand.site,
                    functional_location=cand.functional_location,
                    narrative_snippet=(cand.narrative or "")[:150],
                    fixed_short_description=cand.fixed_short_description,
                    sif_fpi_potential=sa.sif_fpi_potential if sa else None,
                    primary_life_saving_rule=sa.primary_life_saving_rule if sa else None,
                    priority_level=sa.priority_level if sa else None,
                    similarity_score=sim_score,
                    similarity_band=band,
                    shared_details=details,
                )
                items.append(item)

        # Sort by similarity score descending
        items.sort(key=lambda x: x.similarity_score, reverse=True)
        items = items[:top_k]

        return SimilarReportResponse(
            target_report_id=report_id,
            total_found=len(items),
            similar_reports=items,
        )

    @classmethod
    async def _ensure_report_embedding(
        cls,
        report: Report,
        sa: Optional[SafetyAnalysis],
        db: AsyncSession,
    ) -> tuple[List[float], str]:
        """Loads existing embedding or generates & persists new embedding vector."""
        stmt = select(ReportEmbedding).where(ReportEmbedding.report_id == report.report_id)
        res = await db.execute(stmt)
        emb = res.scalar_one_or_none()

        if emb and emb.embedding is not None:
            # Handle JSON vector or Vector instance
            emb_val: Any = emb.embedding
            vec = emb_val if isinstance(emb_val, list) else list(emb_val)
            return vec, emb.canonical_text or ""

        # Build canonical text & embedding vector
        canonical_text = SemanticRepresentationService.build_canonical_text(report, sa)
        provider = EmbeddingFactory.get_provider()
        vec = provider.embed_text(canonical_text)

        # Persist embedding to DB
        if not emb:
            emb = ReportEmbedding(
                report_id=report.report_id,
                embedding=vec,
                canonical_text=canonical_text,
                model_name=settings.EMBEDDING_MODEL,
                embedding_dimension=len(vec),
                representation_version="v1",
            )
            db.add(emb)
        else:
            emb.embedding = vec
            emb.canonical_text = canonical_text

        await db.commit()
        return vec, canonical_text
