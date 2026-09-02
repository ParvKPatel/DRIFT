"""
Phase 6 — Semantic Similarity & Report Retrieval Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from app.schemas.enums import SimilarityBand, LifeSavingRule, SifDecision, PriorityLevel


class SharedMechanismDetails(BaseModel):
    """Explains shared mechanisms and structured overlaps between two reports."""
    shared_activity: Optional[str] = None
    shared_hazard: Optional[str] = None
    shared_equipment: Optional[str] = None
    shared_exposure: Optional[str] = None
    shared_barrier: Optional[str] = None
    shared_lsr: Optional[str] = None
    shared_asset: Optional[str] = None
    shared_functional_location: Optional[str] = None
    days_between: Optional[int] = None
    semantic_similarity: float = Field(..., ge=0.0, le=1.0)
    mechanism_similarity: float = Field(..., ge=0.0, le=1.0)
    structured_similarity: float = Field(..., ge=0.0, le=1.0)


class SimilarReportItem(BaseModel):
    """Single similar report entry in retrieval API response."""
    report_id: str
    report_date: Optional[date] = None
    site: Optional[str] = None
    functional_location: Optional[str] = None
    narrative_snippet: str
    fixed_short_description: Optional[str] = None
    sif_fpi_potential: Optional[SifDecision] = None
    primary_life_saving_rule: Optional[str] = None
    priority_level: Optional[PriorityLevel] = None
    
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    similarity_band: SimilarityBand
    shared_details: SharedMechanismDetails

    model_config = {"from_attributes": True}


class SimilarReportResponse(BaseModel):
    """Response payload for GET /reports/{id}/similar."""
    target_report_id: str
    total_found: int
    similar_reports: List[SimilarReportItem]
