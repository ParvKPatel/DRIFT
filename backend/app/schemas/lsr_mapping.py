"""
Phase 5 — Life-Saving Rule (LSR) Mapping Schemas

Pydantic schemas for evidence-backed Life-Saving Rule mapping.
Enforces mapping to the 9 official project rules:
1. Bypassing Safety Controls
2. Confined Space
3. Driving
4. Energy Isolation
5. Hot Work
6. Line of Fire
7. Safe Mechanical Lifting
8. Work Authorisation
9. Working at Height
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.enums import LifeSavingRule, EvidenceStatus


class LsrMappingResult(BaseModel):
    """
    Full Life-Saving Rule Mapping Decision Payload.
    """
    report_id: str
    primary_life_saving_rule: LifeSavingRule = Field(..., description="Primary mapped Life-Saving Rule")
    secondary_life_saving_rules: List[LifeSavingRule] = Field(default_factory=list, description="Optional secondary mapped rules supported by evidence")
    lsr_confidence: float = Field(..., ge=0.0, le=1.0, description="Mapping confidence score (0.0 to 1.0)")
    lsr_evidence: Optional[str] = Field(None, description="Verbatim quote from narrative supporting the mapping")
    lsr_evidence_status: EvidenceStatus = Field(default=EvidenceStatus.UNKNOWN, description="EXPLICIT | INFERRED | UNKNOWN")
    lsr_reason: str = Field(..., description="Evidence-backed explanation of why rule was mapped")
    lsr_mapping_version: str = Field(default="lsr-engine-v1", description="Engine version")
    mapped_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LsrMappingRequest(BaseModel):
    """Request payload for mapping LSR for a single report."""
    force_remap: bool = Field(default=False, description="Re-map even if already mapped")


class BatchLsrMappingRequest(BaseModel):
    """Request payload for batch LSR mapping."""
    report_ids: Optional[List[str]] = Field(default=None, description="List of report_ids to map. If null, maps all unmapped reports.")
    force_remap: bool = Field(default=False, description="Re-map previously mapped reports")
    batch_size: int = Field(default=5, ge=1, le=20)


class BatchLsrMappingResponse(BaseModel):
    """Response payload for batch LSR mapping."""
    requested: int
    processed: int
    succeeded: int
    failed: int
    skipped: int
    results: List[Dict[str, Any]]
