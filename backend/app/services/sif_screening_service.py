"""
Phase 4 — SIF Screening Service

Coordinates SIF/FPI screening execution for safety reports:
1. Verifies Phase 3 safety fact extraction is COMPLETED.
2. Fetches structured safety facts from SafetyAnalysis DB record.
3. Executes deterministic SafetyRuleEngine.
4. Persists SIF screening results, rule triggers, and transparent signals to DB.
5. Returns SifScreeningResult.

Reuses existing database models & columns — does NOT modify source report fields.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.schemas.enums import AnalysisStatus, ScreeningStatus
from app.schemas.sif_screening import (
    SifScreeningResult,
    BatchSifScreeningResponse,
    ScreeningSignals,
)
from app.services.sif_rule_engine import SafetyRuleEngine
from app.services.extraction_service import SafetyExtractionService
from app.utils.logging import logger


class SifScreeningService:
    """Orchestrates Phase 4 SIF/FPI screening pipeline."""

    SCREENING_VERSION = "sif-engine-v1"

    @classmethod
    async def screen_report(
        cls,
        report_id: str,
        db: AsyncSession,
        force_rescreen: bool = False,
    ) -> SifScreeningResult:
        """
        Screens a single report for SIF/FPI precursor potential.

        Steps:
        1. Fetch report & existing SafetyAnalysis (raises 404 if report missing).
        2. Ensure Phase 3 extraction is COMPLETED (auto-runs extraction if NOT_ANALYZED).
        3. Skip if already SCREENED (unless force_rescreen=True).
        4. Extract safety facts dict from SafetyAnalysis model.
        5. Run deterministic SafetyRuleEngine.
        6. Persist screening results to SafetyAnalysis DB record.
        7. Return SifScreeningResult.
        """
        # 1. Fetch Report
        report_stmt = select(Report).where(Report.report_id == report_id)
        report_res = await db.execute(report_stmt)
        report = report_res.scalar_one_or_none()

        if not report:
            raise ValueError(f"Report '{report_id}' not found in database.")

        # 2. Fetch or auto-run Phase 3 SafetyAnalysis
        sa_stmt = select(SafetyAnalysis).where(SafetyAnalysis.report_id == report_id)
        sa_res = await db.execute(sa_stmt)
        sa = sa_res.scalar_one_or_none()

        if not sa or report.analysis_status != AnalysisStatus.COMPLETED:
            logger.info(
                f"[SifScreeningService] Report '{report_id}' not yet analyzed. "
                "Triggering Phase 3 extraction first..."
            )
            await SafetyExtractionService.analyze_report(report_id=report_id, db=db)
            sa_res = await db.execute(sa_stmt)
            sa = sa_res.scalar_one_or_none()

        if not sa:
            raise RuntimeError(f"Failed to load or generate SafetyAnalysis for report '{report_id}'.")

        # 3. Skip if already screened (unless forced)
        if sa.screening_status == ScreeningStatus.SCREENED and not force_rescreen:
            logger.info(
                f"[SifScreeningService] Report '{report_id}' already SCREENED. "
                "Returning stored screening result. Pass force_rescreen=True to re-screen."
            )
            return cls._build_result_from_db(sa)

        # Update status to SCREENING
        sa.screening_status = ScreeningStatus.SCREENING
        await db.commit()

        logger.info(f"[SifScreeningService] Starting SIF screening for report='{report_id}'")

        try:
            # 4. Extract safety facts dict
            facts = cls._extract_facts_dict(sa)

            # 5. Run Rule Engine
            engine = SafetyRuleEngine()
            result: SifScreeningResult = engine.screen(
                report_id=report_id,
                safety_facts=facts,
                narrative=report.narrative or "",
            )

            # 6. Persist screening result to DB
            now = datetime.now(timezone.utc)
            sa.sif_fpi_potential = result.sif_fpi_potential
            sa.sif_confidence = result.sif_confidence
            sa.screening_status = ScreeningStatus.SCREENED
            sa.screening_reason = result.screening_reason
            sa.reason_code = result.reason_codes[0] if result.reason_codes else "SIF-NONE"
            sa.rule_ids_triggered = json.dumps(result.rule_ids_triggered)
            sa.mechanism_signal = result.signals.mechanism_signal
            sa.exposure_signal = result.signals.exposure_signal
            sa.consequence_signal = result.signals.consequence_signal
            sa.sif_evidence_score = result.signals.evidence_signal
            sa.barrier_score = result.signals.barrier_signal
            sa.screening_version = result.screening_version
            sa.screened_at = now
            sa.review_required = result.review_required
            sa.review_reason = result.review_reason

            await db.commit()
            logger.info(
                f"[SifScreeningService] SIF screening completed for report='{report_id}': "
                f"decision={result.sif_fpi_potential.value} confidence={result.sif_confidence} "
                f"rules_triggered={result.rule_ids_triggered}"
            )

            return result

        except Exception as exc:
            logger.error(f"[SifScreeningService] SIF screening FAILED for report='{report_id}': {exc}", exc_info=True)
            sa.screening_status = ScreeningStatus.SCREENING_FAILED
            await db.commit()
            raise

    @classmethod
    async def get_screening_result(
        cls,
        report_id: str,
        db: AsyncSession,
    ) -> Optional[SifScreeningResult]:
        """Retrieves current SIF screening result for a report without re-running."""
        stmt = select(SafetyAnalysis).where(SafetyAnalysis.report_id == report_id)
        res = await db.execute(stmt)
        sa = res.scalar_one_or_none()

        if not sa or sa.screening_status != ScreeningStatus.SCREENED:
            return None

        return cls._build_result_from_db(sa)

    @classmethod
    async def screen_batch(
        cls,
        db: AsyncSession,
        report_ids: Optional[List[str]] = None,
        force_rescreen: bool = False,
        batch_size: int = 5,
    ) -> BatchSifScreeningResponse:
        """
        Screens a batch of reports for SIF/FPI potential.
        If report_ids is None, screens all COMPLETED reports that are NOT_SCREENED.
        Runs 100% locally without external AI API calls.
        """
        if report_ids is not None:
            targets = report_ids
        else:
            stmt = select(Report.report_id).where(
                Report.analysis_status == AnalysisStatus.COMPLETED
            )
            res = await db.execute(stmt)
            targets = [r[0] for r in res.fetchall()]

        requested = len(targets)
        logger.info(f"[SifScreeningService] Batch SIF screening requested for {requested} reports")

        semaphore = asyncio.Semaphore(batch_size)
        results: List[dict] = []
        succeeded = 0
        failed = 0
        skipped = 0

        async def _screen_one(rid: str):
            nonlocal succeeded, failed, skipped
            async with semaphore:
                try:
                    res = await cls.screen_report(report_id=rid, db=db, force_rescreen=force_rescreen)
                    succeeded += 1
                    results.append({
                        "report_id": rid,
                        "sif_fpi_potential": res.sif_fpi_potential.value,
                        "confidence": res.sif_confidence,
                        "rules_triggered": res.rule_ids_triggered,
                        "review_required": res.review_required,
                    })
                except ValueError:
                    skipped += 1
                    results.append({"report_id": rid, "status": "NOT_FOUND"})
                except Exception as exc:
                    failed += 1
                    results.append({"report_id": rid, "status": "FAILED", "error": str(exc)})

        await asyncio.gather(*[_screen_one(rid) for rid in targets])

        return BatchSifScreeningResponse(
            requested=requested,
            processed=succeeded + failed,
            succeeded=succeeded,
            failed=failed,
            skipped=skipped,
            results=results,
        )

    # ── Private Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _extract_facts_dict(sa: SafetyAnalysis) -> Dict[str, Any]:
        """Extracts facts dictionary from SafetyAnalysis SQLAlchemy model."""
        return {
            "activity": sa.activity,
            "equipment": sa.equipment,
            "hazard": sa.hazard,
            "energy_source": sa.energy_source,
            "exposure": sa.exposure,
            "exposure_location": sa.exposure_location,
            "barrier": sa.barrier,
            "barrier_condition": sa.barrier_condition,
            "potential_consequence": sa.potential_consequence,

            # Evidence text
            "hazard_evidence": sa.hazard_evidence_status.value if sa.hazard_evidence_status else None,
            "exposure_evidence": sa.exposure_evidence,
            "exposure_location_evidence": sa.exposure_location_evidence,
            "barrier_evidence": sa.barrier_evidence,
            "potential_consequence_evidence": sa.potential_consequence_evidence,

            # Evidence status & confidence
            "activity_confidence": sa.activity_confidence,
            "equipment_confidence": sa.equipment_confidence,
            "hazard_confidence": sa.hazard_confidence,
            "energy_source_confidence": sa.energy_source_confidence,
            "exposure_confidence": sa.exposure_confidence,
            "exposure_evidence_status": sa.exposure_evidence_status,
            "exposure_location_confidence": sa.exposure_location_confidence,
            "barrier_confidence": sa.barrier_confidence,
            "barrier_condition_confidence": sa.barrier_condition_confidence,
            "potential_consequence_confidence": sa.potential_consequence_confidence,
        }

    @staticmethod
    def _build_result_from_db(sa: SafetyAnalysis) -> SifScreeningResult:
        """Reconstructs SifScreeningResult from SafetyAnalysis DB record."""
        rule_ids = []
        if sa.rule_ids_triggered:
            try:
                rule_ids = json.loads(sa.rule_ids_triggered)
            except Exception:
                rule_ids = [r.strip() for r in sa.rule_ids_triggered.split(",") if r.strip()]

        reason_codes = [sa.reason_code] if sa.reason_code else []

        signals = ScreeningSignals(
            mechanism_signal=sa.mechanism_signal if sa.mechanism_signal is not None else 0.50,
            exposure_signal=sa.exposure_signal if sa.exposure_signal is not None else 0.50,
            barrier_signal=sa.barrier_score if sa.barrier_score is not None else 0.50,
            consequence_signal=sa.consequence_signal if sa.consequence_signal is not None else 0.50,
            evidence_signal=sa.sif_evidence_score if sa.sif_evidence_score is not None else 0.50,
        )

        return SifScreeningResult(
            report_id=sa.report_id,
            sif_fpi_potential=sa.sif_fpi_potential or SifDecision.UNCERTAIN,
            sif_confidence=sa.sif_confidence if sa.sif_confidence is not None else 0.50,
            screening_status=sa.screening_status or ScreeningStatus.SCREENED,
            screening_reason=sa.screening_reason or "Stored screening result.",
            reason_codes=reason_codes,
            rule_ids_triggered=rule_ids,
            contributing_factors=[],
            signals=signals,
            rules_triggered=[],
            screening_version=sa.screening_version or "sif-engine-v1",
            screened_at=sa.screened_at,
            review_required=sa.review_required or False,
            review_reason=sa.review_reason,
        )
