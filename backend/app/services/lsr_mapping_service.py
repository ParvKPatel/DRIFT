"""
Phase 5 — Life-Saving Rule (LSR) Mapping Service

Orchestrates LSR mapping:
1. Verifies Phase 3 Safety Analysis is complete.
2. Extracts safety facts & narrative.
3. Executes LsrEngine to evaluate the 9 official project Life-Saving Rules.
4. Persists primary & secondary LSR results to SafetyAnalysis DB record.
5. Preserves source incident_cause (source preservation).
6. Returns LsrMappingResult.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.schemas.enums import AnalysisStatus, EvidenceStatus, LifeSavingRule
from app.schemas.lsr_mapping import LsrMappingResult, BatchLsrMappingResponse
from app.services.lsr_engine import LsrEngine
from app.services.extraction_service import SafetyExtractionService
from app.utils.logging import logger


class LsrMappingService:
    """Orchestrates Phase 5 Life-Saving Rule Mapping."""

    MAPPING_VERSION = "lsr-engine-v1"

    @classmethod
    async def map_report_lsr(
        cls,
        report_id: str,
        db: AsyncSession,
        force_remap: bool = False,
    ) -> LsrMappingResult:
        """
        Maps Life-Saving Rules for a single report.
        """
        # Fetch Report
        report_stmt = select(Report).where(Report.report_id == report_id)
        report_res = await db.execute(report_stmt)
        report = report_res.scalar_one_or_none()

        if not report:
            raise ValueError(f"Report '{report_id}' not found in database.")

        # Fetch or auto-run Phase 3 SafetyAnalysis
        sa_stmt = select(SafetyAnalysis).where(SafetyAnalysis.report_id == report_id)
        sa_res = await db.execute(sa_stmt)
        sa = sa_res.scalar_one_or_none()

        if not sa or report.analysis_status != AnalysisStatus.COMPLETED:
            logger.info(f"[LsrMappingService] Report '{report_id}' not yet analyzed. Running Phase 3 extraction...")
            await SafetyExtractionService.analyze_report(report_id=report_id, db=db)
            sa_res = await db.execute(sa_stmt)
            sa = sa_res.scalar_one_or_none()

        if not sa:
            raise RuntimeError(f"Failed to load SafetyAnalysis for report '{report_id}'.")

        # Skip if already mapped (unless forced)
        if sa.primary_life_saving_rule and not force_remap:
            logger.info(f"[LsrMappingService] Report '{report_id}' already mapped to LSR. Returning stored result.")
            return cls._build_result_from_db(sa)

        logger.info(f"[LsrMappingService] Mapping LSR for report='{report_id}'")

        facts = cls._extract_facts_dict(sa)
        engine = LsrEngine()
        result: LsrMappingResult = engine.map_rules(
            report_id=report_id,
            facts=facts,
            narrative=report.narrative or "",
        )

        # Persist to DB (Preserving original report.incident_cause!)
        sa.primary_life_saving_rule = result.primary_life_saving_rule.value
        sa.secondary_life_saving_rules = json.dumps([r.value for r in result.secondary_life_saving_rules])
        sa.lsr_confidence = result.lsr_confidence
        sa.lsr_evidence = result.lsr_evidence
        sa.lsr_evidence_status = result.lsr_evidence_status
        sa.lsr_reason = result.lsr_reason
        sa.lsr_mapping_version = result.lsr_mapping_version
        # Update legacy field for backward compatibility
        sa.life_saving_rule = result.primary_life_saving_rule.value

        await db.commit()
        logger.info(f"[LsrMappingService] LSR mapped for report='{report_id}': primary='{result.primary_life_saving_rule.value}'")

        return result

    @classmethod
    async def get_lsr_result(
        cls,
        report_id: str,
        db: AsyncSession,
    ) -> Optional[LsrMappingResult]:
        """Retrieves existing LSR mapping result for a report."""
        stmt = select(SafetyAnalysis).where(SafetyAnalysis.report_id == report_id)
        res = await db.execute(stmt)
        sa = res.scalar_one_or_none()

        if not sa or not sa.primary_life_saving_rule:
            return None

        return cls._build_result_from_db(sa)

    @classmethod
    async def map_batch(
        cls,
        db: AsyncSession,
        report_ids: Optional[List[str]] = None,
        force_remap: bool = False,
        batch_size: int = 5,
    ) -> BatchLsrMappingResponse:
        """Batch LSR mapping for multiple reports."""
        if report_ids is not None:
            targets = report_ids
        else:
            stmt = select(Report.report_id).where(Report.analysis_status == AnalysisStatus.COMPLETED)
            res = await db.execute(stmt)
            targets = [r[0] for r in res.fetchall()]

        requested = len(targets)
        logger.info(f"[LsrMappingService] Batch LSR mapping requested for {requested} reports")

        semaphore = asyncio.Semaphore(batch_size)
        results: List[dict] = []
        succeeded = 0
        failed = 0
        skipped = 0

        async def _map_one(rid: str):
            nonlocal succeeded, failed, skipped
            async with semaphore:
                try:
                    res = await cls.map_report_lsr(report_id=rid, db=db, force_remap=force_remap)
                    succeeded += 1
                    results.append({
                        "report_id": rid,
                        "primary_lsr": res.primary_life_saving_rule.value,
                        "confidence": res.lsr_confidence,
                    })
                except ValueError:
                    skipped += 1
                    results.append({"report_id": rid, "status": "NOT_FOUND"})
                except Exception as exc:
                    failed += 1
                    results.append({"report_id": rid, "status": "FAILED", "error": str(exc)})

        for rid in targets:
            await _map_one(rid)

        return BatchLsrMappingResponse(
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
        }

    @staticmethod
    def _build_result_from_db(sa: SafetyAnalysis) -> LsrMappingResult:
        primary_val = sa.primary_life_saving_rule or sa.life_saving_rule or "UNKNOWN"
        try:
            primary_enum = LifeSavingRule(primary_val)
        except ValueError:
            primary_enum = LifeSavingRule.UNKNOWN

        secondaries: List[LifeSavingRule] = []
        if sa.secondary_life_saving_rules:
            try:
                raw_list = json.loads(sa.secondary_life_saving_rules)
                for s in raw_list:
                    try:
                        secondaries.append(LifeSavingRule(s))
                    except ValueError:
                        pass
            except Exception:
                pass

        return LsrMappingResult(
            report_id=sa.report_id,
            primary_life_saving_rule=primary_enum,
            secondary_life_saving_rules=secondaries,
            lsr_confidence=sa.lsr_confidence if sa.lsr_confidence is not None else 0.50,
            lsr_evidence=sa.lsr_evidence,
            lsr_evidence_status=sa.lsr_evidence_status or EvidenceStatus.UNKNOWN,
            lsr_reason=sa.lsr_reason or "Stored Life-Saving Rule mapping.",
            lsr_mapping_version=sa.lsr_mapping_version or "lsr-engine-v1",
            mapped_at=sa.updated_at,
        )
