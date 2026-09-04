"""
Phase 3 — Safety Extraction Service

Orchestrates the full analysis pipeline:
    Report → AI Provider → Structured JSON → Pydantic Validation
    → Evidence Spans → SafetyAnalysis DB record → Evidence DB records

The AI provider NEVER writes to the database.
This service is the only persistence layer for analysis results.

Key design rules:
- Source fields on Report are NEVER modified (immutable)
- analysis_status on Report is updated to track pipeline state
- Evidence offsets are calculated against the ORIGINAL verbatim narrative string
- Mock analyses are clearly flagged is_mock=True
- Analyses carry version/model/provider metadata for future comparison
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.models.evidence import Evidence
from app.services.sif_rule_engine import SafetyRuleEngine
from app.services.review_service import ReviewService
from app.utils.logging import logger
from app.schemas.enums import AnalysisStatus, EvidenceStatus, BarrierCondition, EnergySource
from app.schemas.safety_extraction import (
    SafetyFactsExtractionResponse,
    FactField,
    AnalysisResultResponse,
    EvidenceItemResponse,
    BatchAnalysisResultResponse,
)
from app.utils.logging import logger
from ai.factory import get_safety_extraction_provider


# Evidence field names that map to the 9 safety facts
EVIDENCE_FIELD_NAMES = [
    "activity", "equipment", "hazard", "energy_source",
    "exposure", "exposure_location", "barrier",
    "barrier_condition", "potential_consequence",
]


class SafetyExtractionService:
    """
    Coordinates safety fact extraction from source reports.
    Does NOT expose SIF/FPI classification (Phase 4+).
    """

    ANALYSIS_VERSION = "3.0.0"

    @classmethod
    async def analyze_report(
        cls,
        report_id: str,
        db: AsyncSession,
        force_reanalyze: bool = False,
    ) -> AnalysisResultResponse:
        """
        Runs safety fact extraction for a single report.

        Steps:
        1. Fetch report from DB (404 if missing)
        2. Check if already COMPLETED (skip unless force_reanalyze)
        3. Set analysis_status = PROCESSING
        4. Call AI provider
        5. Validate structured output
        6. Calculate evidence offsets against original narrative
        7. Upsert SafetyAnalysis record
        8. Insert / replace Evidence records
        9. Update analysis_status = COMPLETED (or FAILED)
        10. Return AnalysisResultResponse
        """
        # 1. Fetch report
        stmt = select(Report).where(Report.report_id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise ValueError(f"Report '{report_id}' not found in database.")

        # 2. Skip if already completed (unless forced)
        if report.analysis_status == AnalysisStatus.COMPLETED and not force_reanalyze:
            logger.info(
                f"[ExtractionService] Report {report_id} already COMPLETED. "
                "Returning existing analysis. Pass force_reanalyze=True to re-run."
            )
            existing = await cls._build_result_from_db(report_id, db)
            if existing is not None:
                return existing

        # 3. Mark as PROCESSING
        report.analysis_status = AnalysisStatus.PROCESSING
        await db.commit()

        logger.info(f"[ExtractionService] Analysis started for report={report_id}")

        try:
            # 4. Select AI provider
            provider = get_safety_extraction_provider()
            logger.info(
                f"[ExtractionService] Provider selected: {provider.PROVIDER_NAME} "
                f"model={provider.MODEL_NAME} for report={report_id}"
            )

            # 4b. Fetch any human reviews to feed into AI context
            review = await ReviewService.get_latest_review(report_id, db)
            human_feedback = review.reviewer_comment if review and review.reviewer_comment else ""
            human_decision = ""
            if review and review.review_decision:
                human_decision = getattr(review.review_decision, "value", str(review.review_decision))

            # 5. Build context metadata for the provider prompt
            context: Dict[str, Any] = {
                "report_id": report_id,
                "incident_cause": report.incident_cause or "",
                "fixed_short_description": report.fixed_short_description or "",
                "corrective_action": report.corrective_action or "",
                "human_feedback": human_feedback,
                "human_decision": human_decision,
            }

            # 6. Call provider
            extraction: SafetyFactsExtractionResponse = await provider.extract_safety_facts(
                narrative=report.narrative,
                context=context,
            )

            logger.info(
                f"[ExtractionService] Extraction completed for report={report_id} "
                f"is_mock={extraction.is_mock}"
            )

            # 7. Upsert SafetyAnalysis record
            sa = await cls._upsert_safety_analysis(
                report_id=report_id,
                extraction=extraction,
                provider=provider,
                db=db,
            )

            # 8. Insert evidence spans
            evidence_items = await cls._upsert_evidence_items(
                report_id=report_id,
                analysis_id=sa.id,
                narrative=report.narrative,
                extraction=extraction,
                db=db,
            )

            # 8.5 Generate suggested actions
            try:
                # Helper to safely get string value from FactField
                def _val(ff):
                    v = ff.value
                    return str(v.value) if (v is not None and hasattr(v, "value")) else (str(v) if v is not None else None)

                actions, reasoning = await provider.generate_suggested_actions(
                    narrative=report.narrative,
                    hazard=_val(extraction.hazard) or "",
                    barrier_condition=_val(extraction.barrier_condition) or "",
                    life_saving_rule=sa.life_saving_rule or "",
                    previous_actions=report.corrective_action or "",
                )
                import json
                sa.suggested_actions = json.dumps(actions)
                sa.suggested_actions_reasoning = reasoning
            except Exception as e:
                logger.error(f"[ExtractionService] Failed to generate actions for report={report_id}: {e}")

            # 9. Update report analysis_status = COMPLETED
            report.analysis_status = AnalysisStatus.COMPLETED
            await db.commit()

            logger.info(
                f"[ExtractionService] Analysis persisted for report={report_id} "
                f"analysis_id={sa.id} evidence_count={len(evidence_items)}"
            )

            return cls._build_result_from_extraction(
                report_id=report_id,
                extraction=extraction,
                sa=sa,
                evidence_items=evidence_items,
            )

        except Exception as exc:
            logger.error(
                f"[ExtractionService] Analysis FAILED for report={report_id}: {exc}",
                exc_info=True,
            )
            # Mark as FAILED — do not leave in PROCESSING state
            report.analysis_status = AnalysisStatus.FAILED
            await db.commit()
            raise

    @classmethod
    async def analyze_batch(
        cls,
        db: AsyncSession,
        report_ids: Optional[List[str]] = None,
        force_reanalyze: bool = False,
        batch_size: int = 5,
    ) -> BatchAnalysisResultResponse:
        """
        Analyzes a batch of reports with controlled concurrency.

        If report_ids is None → all NOT_ANALYZED reports are targeted.
        Uses asyncio.Semaphore to avoid overwhelming an external AI API.
        """
        # Determine target reports
        if report_ids is not None:
            targets = report_ids
        else:
            # Fetch all NOT_ANALYZED reports
            stmt = select(Report.report_id).where(
                Report.analysis_status == AnalysisStatus.NOT_ANALYZED
            )
            result = await db.execute(stmt)
            targets = [row[0] for row in result.fetchall()]

        requested = len(targets)
        logger.info(
            f"[ExtractionService] Batch analysis requested for {requested} reports "
            f"batch_size={batch_size} force={force_reanalyze}"
        )

        semaphore = asyncio.Semaphore(batch_size)
        results: List[dict] = []
        succeeded = 0
        failed = 0
        skipped = 0

        async def _analyze_one(rid: str):
            nonlocal succeeded, failed, skipped
            async with semaphore:
                try:
                    res = await cls.analyze_report(
                        report_id=rid,
                        db=db,
                        force_reanalyze=force_reanalyze,
                    )
                    succeeded += 1
                    results.append({
                        "report_id": rid,
                        "status": "COMPLETED",
                        "is_mock": res.is_mock,
                    })
                except ValueError:
                    # Report not found
                    skipped += 1
                    results.append({"report_id": rid, "status": "NOT_FOUND"})
                except Exception as exc:
                    failed += 1
                    results.append({"report_id": rid, "status": "FAILED", "error": str(exc)})

        for rid in targets:
            await _analyze_one(rid)

        return BatchAnalysisResultResponse(
            requested=requested,
            processed=succeeded + failed,
            succeeded=succeeded,
            failed=failed,
            skipped=skipped,
            results=results,
        )

    @classmethod
    async def get_analysis_result(
        cls,
        report_id: str,
        db: AsyncSession,
    ) -> Optional[AnalysisResultResponse]:
        """Fetches existing analysis result for a report without re-running."""
        return await cls._build_result_from_db(report_id, db)

    # ── Private helpers ────────────────────────────────────────────────────

    @classmethod
    async def _upsert_safety_analysis(
        cls,
        report_id: str,
        extraction: SafetyFactsExtractionResponse,
        provider,
        db: AsyncSession,
    ) -> SafetyAnalysis:
        """Insert or update SafetyAnalysis record from extraction."""
        stmt = select(SafetyAnalysis).where(SafetyAnalysis.report_id == report_id)
        result = await db.execute(stmt)
        sa = result.scalar_one_or_none()

        # Helper to safely get string value from FactField
        def _val(ff: FactField):
            v = ff.value
            return str(v.value) if (v is not None and hasattr(v, "value")) else (str(v) if v is not None else None)

        def _ev_status(ff: FactField):
            return ff.evidence_status

        def _conf(ff: FactField):
            return ff.confidence

        now = datetime.now(timezone.utc)

        kwargs: Dict[str, Any] = dict(
            report_id=report_id,
            # 9 safety fact values
            activity=_val(extraction.activity),
            equipment=_val(extraction.equipment),
            hazard=_val(extraction.hazard),
            energy_source=extraction.energy_source.value if extraction.energy_source.value is not None else None,
            exposure=_val(extraction.exposure),
            exposure_location=_val(extraction.exposure_location),
            barrier=_val(extraction.barrier),
            barrier_condition=extraction.barrier_condition.value if extraction.barrier_condition.value is not None else None,
            potential_consequence=_val(extraction.potential_consequence),
            # Per-field evidence status / confidence
            activity_evidence_status=_ev_status(extraction.activity),
            activity_confidence=_conf(extraction.activity),
            equipment_evidence_status=_ev_status(extraction.equipment),
            equipment_confidence=_conf(extraction.equipment),
            hazard_evidence_status=_ev_status(extraction.hazard),
            hazard_confidence=_conf(extraction.hazard),
            energy_source_evidence=extraction.energy_source.evidence,
            energy_source_evidence_status=_ev_status(extraction.energy_source),
            energy_source_confidence=_conf(extraction.energy_source),
            exposure_evidence=extraction.exposure.evidence,
            exposure_evidence_status=_ev_status(extraction.exposure),
            exposure_confidence=_conf(extraction.exposure),
            exposure_location_evidence=extraction.exposure_location.evidence,
            exposure_location_evidence_status=_ev_status(extraction.exposure_location),
            exposure_location_confidence=_conf(extraction.exposure_location),
            barrier_evidence=extraction.barrier.evidence,
            barrier_evidence_status=_ev_status(extraction.barrier),
            barrier_confidence=_conf(extraction.barrier),
            barrier_condition_evidence=extraction.barrier_condition.evidence,
            barrier_condition_evidence_status=_ev_status(extraction.barrier_condition),
            barrier_condition_confidence=_conf(extraction.barrier_condition),
            potential_consequence_evidence=extraction.potential_consequence.evidence,
            potential_consequence_evidence_status=_ev_status(extraction.potential_consequence),
            potential_consequence_confidence=_conf(extraction.potential_consequence),
            # Provenance & version
            analysis_version=cls.ANALYSIS_VERSION,
            model_name=provider.MODEL_NAME,
            provider_name=provider.PROVIDER_NAME,
            analyzed_at=now,
            is_mock=extraction.is_mock,
            analysis_status=AnalysisStatus.COMPLETED,
            # legacy field (kept for schema compat)
            evidence_status=EvidenceStatus.EXPLICIT if not extraction.is_mock else EvidenceStatus.INFERRED,
        )

        if sa is None:
            sa = SafetyAnalysis(**kwargs)
            db.add(sa)
        else:
            for key, value in kwargs.items():
                setattr(sa, key, value)

        await db.flush()
        return sa

    @classmethod
    async def _upsert_evidence_items(
        cls,
        report_id: str,
        analysis_id: int,
        narrative: str,
        extraction: SafetyFactsExtractionResponse,
        db: AsyncSession,
    ) -> List[Evidence]:
        """Delete old evidence items and insert fresh ones from this extraction."""
        # Delete existing evidence for this analysis
        from sqlalchemy import delete
        await db.execute(
            delete(Evidence).where(Evidence.analysis_id == analysis_id)
        )

        evidence_list: List[Evidence] = []
        fields = {
            "activity": extraction.activity,
            "equipment": extraction.equipment,
            "hazard": extraction.hazard,
            "energy_source": extraction.energy_source,
            "exposure": extraction.exposure,
            "exposure_location": extraction.exposure_location,
            "barrier": extraction.barrier,
            "barrier_condition": extraction.barrier_condition,
            "potential_consequence": extraction.potential_consequence,
        }

        for field_name, fact in fields.items():
            if fact.evidence is None:
                continue  # No evidence text to store for UNKNOWN fields

            # Calculate offsets from original narrative
            start_offset, end_offset = _calculate_offsets(narrative, fact.evidence)

            ev = Evidence(
                report_id=report_id,
                analysis_id=analysis_id,
                field_name=field_name,
                evidence_text=fact.evidence,
                start_offset=start_offset,
                end_offset=end_offset,
                evidence_status=fact.evidence_status,
                confidence=fact.confidence,
            )
            db.add(ev)
            evidence_list.append(ev)

        await db.flush()
        logger.info(
            f"[ExtractionService] Stored {len(evidence_list)} evidence items "
            f"for report={report_id} analysis_id={analysis_id}"
        )
        return evidence_list

    @classmethod
    async def _build_result_from_db(
        cls,
        report_id: str,
        db: AsyncSession,
    ) -> Optional[AnalysisResultResponse]:
        """Build AnalysisResultResponse from existing DB records."""
        sa_stmt = select(SafetyAnalysis).where(SafetyAnalysis.report_id == report_id)
        sa_result = await db.execute(sa_stmt)
        sa: Any = sa_result.scalar_one_or_none()

        if sa is None:
            return None

        ev_stmt = select(Evidence).where(Evidence.analysis_id == sa.id)
        ev_result = await db.execute(ev_stmt)
        ev_items = ev_result.scalars().all()

        ev_by_field: Dict[str, str] = {
            str(e.field_name): str(e.evidence_text)
            for e in ev_items
            if e.field_name and e.evidence_text
        }

        def _get_ev(field_name: str, fallback: Any = None) -> Optional[str]:
            if field_name in ev_by_field:
                return ev_by_field[field_name]
            return str(fallback) if fallback is not None else None

        return AnalysisResultResponse(
            report_id=report_id,
            analysis_status=sa.analysis_status or AnalysisStatus.COMPLETED,
            analysis_version=sa.analysis_version,
            model_name=sa.model_name,
            provider_name=sa.provider_name,
            analyzed_at=sa.analyzed_at,
            is_mock=sa.is_mock or False,
            activity=sa.activity,
            activity_evidence=_get_ev("activity"),
            activity_evidence_status=sa.activity_evidence_status,
            activity_confidence=sa.activity_confidence,
            equipment=sa.equipment,
            equipment_evidence=_get_ev("equipment"),
            equipment_evidence_status=sa.equipment_evidence_status,
            equipment_confidence=sa.equipment_confidence,
            hazard=sa.hazard,
            hazard_evidence=_get_ev("hazard"),
            hazard_evidence_status=sa.hazard_evidence_status,
            hazard_confidence=sa.hazard_confidence,
            energy_source=str(sa.energy_source.value) if sa.energy_source else None,
            energy_source_evidence=_get_ev("energy_source", sa.energy_source_evidence),
            energy_source_evidence_status=sa.energy_source_evidence_status,
            energy_source_confidence=sa.energy_source_confidence,
            exposure=sa.exposure,
            exposure_evidence=_get_ev("exposure", sa.exposure_evidence),
            exposure_evidence_status=sa.exposure_evidence_status,
            exposure_confidence=sa.exposure_confidence,
            exposure_location=sa.exposure_location,
            exposure_location_evidence=_get_ev("exposure_location", sa.exposure_location_evidence),
            exposure_location_evidence_status=sa.exposure_location_evidence_status,
            exposure_location_confidence=sa.exposure_location_confidence,
            barrier=sa.barrier,
            barrier_evidence=_get_ev("barrier", sa.barrier_evidence),
            barrier_evidence_status=sa.barrier_evidence_status,
            barrier_confidence=sa.barrier_confidence,
            barrier_condition=str(sa.barrier_condition.value) if sa.barrier_condition else None,
            barrier_condition_evidence=_get_ev("barrier_condition", sa.barrier_condition_evidence),
            barrier_condition_evidence_status=sa.barrier_condition_evidence_status,
            barrier_condition_confidence=sa.barrier_condition_confidence,
            potential_consequence=sa.potential_consequence,
            potential_consequence_evidence=_get_ev("potential_consequence", sa.potential_consequence_evidence),
            potential_consequence_evidence_status=sa.potential_consequence_evidence_status,
            potential_consequence_confidence=sa.potential_consequence_confidence,
            suggested_actions=sa.suggested_actions,
            suggested_actions_reasoning=sa.suggested_actions_reasoning,
            evidence_items=[EvidenceItemResponse.model_validate(e) for e in ev_items],
        )

    @staticmethod
    def _build_result_from_extraction(
        report_id: str,
        extraction: SafetyFactsExtractionResponse,
        sa: Any,
        evidence_items: List[Evidence],
    ) -> AnalysisResultResponse:
        """Build AnalysisResultResponse directly from fresh extraction output."""
        def _val(ff: FactField):
            v = ff.value
            return str(v.value) if (v is not None and hasattr(v, "value")) else (str(v) if v is not None else None)

        return AnalysisResultResponse(
            report_id=report_id,
            analysis_status=AnalysisStatus.COMPLETED,
            analysis_version=sa.analysis_version,
            model_name=sa.model_name,
            provider_name=sa.provider_name,
            analyzed_at=sa.analyzed_at,
            is_mock=extraction.is_mock,
            activity=_val(extraction.activity),
            activity_evidence=extraction.activity.evidence,
            activity_evidence_status=extraction.activity.evidence_status,
            activity_confidence=extraction.activity.confidence,
            equipment=_val(extraction.equipment),
            equipment_evidence=extraction.equipment.evidence,
            equipment_evidence_status=extraction.equipment.evidence_status,
            equipment_confidence=extraction.equipment.confidence,
            hazard=_val(extraction.hazard),
            hazard_evidence=extraction.hazard.evidence,
            hazard_evidence_status=extraction.hazard.evidence_status,
            hazard_confidence=extraction.hazard.confidence,
            energy_source=_val(extraction.energy_source),
            energy_source_evidence=extraction.energy_source.evidence,
            energy_source_evidence_status=extraction.energy_source.evidence_status,
            energy_source_confidence=extraction.energy_source.confidence,
            exposure=_val(extraction.exposure),
            exposure_evidence=extraction.exposure.evidence,
            exposure_evidence_status=extraction.exposure.evidence_status,
            exposure_confidence=extraction.exposure.confidence,
            exposure_location=_val(extraction.exposure_location),
            exposure_location_evidence=extraction.exposure_location.evidence,
            exposure_location_evidence_status=extraction.exposure_location.evidence_status,
            exposure_location_confidence=extraction.exposure_location.confidence,
            barrier=_val(extraction.barrier),
            barrier_evidence=extraction.barrier.evidence,
            barrier_evidence_status=extraction.barrier.evidence_status,
            barrier_confidence=extraction.barrier.confidence,
            barrier_condition=_val(extraction.barrier_condition),
            barrier_condition_evidence=extraction.barrier_condition.evidence,
            barrier_condition_evidence_status=extraction.barrier_condition.evidence_status,
            barrier_condition_confidence=extraction.barrier_condition.confidence,
            potential_consequence=_val(extraction.potential_consequence),
            potential_consequence_evidence=extraction.potential_consequence.evidence,
            potential_consequence_evidence_status=extraction.potential_consequence.evidence_status,
            potential_consequence_confidence=extraction.potential_consequence.confidence,
            suggested_actions=sa.suggested_actions,
            suggested_actions_reasoning=sa.suggested_actions_reasoning,
            evidence_items=[EvidenceItemResponse.model_validate(e) for e in evidence_items],
        )


def _calculate_offsets(
    narrative: str, evidence_text: str
) -> Tuple[Optional[int], Optional[int]]:
    """
    Safely calculate start/end character offsets of evidence_text within the
    original narrative string (case-insensitive search, original-case offsets).

    Returns (None, None) if:
    - evidence_text is None or empty
    - evidence_text is not found in narrative
    - narrative is None or empty
    """
    if not narrative or not evidence_text:
        return None, None

    try:
        idx = narrative.lower().find(evidence_text.lower())
        if idx == -1:
            return None, None
        return idx, idx + len(evidence_text)
    except Exception:
        return None, None
