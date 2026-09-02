from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.schemas.enums import EvidenceStatus, SifDecision, BarrierCondition, PriorityLevel, EnergySource


class SafetyAnalysisBase(BaseModel):
    report_id: str = Field(..., description="Foreign key reference to raw report_id")
    activity: Optional[str] = None
    equipment: Optional[str] = None
    hazard: Optional[str] = None
    energy_source: Optional[EnergySource] = EnergySource.UNKNOWN
    exposure: Optional[str] = None
    exposure_location: Optional[str] = None
    barrier: Optional[str] = None
    barrier_condition: Optional[BarrierCondition] = BarrierCondition.UNKNOWN
    potential_consequence: Optional[str] = None
    sif_fpi_potential: Optional[SifDecision] = SifDecision.UNCERTAIN
    sif_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence_status: Optional[EvidenceStatus] = EvidenceStatus.UNKNOWN
    evidence_span: Optional[str] = None
    reason_code: Optional[str] = None
    life_saving_rule: Optional[str] = None
    novelty_score: Optional[float] = None
    review_required: bool = False
    review_reason: Optional[str] = None

    # Calculated intelligence scores
    sif_evidence_score: Optional[float] = None
    barrier_score: Optional[float] = None
    recurrence_score: Optional[float] = None
    escalation_score: Optional[float] = None
    priority_score: Optional[float] = None
    priority_level: Optional[PriorityLevel] = PriorityLevel.UNCERTAIN


class SafetyAnalysisCreate(SafetyAnalysisBase):
    pass


class SafetyAnalysisRead(SafetyAnalysisBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
