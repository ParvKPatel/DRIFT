"""
Phase 7 — Dashboard Schemas

Pydantic schemas for the DRIFT Intelligence Dashboard:
- Executive Summary & Comparison
- Trend Points
- Site & Functional Location Intelligence (Density vs Concentration)
- Activity & Hazard Intelligence
- Life-Saving Rule (LSR) Intelligence
- Barrier Intelligence (Intact, Degraded, Failed, Absent, Unknown)
- Escalating Precursor Patterns
- Recent Pattern Alerts
- Data Quality & Coverage
- Global Filter Parameters
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date, datetime
from app.schemas.enums import SifDecision, PriorityLevel, EscalationBand, BarrierCondition, LifeSavingRule


class DashboardSummary(BaseModel):
    total_reports: int = 0
    analyzed_reports: int = 0
    sif_yes: int = 0
    sif_no: int = 0
    sif_uncertain: int = 0
    high_priority: int = 0
    critical: int = 0
    escalating_clusters: int = 0
    active_clusters: int = 0
    # Denominator-safe share of analyzed reports
    sif_share_pct: Optional[float] = None
    # Comparison period data (None if unavailable)
    comparison_period_label: Optional[str] = "No comparison data"
    total_reports_change_pct: Optional[float] = None
    sif_yes_change_pct: Optional[float] = None
    high_priority_change_pct: Optional[float] = None


class TrendPoint(BaseModel):
    date: str
    total_reports: int = 0
    sif_yes: int = 0
    sif_uncertain: int = 0
    high_priority: int = 0


class SiteSummary(BaseModel):
    site: str
    report_count: int = 0
    sif_count: int = 0
    sif_uncertain_count: int = 0
    high_priority_count: int = 0
    critical_count: int = 0
    cluster_count: int = 0
    escalating_cluster_count: int = 0
    total_man_hours: float = 0.0
    # Normalized density: SIF / man-hours (per 10k or 100k man-hours)
    precursor_density: Optional[float] = None
    precursor_density_unit: Optional[str] = None
    # Fallback concentration: SIF / total reports %
    precursor_concentration_pct: float = 0.0
    has_valid_man_hours: bool = False
    barrier_weakness_count: int = 0


class ActivitySummary(BaseModel):
    activity: str
    report_count: int = 0
    sif_count: int = 0
    high_priority_count: int = 0
    cluster_count: int = 0
    escalation_score: float = 0.0
    common_hazard: Optional[str] = None
    common_barrier: Optional[str] = None
    common_lsr: Optional[str] = None


class HazardSummary(BaseModel):
    hazard: str
    report_count: int = 0
    sif_count: int = 0
    high_priority_count: int = 0
    associated_lsrs: List[str] = Field(default_factory=list)
    associated_barriers: List[str] = Field(default_factory=list)
    associated_clusters: List[str] = Field(default_factory=list)


class LsrSummary(BaseModel):
    lsr: str
    mapped_count: int = 0
    sif_yes_count: int = 0
    high_priority_count: int = 0
    critical_count: int = 0
    escalating_cluster_count: int = 0


class BarrierSummary(BaseModel):
    barrier: str
    total_mentions: int = 0
    intact_count: int = 0
    degraded_count: int = 0
    failed_count: int = 0
    absent_count: int = 0
    unknown_count: int = 0
    sif_count: int = 0
    high_priority_count: int = 0
    escalating_cluster_count: int = 0
    # Weakness score: weighted sum of (failed * 3 + absent * 3 + degraded * 1.5)
    weakness_score: float = 0.0


class RecurringMechanismSummary(BaseModel):
    mechanism_name: str
    report_count: int = 0
    sif_count: int = 0
    cluster_count: int = 0
    escalation_score: float = 0.0
    shared_asset: Optional[str] = None
    shared_barrier: Optional[str] = None
    lsr: Optional[str] = None


class RecentAlertSummary(BaseModel):
    id: int
    created_at: str
    cluster_id: Optional[int] = None
    cluster_name: Optional[str] = None
    escalation_score: float = 0.0
    priority: str
    mechanism: Optional[str] = None
    location: Optional[str] = None
    reason: str


class DataQualitySummary(BaseModel):
    total_imported: int = 0
    analyzed_count: int = 0
    not_analyzed_count: int = 0
    failed_analysis_count: int = 0
    sif_screened_count: int = 0
    lsr_mapped_count: int = 0
    embedding_coverage_pct: float = 0.0
    clustered_reports_count: int = 0
    field_completeness: Dict[str, float] = Field(default_factory=dict)
