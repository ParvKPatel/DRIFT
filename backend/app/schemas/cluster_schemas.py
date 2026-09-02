"""
Phase 6 — Precursor Clustering & Escalation Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from app.schemas.enums import EscalationBand, SifDecision, PriorityLevel


class TimelineEvent(BaseModel):
    """Event in cluster timeline visualization."""
    report_id: str
    report_date: Optional[date] = None
    days_from_first: int
    title: str
    narrative_snippet: str
    hazard: Optional[str] = None
    barrier_condition: Optional[str] = None
    exposure: Optional[str] = None
    sif_fpi_potential: Optional[SifDecision] = None


class ClusterMemberResponse(BaseModel):
    """Member report inside a cluster."""
    report_id: str
    report_date: Optional[date] = None
    site: Optional[str] = None
    functional_location: Optional[str] = None
    short_description: Optional[str] = None
    sif_fpi_potential: Optional[SifDecision] = None
    primary_life_saving_rule: Optional[str] = None
    priority_level: Optional[PriorityLevel] = None
    similarity_to_cluster: float

    model_config = {"from_attributes": True}


class ClusterResponse(BaseModel):
    """Cluster summary payload for directory list."""
    id: int
    cluster_name: str
    common_mechanism: Optional[str] = None
    common_asset: Optional[str] = None
    common_hazard: Optional[str] = None
    common_activity: Optional[str] = None
    common_equipment: Optional[str] = None
    common_barrier: Optional[str] = None
    common_lsr: Optional[str] = None
    recurrence_count: int
    escalation_score: float = Field(..., ge=0.0, le=100.0)
    escalation_band: EscalationBand
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClusterDetailResponse(ClusterResponse):
    """Detailed cluster payload including members, timeline, and escalation evidence."""
    members: List[ClusterMemberResponse]
    timeline: List[TimelineEvent]
    why_escalating: List[str]
    systemic_pattern: Optional[str] = None


class ClusterRebuildResponse(BaseModel):
    """Response for POST /clusters/rebuild."""
    total_reports_processed: int
    total_clusters_formed: int
    high_escalation_clusters: int
    rebuilt_at: datetime
