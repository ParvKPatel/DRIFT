"""
Phase 3 — Structured Safety Fact Extraction Schema

Every extracted safety fact carries:
  - value: the extracted content (None = not found)
  - evidence: verbatim quote from the source narrative
  - evidence_status: EXPLICIT | INFERRED | UNKNOWN
  - confidence: 0.0–1.0
  - start_offset / end_offset: character positions in the original narrative

The AI must NEVER invent missing facts. Unknown = UNKNOWN.
SIF/FPI classification does NOT belong in this schema — that is Phase 4+.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from app.schemas.enums import (
    EvidenceStatus,
    AnalysisStatus,
    BarrierCondition,
    EnergySource,
)

T = TypeVar("T")


class FactField(BaseModel, Generic[T]):
    """A single extracted safety fact with evidence traceability."""

    value: Optional[T] = Field(
        default=None,
        description="Extracted value. None if not found in narrative."
    )
    evidence: Optional[str] = Field(
        default=None,
        description="Verbatim supporting quote from the original narrative text."
    )
    evidence_status: EvidenceStatus = Field(
        default=EvidenceStatus.UNKNOWN,
        description="EXPLICIT = stated directly. INFERRED = reasoned from context. UNKNOWN = not determinable."
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence of extraction from 0.0 to 1.0."
    )
    start_offset: Optional[int] = Field(
        default=None,
        description="Character start position in original narrative (0-indexed). None if not calculable."
    )
    end_offset: Optional[int] = Field(
        default=None,
        description="Character end position in original narrative (exclusive). None if not calculable."
    )

    model_config = {"from_attributes": True}


class SafetyFactsExtractionResponse(BaseModel):
    """
    The full structured safety fact payload returned by AI extraction.

    All 9 safety fact fields map to Phase 3 acceptance criteria.
    No SIF/FPI decision, no priority score, no LSR mapping here.
    """

    activity: FactField[str] = Field(
        default_factory=FactField,
        description="Task or work being performed at time of incident."
    )
    equipment: FactField[str] = Field(
        default_factory=FactField,
        description="Equipment, tool, machine, or object involved."
    )
    hazard: FactField[str] = Field(
        default_factory=FactField,
        description="The hazardous mechanism or condition (NOT the source incident_cause field)."
    )
    energy_source: FactField[EnergySource] = Field(
        default_factory=FactField,
        description="The energy form capable of causing harm."
    )
    exposure: FactField[str] = Field(
        default_factory=FactField,
        description="Who or what was exposed and how."
    )
    exposure_location: FactField[str] = Field(
        default_factory=FactField,
        description="Where the exposed person/object was relative to the hazard."
    )
    barrier: FactField[str] = Field(
        default_factory=FactField,
        description="The safety control that should prevent or mitigate the hazard."
    )
    barrier_condition: FactField[BarrierCondition] = Field(
        default_factory=FactField,
        description="Condition of the barrier: INTACT, DEGRADED, FAILED, ABSENT, or UNKNOWN."
    )
    potential_consequence: FactField[str] = Field(
        default_factory=FactField,
        description="What COULD happen if the hazard mechanism reaches the exposed person. NOT the actual outcome."
    )

    # Top-level extraction metadata
    is_mock: bool = Field(
        default=False,
        description="True when produced by mock/demo provider. False for real AI output."
    )
    extraction_notes: Optional[str] = Field(
        default=None,
        description="Optional freeform notes about extraction quality or unusual conditions."
    )

    model_config = {"from_attributes": True}


class AnalysisRequest(BaseModel):
    """Request body for triggering analysis."""
    force_reanalyze: bool = Field(
        default=False,
        description="If True, re-run analysis even if a COMPLETED analysis already exists."
    )


class BatchAnalysisRequest(BaseModel):
    """Request body for batch analysis trigger."""
    report_ids: Optional[List[str]] = Field(
        default=None,
        description="List of report IDs to analyze. If None, all NOT_ANALYZED reports are targeted."
    )
    force_reanalyze: bool = Field(
        default=False,
        description="If True, re-run even for reports that already have COMPLETED analysis."
    )
    batch_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent analysis jobs."
    )


class EvidenceItemResponse(BaseModel):
    """Evidence span as returned from the API."""
    id: int
    report_id: str
    analysis_id: Optional[int] = None
    field_name: str
    evidence_text: str
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    evidence_status: EvidenceStatus
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisResultResponse(BaseModel):
    """Full analysis result returned by the single-report analyze endpoint."""
    report_id: str
    analysis_status: AnalysisStatus
    analysis_version: str
    model_name: Optional[str] = None
    provider_name: Optional[str] = None
    analyzed_at: Optional[datetime] = None
    is_mock: bool = False

    # Extracted safety facts (flat view for UI consumption)
    activity: Optional[str] = None
    activity_evidence: Optional[str] = None
    activity_evidence_status: Optional[EvidenceStatus] = None
    activity_confidence: Optional[float] = None

    equipment: Optional[str] = None
    equipment_evidence: Optional[str] = None
    equipment_evidence_status: Optional[EvidenceStatus] = None
    equipment_confidence: Optional[float] = None

    hazard: Optional[str] = None
    hazard_evidence: Optional[str] = None
    hazard_evidence_status: Optional[EvidenceStatus] = None
    hazard_confidence: Optional[float] = None

    energy_source: Optional[str] = None
    energy_source_evidence: Optional[str] = None
    energy_source_evidence_status: Optional[EvidenceStatus] = None
    energy_source_confidence: Optional[float] = None

    exposure: Optional[str] = None
    exposure_evidence: Optional[str] = None
    exposure_evidence_status: Optional[EvidenceStatus] = None
    exposure_confidence: Optional[float] = None

    exposure_location: Optional[str] = None
    exposure_location_evidence: Optional[str] = None
    exposure_location_evidence_status: Optional[EvidenceStatus] = None
    exposure_location_confidence: Optional[float] = None

    barrier: Optional[str] = None
    barrier_evidence: Optional[str] = None
    barrier_evidence_status: Optional[EvidenceStatus] = None
    barrier_confidence: Optional[float] = None

    barrier_condition: Optional[str] = None
    barrier_condition_evidence: Optional[str] = None
    barrier_condition_evidence_status: Optional[EvidenceStatus] = None
    barrier_condition_confidence: Optional[float] = None

    potential_consequence: Optional[str] = None
    potential_consequence_evidence: Optional[str] = None
    potential_consequence_evidence_status: Optional[EvidenceStatus] = None
    potential_consequence_confidence: Optional[float] = None

    # Evidence span items
    evidence_items: List[EvidenceItemResponse] = []

    model_config = {"from_attributes": True}


class BatchAnalysisResultResponse(BaseModel):
    """Summary result from batch analysis endpoint."""
    requested: int
    processed: int
    succeeded: int
    failed: int
    skipped: int
    results: List[dict] = []
