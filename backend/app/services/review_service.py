"""
Phase 8 — Review Service

Business logic for the HSE Review & Human-in-the-Loop workflow:
- Create / Update Review (Confirm AI, Override, Reject, Needs More Information)
- Preserve Original AI Assessment immutably
- Retrieve Active Review State
- Retrieve Full Chronological Audit Trail History
- Retrieve Review Queue (with priority ordering & filtering)
- Review Summary Analytics (real database values)
"""

import json
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, case
from sqlalchemy.orm import selectinload

from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.models.reviews import Review
from app.schemas.enums import ReviewStatus, ReviewDecision, SifDecision, PriorityLevel
from app.schemas.review_schemas import (
    ReviewCreateRequest,
    ReviewResponse,
    ReviewHistoryItem,
    ReviewQueueItem,
    ReviewQueueResponse,
    ReviewAnalyticsSummary,
)
from app.utils.logging import logger


class ReviewService:

    @classmethod
    async def create_or_update_review(
        cls,
        report_id: str,
        request: ReviewCreateRequest,
        db: AsyncSession,
    ) -> ReviewResponse:
        """
        Creates a persistent review record for a safety report.
        Strictly preserves original AI conclusions and records reviewer decisions separately.
        """
        # 1. Fetch report and its AI analysis
        rep_query = select(Report).where(Report.report_id == report_id).options(selectinload(Report.safety_analysis))
        rep_res = await db.execute(rep_query)
        report = rep_res.scalar_one_or_none()

        if not report:
            raise ValueError(f"Safety report '{report_id}' not found.")

        sa = report.safety_analysis

        # 2. Extract original AI conclusions to preserve immutably
        orig_sif = sa.sif_fpi_potential.value if sa and sa.sif_fpi_potential else "UNCERTAIN"
        orig_lsr = (sa.primary_life_saving_rule or sa.life_saving_rule) if sa else "UNKNOWN"
        orig_lsr = orig_lsr or "UNKNOWN"
        orig_prio = sa.priority_level.value if sa and sa.priority_level else "ROUTINE"

        # 3. Determine final values and review status based on decision
        decision = request.review_decision
        if decision == ReviewDecision.CONFIRM_AI:
            review_status = ReviewStatus.REVIEWED
            final_sif = orig_sif
            final_lsr = orig_lsr
            final_prio = orig_prio
        elif decision == ReviewDecision.OVERRIDE:
            review_status = ReviewStatus.REVIEWED
            final_sif = request.final_sif_potential or orig_sif
            final_lsr = request.final_lsr or orig_lsr
            final_prio = request.final_priority or orig_prio
        elif decision == ReviewDecision.REJECT:
            review_status = ReviewStatus.REVIEWED
            final_sif = "REJECTED"
            final_lsr = "REJECTED"
            final_prio = "ROUTINE"
            if not request.reviewer_comment and not request.rejection_reason:
                raise ValueError("Rejection rationale or reason is required when rejecting a finding.")
        elif decision == ReviewDecision.NEEDS_MORE_INFORMATION:
            review_status = ReviewStatus.NEEDS_MORE_INFORMATION
            final_sif = orig_sif
            final_lsr = orig_lsr
            final_prio = orig_prio
        else:
            review_status = ReviewStatus.REVIEWED
            final_sif = orig_sif
            final_lsr = orig_lsr
            final_prio = orig_prio

        # 4. Serialize missing information fields if provided
        missing_json = json.dumps(request.missing_information_fields) if request.missing_information_fields else None

        # 5. Insert new Review record (audit trail retains every action)
        review_record = Review(
            report_id=report_id,
            reviewer_id=request.reviewer_id,
            review_status=review_status,
            review_decision=decision,
            original_ai_sif_potential=orig_sif,
            original_ai_lsr=orig_lsr,
            original_ai_priority=orig_prio,
            final_sif_potential=final_sif,
            final_lsr=final_lsr,
            final_priority=final_prio,
            reviewer_comment=request.reviewer_comment,
            rejection_reason=request.rejection_reason,
            missing_information_fields=missing_json,
            reviewed_at=datetime.now(timezone.utc),
        )
        db.add(review_record)

        # 6. Update SafetyAnalysis human review indicator (without overwriting original AI outputs)
        if sa:
            if decision in (ReviewDecision.CONFIRM_AI, ReviewDecision.OVERRIDE, ReviewDecision.REJECT):
                sa.review_required = False
            elif decision == ReviewDecision.NEEDS_MORE_INFORMATION:
                sa.review_required = True
                sa.review_reason = f"Needs More Information: {request.reviewer_comment or 'Evidence clarification required'}"

        await db.commit()
        await db.refresh(review_record)

        logger.info(
            f"Review recorded for report '{report_id}' by '{request.reviewer_id}': "
            f"Decision={decision.value} Status={review_status.value}"
        )

        return cls._map_to_response(review_record)

    @classmethod
    async def get_latest_review(
        cls,
        report_id: str,
        db: AsyncSession,
    ) -> Optional[ReviewResponse]:
        query = (
            select(Review)
            .where(Review.report_id == report_id)
            .order_by(Review.reviewed_at.desc(), Review.id.desc())
            .limit(1)
        )
        res = await db.execute(query)
        review = res.scalar_one_or_none()
        return cls._map_to_response(review) if review else None

    @classmethod
    async def get_review_history(
        cls,
        report_id: str,
        db: AsyncSession,
    ) -> List[ReviewHistoryItem]:
        query = (
            select(Review)
            .where(Review.report_id == report_id)
            .order_by(Review.reviewed_at.desc(), Review.id.desc())
        )
        res = await db.execute(query)
        reviews = res.scalars().all()

        history = []
        for r in reviews:
            missing_fields = []
            if r.missing_information_fields:
                try:
                    missing_fields = json.loads(r.missing_information_fields)
                except Exception:
                    pass

            history.append(
                ReviewHistoryItem(
                    id=r.id,
                    reviewer_id=r.reviewer_id,
                    review_decision=r.review_decision.value if hasattr(r.review_decision, "value") else str(r.review_decision),
                    original_ai_sif_potential=r.original_ai_sif_potential,
                    final_sif_potential=r.final_sif_potential,
                    original_ai_lsr=r.original_ai_lsr,
                    final_lsr=r.final_lsr,
                    original_ai_priority=r.original_ai_priority,
                    final_priority=r.final_priority,
                    reviewer_comment=r.reviewer_comment,
                    rejection_reason=r.rejection_reason,
                    missing_information_fields=missing_fields,
                    reviewed_at=r.reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if r.reviewed_at else "",
                )
            )
        return history

    @classmethod
    async def get_review_queue(
        cls,
        db: AsyncSession,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        sif_filter: Optional[str] = None,
        site_filter: Optional[str] = None,
        lsr_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ReviewQueueResponse:
        """
        Retrieves safety reports needing HSE attention, ordered by priority score descending.
        Reports are enriched with their latest review status and decisions.
        """
        # Query reports with joined safety analysis
        query = (
            select(Report)
            .outerjoin(SafetyAnalysis, Report.report_id == SafetyAnalysis.report_id)
            .options(selectinload(Report.safety_analysis))
        )

        filters = []
        if priority_filter:
            filters.append(SafetyAnalysis.priority_level == priority_filter)
        if sif_filter:
            filters.append(SafetyAnalysis.sif_fpi_potential == sif_filter)
        if site_filter:
            filters.append(Report.site.ilike(f"%{site_filter}%"))
        if lsr_filter:
            filters.append(
                or_(
                    SafetyAnalysis.primary_life_saving_rule == lsr_filter,
                    SafetyAnalysis.life_saving_rule == lsr_filter,
                )
            )

        if filters:
            query = query.where(and_(*filters))

        # Order by priority score desc, then report date desc
        query = query.order_by(
            SafetyAnalysis.priority_score.desc().nullslast(),
            Report.report_date.desc().nullslast(),
            Report.id.desc(),
        )

        count_stmt = select(func.count(Report.id)).outerjoin(SafetyAnalysis, Report.report_id == SafetyAnalysis.report_id)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one() or 0

        res = await db.execute(query.offset(offset).limit(limit))
        reports = res.scalars().all()

        # Query latest reviews for these reports
        rep_ids = [r.report_id for r in reports]
        rev_query = (
            select(Review)
            .where(Review.report_id.in_(rep_ids))
            .order_by(Review.reviewed_at.desc(), Review.id.desc())
        )
        rev_res = await db.execute(rev_query)
        all_revs = rev_res.scalars().all()

        latest_rev_map = {}
        for rev in all_revs:
            if rev.report_id not in latest_rev_map:
                latest_rev_map[rev.report_id] = rev

        items = []
        for r in reports:
            sa = r.safety_analysis
            latest_rev = latest_rev_map.get(r.report_id)

            cur_status = latest_rev.review_status if latest_rev else ReviewStatus.UNREVIEWED
            cur_decision = latest_rev.review_decision.value if latest_rev and hasattr(latest_rev.review_decision, "value") else (str(latest_rev.review_decision) if latest_rev else None)

            # Apply review status filter in memory if specified
            if status_filter and status_filter != "ALL":
                if cur_status.value != status_filter:
                    continue

            snippet = r.narrative[:140] + ("..." if len(r.narrative) > 140 else "")

            ai_lsr = None
            if sa:
                ai_lsr = sa.primary_life_saving_rule or sa.life_saving_rule

            items.append(
                ReviewQueueItem(
                    report_id=r.report_id,
                    report_date=r.report_date.isoformat() if r.report_date else None,
                    site=r.site,
                    functional_location=r.functional_location,
                    activity=sa.activity if sa else None,
                    hazard=sa.hazard if sa else None,
                    narrative_snippet=snippet,
                    ai_sif_potential=sa.sif_fpi_potential.value if sa and sa.sif_fpi_potential else None,
                    ai_lsr=ai_lsr,
                    ai_priority_level=sa.priority_level.value if sa and sa.priority_level else None,
                    ai_priority_score=sa.priority_score if sa else None,
                    review_status=cur_status,
                    latest_decision=cur_decision,
                    review_required=sa.review_required if sa else False,
                    review_reason=sa.review_reason if sa else None,
                    escalation_score=sa.escalation_score if sa else None,
                )
            )

        return ReviewQueueResponse(total=total, items=items)

    @classmethod
    async def get_review_analytics(cls, db: AsyncSession) -> ReviewAnalyticsSummary:
        """Calculates real, database-backed review completion metrics."""
        total_reports_res = await db.execute(select(func.count(Report.id)))
        total_in_scope = total_reports_res.scalar_one() or 0

        # Unique reviewed report IDs
        reviewed_reports_res = await db.execute(select(func.count(func.distinct(Review.report_id))))
        reviewed_count = reviewed_reports_res.scalar_one() or 0
        pending_review = max(0, total_in_scope - reviewed_count)

        # Decision breakdown
        dec_query = select(
            func.count(case((Review.review_decision == ReviewDecision.CONFIRM_AI, 1))).label("confirmed"),
            func.count(case((Review.review_decision == ReviewDecision.OVERRIDE, 1))).label("overridden"),
            func.count(case((Review.review_decision == ReviewDecision.REJECT, 1))).label("rejected"),
            func.count(case((Review.review_decision == ReviewDecision.NEEDS_MORE_INFORMATION, 1))).label("needs_info"),
        )
        d_res = await db.execute(dec_query)
        d_row = d_res.one()

        return ReviewAnalyticsSummary(
            total_in_scope=total_in_scope,
            pending_review=pending_review,
            total_reviewed=reviewed_count,
            confirmed_count=d_row.confirmed or 0,
            overridden_count=d_row.overridden or 0,
            rejected_count=d_row.rejected or 0,
            needs_more_info_count=d_row.needs_info or 0,
        )

    @staticmethod
    def _map_to_response(r: Review) -> ReviewResponse:
        missing_fields = []
        if r.missing_information_fields:
            try:
                missing_fields = json.loads(r.missing_information_fields)
            except Exception:
                pass

        return ReviewResponse(
            id=r.id,
            report_id=r.report_id,
            reviewer_id=r.reviewer_id,
            review_status=r.review_status,
            review_decision=r.review_decision,
            original_ai_sif_potential=r.original_ai_sif_potential,
            original_ai_lsr=r.original_ai_lsr,
            original_ai_priority=r.original_ai_priority,
            final_sif_potential=r.final_sif_potential,
            final_lsr=r.final_lsr,
            final_priority=r.final_priority,
            reviewer_comment=r.reviewer_comment,
            rejection_reason=r.rejection_reason,
            missing_information_fields=missing_fields,
            reviewed_at=r.reviewed_at,
            created_at=r.created_at,
        )
