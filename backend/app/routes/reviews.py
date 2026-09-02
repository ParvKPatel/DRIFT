"""
Phase 8 — Review API Router

Exposes endpoints for the HSE Review & Human-in-the-Loop workflow:
- GET  /reviews/queue             (Review queue with priority sorting & filtering)
- GET  /reviews/analytics         (Real review analytics)
- GET  /reviews/{report_id}       (Get latest review for report)
- POST /reviews/{report_id}       (Submit human review decision)
- GET  /reviews/{report_id}/history (Chronological audit trail)
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.schemas.review_schemas import (
    ReviewCreateRequest,
    ReviewResponse,
    ReviewHistoryItem,
    ReviewQueueResponse,
    ReviewAnalyticsSummary,
)
from app.services.review_service import ReviewService
from app.utils.logging import logger

router = APIRouter(prefix="/reviews", tags=["HSE Review & Human-in-the-Loop"])


@router.get("/queue", response_model=ReviewQueueResponse, summary="Get HSE Review Queue")
async def get_review_queue(
    status: Optional[str] = Query(None, description="Filter by review status (UNREVIEWED, IN_REVIEW, REVIEWED, NEEDS_MORE_INFORMATION)"),
    priority: Optional[str] = Query(None, description="Filter by HSE Priority level"),
    sif: Optional[str] = Query(None, description="Filter by SIF potential (YES, NO, UNCERTAIN)"),
    site: Optional[str] = Query(None, description="Filter by operational site"),
    lsr: Optional[str] = Query(None, description="Filter by Life-Saving Rule"),
    limit: int = Query(50, ge=1, le=100, description="Items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
):
    """Returns safety reports in the HSE review queue, sorted by priority urgency."""
    return await ReviewService.get_review_queue(
        db=db,
        status_filter=status,
        priority_filter=priority,
        sif_filter=sif,
        site_filter=site,
        lsr_filter=lsr,
        limit=limit,
        offset=offset,
    )


@router.get("/analytics", response_model=ReviewAnalyticsSummary, summary="Get HSE Review Analytics")
async def get_review_analytics(db: AsyncSession = Depends(get_db)):
    """Returns database-derived review metrics: pending, confirmed, overridden, rejected, needs more info."""
    return await ReviewService.get_review_analytics(db=db)


@router.get("/{report_id}", response_model=Optional[ReviewResponse], summary="Get Latest Review for Report")
async def get_report_review(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns the most recent human review for the specified safety report."""
    review = await ReviewService.get_latest_review(report_id=report_id, db=db)
    if not review:
        return None
    return review


@router.post("/{report_id}", response_model=ReviewResponse, summary="Submit Human Review Decision")
async def submit_report_review(
    report_id: str,
    request: ReviewCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a human review decision (CONFIRM_AI, OVERRIDE, REJECT, NEEDS_MORE_INFORMATION).
    Preserves original AI outputs and appends an auditable record to the report's review history.
    """
    try:
        return await ReviewService.create_or_update_review(
            report_id=report_id,
            request=request,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to submit review for report '{report_id}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit review: {exc}",
        )


@router.get("/{report_id}/history", response_model=List[ReviewHistoryItem], summary="Get Review Audit Trail History")
async def get_report_review_history(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns complete chronological audit history of all reviewer actions for a safety report."""
    return await ReviewService.get_review_history(report_id=report_id, db=db)
