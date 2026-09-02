"""
Phase 5 — Full Intelligence Pipeline Orchestrator Service

Provides a unified pipeline function that runs all phases in sequence for a report:
    Phase 3: Safety Fact Extraction
        ↓
    Phase 4: SIF / FPI Screening
        ↓
    Phase 5: Life-Saving Rule Mapping
        ↓
    Phase 5: HSE Priority Engine Calculation

Returns a FullIntelligenceResult payload.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.priority_engine import FullIntelligenceResult
from app.services.extraction_service import SafetyExtractionService
from app.services.sif_screening_service import SifScreeningService
from app.services.lsr_mapping_service import LsrMappingService
from app.services.priority_service import PriorityService
from app.utils.logging import logger


class IntelligenceService:
    """Unified pipeline orchestrator for OIL SENTINEL Report Intelligence."""

    @classmethod
    async def process_full_intelligence(
        cls,
        report_id: str,
        db: AsyncSession,
        force_reanalyze: bool = False,
    ) -> FullIntelligenceResult:
        """
        Executes full intelligence pipeline for a single report:
        1. Phase 3 Safety Fact Extraction
        2. Phase 4 SIF Screening
        3. Phase 5 LSR Mapping
        4. Phase 5 Priority Calculation
        Returns combined FullIntelligenceResult.
        """
        logger.info(f"[IntelligenceService] Running full pipeline for report='{report_id}' (force={force_reanalyze})")

        # 1. Phase 3 Fact Extraction
        extraction = await SafetyExtractionService.analyze_report(
            report_id=report_id,
            db=db,
            force_reanalyze=force_reanalyze,
        )

        # 2. Phase 4 SIF Screening
        sif = await SifScreeningService.screen_report(
            report_id=report_id,
            db=db,
            force_rescreen=force_reanalyze,
        )

        # 3. Phase 5 LSR Mapping
        lsr = await LsrMappingService.map_report_lsr(
            report_id=report_id,
            db=db,
            force_remap=force_reanalyze,
        )

        # 4. Phase 5 Priority Calculation
        priority = await PriorityService.calculate_priority(
            report_id=report_id,
            db=db,
            force_recalculate=force_reanalyze,
        )

        return FullIntelligenceResult(
            report_id=report_id,
            extraction=extraction,
            sif_screening=sif,
            lsr_mapping=lsr,
            priority=priority,
        )
