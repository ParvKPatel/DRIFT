"""
Phase 5 — HSE Priority Engine Schemas & Full Intelligence Pipeline Schemas

Pydantic schemas for:
- 0–100 HSE priority score ranking
- Priority components & availability tracking
- Combined Full Intelligence Pipeline response (Phase 3 + 4 + 5)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.enums import PriorityLevel, ComponentStatus, SifDecision
from app.schemas.safety_extraction import AnalysisResultResponse
from app.schemas.sif_screening import SifScreeningResult
from app.schemas.lsr_mapping import LsrMappingResult


class PriorityComponent(BaseModel):
    """Component score in the HSE Priority Engine."""
    name: str = Field(..., description="Component name, e.g. sif_evidence_score")
    score: Optional[float] = Field(None, description="Score 0.0 to 1.0 (or null if unavailable)")
    weight: float = Field(..., description="Weight used in 0-100 formula")
    status: ComponentStatus = Field(..., description="AVAILABLE | NOT_YET_AVAILABLE | UNKNOWN")
    description: str = Field(..., description="Human readable component status description")


class PriorityResult(BaseModel):
    """
    Full HSE Priority Calculation Payload.

    IMPORTANT:
    The priority_score is a 0–100 ranking/prioritisation score for HSE attention.
    It does NOT represent probability of death or risk percentage.
    """
    report_id: str
    priority_score: float = Field(..., ge=0.0, le=100.0, description="HSE Prioritisation Score (0 to 100)")
    priority_level: PriorityLevel = Field(..., description="ROUTINE | SAFETY_REVIEW | HIGH_PRIORITY_SIF_FPI_PRECURSOR | CRITICAL | UNCERTAIN")
    priority_reason_codes: List[str] = Field(default_factory=list, description="Reason codes, e.g. ['PRIORITY-001']")
    priority_override: bool = Field(default=False, description="True if critical safety rule forced priority level override")
    override_reason: Optional[str] = Field(default=None, description="Reason for critical safety override")
    
    components: List[PriorityComponent] = Field(default_factory=list, description="Breakdown of individual component scores")
    why_prioritized: List[str] = Field(default_factory=list, description="Key factors explaining why this priority score/level was assigned")
    unavailable_components: List[str] = Field(default_factory=list, description="Components not yet available until Phase 6+")

    priority_version: str = Field(default="priority-engine-v1")
    calculated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PriorityRequest(BaseModel):
    """Request payload for priority calculation."""
    force_recalculate: bool = Field(default=False)


class BatchPriorityRequest(BaseModel):
    """Request payload for batch priority calculation."""
    report_ids: Optional[List[str]] = Field(default=None)
    force_recalculate: bool = Field(default=False)
    batch_size: int = Field(default=5, ge=1, le=20)


class BatchPriorityResponse(BaseModel):
    """Response payload for batch priority calculation."""
    requested: int
    processed: int
    succeeded: int
    failed: int
    skipped: int
    results: List[Dict[str, Any]]


class FullIntelligenceResult(BaseModel):
    """
    Combined Pipeline Result (Phase 3 Extraction + Phase 4 SIF Screening + Phase 5 LSR & Priority).
    Provides a complete, single-call payload for report intelligence dashboard.
    """
    report_id: str
    extraction: Optional[AnalysisResultResponse] = None
    sif_screening: Optional[SifScreeningResult] = None
    lsr_mapping: Optional[LsrMappingResult] = None
    priority: Optional[PriorityResult] = None
