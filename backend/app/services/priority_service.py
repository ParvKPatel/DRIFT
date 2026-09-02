"""
Phase 5 — HSE Priority Service

Orchestrates HSE Priority calculation:
1. Verifies Phase 3 Fact Extraction and Phase 4 SIF Screening are run.
2. Extracts analysis facts & SIF signals from SafetyAnalysis DB record.
3. Executes HsePriorityEngine to compute 0-100 priority_score & PriorityLevel.
4. Persists priority score, level, override, and reason codes to DB.
5. Returns PriorityResult.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.schemas.enums import AnalysisStatus, ScreeningStatus, PriorityLevel
from app.schemas.priority_engine import PriorityResult, BatchPriorityResponse
from app.services.priority_engine import HsePriorityEngine
from app.services.sif_screening_service import SifScreeningService
from app.utils.logging import logger


class PriorityService:
    """Orchestrates Phase 5 HSE Priority calculation & persistence."""

    PRIORITY_VERSION = "priority-engine-v1"

    @classmethod
    async def calculate_priority(
        cls,
        report_id: str,
        db: AsyncSession,
        force_recalculate: bool = False,
    ) -> PriorityResult:
        """
        Calculates HSE priority for a single report.
        """
        # Fetch Report
        report_stmt = select(Report).where(Report.report_id == report_id)
        report_res = await db.execute(report_stmt)
        report = report_res.scalar_one_or_none()

        if not report:
            raise ValueError(f"Report '{report_id}' not found in database.")

        # Fetch or auto-run Phase 4 SIF Screening
        sa_stmt = select(SafetyAnalysis).where(SafetyAnalysis.report_id == report_id)
        sa_res = await db.execute(sa_stmt)
        sa = sa_res.scalar_one_or_none()

        if not sa or sa.screening_status != ScreeningStatus.SCREENED:
            logger.info(f"[PriorityService] Report '{report_id}' not yet SIF screened. Running SIF screening first...")
            await SifScreeningService.screen_report(report_id=report_id, db=db)
            sa_res = await db.execute(sa_stmt)
            sa = sa_res.scalar_one_or_none()

        if not sa:
            raise RuntimeError(f"Failed to load SafetyAnalysis for report '{report_id}'.")

        # Skip if already calculated (unless forced)
        if sa.priority_score is not None and not force_recalculate:
            logger.info(f"[PriorityService] Report '{report_id}' already has priority score. Returning stored result.")
            return cls._build_result_from_db(sa)

        logger.info(f"[PriorityService] Calculating HSE priority for report='{report_id}'")

        facts = cls._extract_facts_dict(sa)
        engine = HsePriorityEngine()
        result: PriorityResult = engine.calculate_priority(report_id=report_id, safety_analysis_facts=facts)

        # Persist to DB
        now = datetime.now(timezone.utc)
        sa.sif_evidence_score = next((c.score for c in result.components if c.name == "sif_evidence_score"), 0.5)
        sa.barrier_score = next((c.score for c in result.components if c.name == "barrier_score"), 0.5)
        sa.priority_score = result.priority_score
        sa.priority_level = result.priority_level
        sa.priority_reason_codes = json.dumps(result.priority_reason_codes)
        sa.priority_override = result.priority_override
        sa.priority_version = result.priority_version
        sa.priority_calculated_at = now

        await db.commit()
        logger.info(
            f"[PriorityService] Priority calculated for report='{report_id}': "
            f"score={result.priority_score} level={result.priority_level.value} override={result.priority_override}"
        )

        return result

    @classmethod
    async def get_priority_result(
        cls,
        report_id: str,
        db: AsyncSession,
    ) -> Optional[PriorityResult]:
        """Retrieves existing priority result for a report."""
        stmt = select(SafetyAnalysis).where(SafetyAnalysis.report_id == report_id)
        res = await db.execute(stmt)
        sa = res.scalar_one_or_none()

        if not sa or sa.priority_score is None:
            return None

        return cls._build_result_from_db(sa)

    @classmethod
    async def calculate_batch(
        cls,
        db: AsyncSession,
        report_ids: Optional[List[str]] = None,
        force_recalculate: bool = False,
        batch_size: int = 5,
    ) -> BatchPriorityResponse:
        """Batch priority calculation for multiple reports."""
        if report_ids is not None:
            targets = report_ids
        else:
            stmt = select(Report.report_id).where(Report.analysis_status == AnalysisStatus.COMPLETED)
            res = await db.execute(stmt)
            targets = [r[0] for r in res.fetchall()]

        requested = len(targets)
        logger.info(f"[PriorityService] Batch priority calculation requested for {requested} reports")

        semaphore = asyncio.Semaphore(batch_size)
        results: List[dict] = []
        succeeded = 0
        failed = 0
        skipped = 0

        async def _calc_one(rid: str):
            nonlocal succeeded, failed, skipped
            async with semaphore:
                try:
                    res = await cls.calculate_priority(report_id=rid, db=db, force_recalculate=force_recalculate)
                    succeeded += 1
                    results.append({
                        "report_id": rid,
                        "priority_score": res.priority_score,
                        "priority_level": res.priority_level.value,
                        "override": res.priority_override,
                    })
                except ValueError:
                    skipped += 1
                    results.append({"report_id": rid, "status": "NOT_FOUND"})
                except Exception as exc:
                    failed += 1
                    results.append({"report_id": rid, "status": "FAILED", "error": str(exc)})

        for rid in targets:
            await _calc_one(rid)

        return BatchPriorityResponse(
            requested=requested,
            processed=succeeded + failed,
            succeeded=succeeded,
            failed=failed,
            skipped=skipped,
            results=results,
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_facts_dict(sa: SafetyAnalysis) -> Dict[str, Any]:
        rule_ids = []
        if sa.rule_ids_triggered:
            try:
                rule_ids = json.loads(sa.rule_ids_triggered)
            except Exception:
                pass

        return {
            "sif_fpi_potential": sa.sif_fpi_potential,
            "sif_confidence": sa.sif_confidence,
            "barrier_condition": sa.barrier_condition,
            "rule_ids_triggered": rule_ids,
            "exposure": sa.exposure,
            "hazard": sa.hazard,
            "hazard_confidence": sa.hazard_confidence,
            "primary_life_saving_rule": sa.primary_life_saving_rule or sa.life_saving_rule,
        }

    @classmethod
    def _build_result_from_db(cls, sa: SafetyAnalysis) -> PriorityResult:
        reason_codes = []
        if sa.priority_reason_codes:
            try:
                reason_codes = json.loads(sa.priority_reason_codes)
            except Exception:
                pass

        engine = HsePriorityEngine()
        facts = cls._extract_facts_dict(sa)
        res = engine.calculate_priority(sa.report_id, facts)
        
        # Override with exact stored scores
        res.priority_score = sa.priority_score if sa.priority_score is not None else res.priority_score
        res.priority_level = sa.priority_level or res.priority_level
        res.priority_override = sa.priority_override if sa.priority_override is not None else res.priority_override
        if reason_codes:
            res.priority_reason_codes = reason_codes
        return res
