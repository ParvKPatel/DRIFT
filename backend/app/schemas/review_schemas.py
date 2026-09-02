"""
Phase 8 — Review Schemas

Pydantic schemas for HSE Review & Human-in-the-Loop workflow:
- ReviewCreateRequest (Confirm, Override, Reject, Needs More Info)
- ReviewResponse
- ReviewHistoryItem
- ReviewQueueItem & ReviewQueueResponse
- ReviewAnalyticsSummary
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.enums import ReviewStatus, ReviewDecision, RejectionReason, SifDecision, PriorityLevel, LifeSavingRule


class ReviewCreateRequest(BaseModel):
    reviewer_id: str = Field(default="HSE Reviewer #1", description="Reviewer identifier")
    review_decision: ReviewDecision = Field(..., description="Review decision: CONFIRM_AI, OVERRIDE, REJECT, NEEDS_MORE_INFORMATION")

    # Editable fields when OVERRIDE is chosen
    final_sif_potential: Optional[str] = Field(None, description="Overridden SIF potential (YES, NO, UNCERTAIN)")
    final_lsr: Optional[str] = Field(None, description="Overridden Life-Saving Rule")
    final_priority: Optional[str] = Field(None, description="Overridden Priority Level")

    # Required when REJECT is chosen
    rejection_reason: Optional[str] = Field(None, description="Rejection reason code or description")

    # Required/relevant when NEEDS_MORE_INFORMATION is chosen
    missing_information_fields: Optional[List[str]] = Field(default_factory=list, description="List of missing evidence fields")

    # Reviewer rationale
    reviewer_comment: Optional[str] = Field(None, description="Reviewer comments and justification")


class ReviewResponse(BaseModel):
    id: int
    report_id: str
    reviewer_id: str
    review_status: ReviewStatus
    review_decision: ReviewDecision

    # Original AI outputs preserved
    original_ai_sif_potential: Optional[str] = None
    original_ai_lsr: Optional[str] = None
    original_ai_priority: Optional[str] = None

    # Human-reviewed outputs
    final_sif_potential: Optional[str] = None
    final_lsr: Optional[str] = None
    final_priority: Optional[str] = None

    reviewer_comment: Optional[str] = None
    rejection_reason: Optional[str] = None
    missing_information_fields: List[str] = Field(default_factory=list)
    reviewed_at: datetime
    created_at: datetime


class ReviewHistoryItem(BaseModel):
    id: int
    reviewer_id: str
    review_decision: str
    original_ai_sif_potential: Optional[str] = None
    final_sif_potential: Optional[str] = None
    original_ai_lsr: Optional[str] = None
    final_lsr: Optional[str] = None
    original_ai_priority: Optional[str] = None
    final_priority: Optional[str] = None
    reviewer_comment: Optional[str] = None
    rejection_reason: Optional[str] = None
    missing_information_fields: List[str] = Field(default_factory=list)
    reviewed_at: str


class ReviewQueueItem(BaseModel):
    report_id: str
    report_date: Optional[str] = None
    site: Optional[str] = None
    functional_location: Optional[str] = None
    activity: Optional[str] = None
    hazard: Optional[str] = None
    narrative_snippet: str
    ai_sif_potential: Optional[str] = None
    ai_lsr: Optional[str] = None
    ai_priority_level: Optional[str] = None
    ai_priority_score: Optional[float] = None
    review_status: ReviewStatus
    latest_decision: Optional[str] = None
    review_required: bool = False
    review_reason: Optional[str] = None
    escalation_score: Optional[float] = None


class ReviewQueueResponse(BaseModel):
    total: int
    items: List[ReviewQueueItem]


class ReviewAnalyticsSummary(BaseModel):
    total_in_scope: int = 0
    pending_review: int = 0
    total_reviewed: int = 0
    confirmed_count: int = 0
    overridden_count: int = 0
    rejected_count: int = 0
    needs_more_info_count: int = 0
