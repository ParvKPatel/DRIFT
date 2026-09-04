"""
Phase 4 — SIF/FPI Intelligence Engine Schemas

Pydantic schemas for:
- Transparent safety screening signals (0.0 to 1.0)
- Deterministic safety rule triggers
- SIF/FPI screening result and batch response payloads
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.enums import SifDecision, ScreeningStatus, EvidenceStatus


class ScreeningSignals(BaseModel):
    """
    Transparent safety-screening signals (0.0 to 1.0).

    IMPORTANT:
    These are NOT probabilities of death or injury.
    They are intermediate screening metrics that measure signal strength
    across the 5 critical dimensions of safety risk.
    """
    mechanism_signal: float = Field(..., ge=0.0, le=1.0, description="Strength of hazardous mechanism/energy signal")
    exposure_signal: float = Field(..., ge=0.0, le=1.0, description="Plausibility of human exposure to hazard")
    barrier_signal: float = Field(..., ge=0.0, le=1.0, description="Degree of barrier failure/absence/degradation")
    consequence_signal: float = Field(..., ge=0.0, le=1.0, description="Severity of potential consequence")
    evidence_signal: float = Field(..., ge=0.0, le=1.0, description="Overall quality and explicitness of narrative evidence")


class RuleTrigger(BaseModel):
    """Details of a deterministic safety rule that fired during screening."""
    rule_id: str = Field(..., description="Canonical rule ID, e.g. RULE-001")
    rule_name: str = Field(..., description="Human readable rule name")
    reason_code: str = Field(..., description="Standardized DRIFT reason code, e.g. SIF-001")
    description: str = Field(..., description="Detailed explanation of why rule triggered")
    signal_strength: float = Field(1.0, ge=0.0, le=1.0, description="Rule signal weight")
    evidence_refs: List[str] = Field(default_factory=list, description="Associated evidence quotes from narrative")


class SifScreeningResult(BaseModel):
    """
    Full SIF/FPI Screening Decision Payload.

    Contains defensible classification (YES/NO/UNCERTAIN), confidence,
    reason codes, triggered rules, intermediate signals, and evidence explanation.
    """
    report_id: str
    sif_fpi_potential: SifDecision = Field(..., description="YES | NO | UNCERTAIN")
    sif_confidence: float = Field(..., ge=0.0, le=1.0, description="Screening decision confidence score")
    screening_status: ScreeningStatus = Field(default=ScreeningStatus.SCREENED)

    screening_reason: str = Field(..., description="Evidence-backed human readable explanation")
    reason_codes: List[str] = Field(default_factory=list, description="List of reason codes, e.g. ['SIF-001', 'SIF-003']")
    rule_ids_triggered: List[str] = Field(default_factory=list, description="List of rule IDs triggered, e.g. ['RULE-001']")
    contributing_factors: List[str] = Field(default_factory=list, description="Summary of key contributing factors")

    signals: ScreeningSignals = Field(..., description="5 transparent screening signal metrics")
    rules_triggered: List[RuleTrigger] = Field(default_factory=list, description="Detailed list of rule triggers")

    screening_version: str = Field(default="sif-engine-v1", description="Version of SIF screening engine")
    screened_at: Optional[datetime] = None

    review_required: bool = Field(default=False, description="True if human safety review is required")
    review_reason: Optional[str] = Field(default=None, description="Explanation why review is required")

    model_config = {"from_attributes": True}


class SifScreeningRequest(BaseModel):
    """Request model for screening a single report."""
    force_rescreen: bool = Field(default=False, description="If True, re-screen even if report was previously SCREENED")


class BatchSifScreeningRequest(BaseModel):
    """Request model for batch SIF screening."""
    report_ids: Optional[List[str]] = Field(default=None, description="List of report_ids to screen. If null, screens all unscreened completed reports.")
    force_rescreen: bool = Field(default=False, description="If True, re-screens previously screened reports")
    batch_size: int = Field(default=5, ge=1, le=20, description="Max concurrent processing batch size")


class BatchSifScreeningResponse(BaseModel):
    """Response payload for batch SIF screening."""
    requested: int
    processed: int
    succeeded: int
    failed: int
    skipped: int
    results: List[Dict[str, Any]]
