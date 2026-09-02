from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, time, datetime
from app.schemas.enums import ProvenanceType, AnalysisStatus, SifDecision, PriorityLevel, ScreeningStatus, LifeSavingRule


class ReportBase(BaseModel):
    report_id: str = Field(..., description="Canonical source report identifier")
    source_system_id: Optional[str] = None
    report_date: Optional[date] = None
    report_time: Optional[time] = None
    site: Optional[str] = None
    unit: Optional[str] = None
    shift: Optional[str] = None
    functional_location: Optional[str] = None
    functional_location_description: Optional[str] = None
    item_no: Optional[str] = None
    incident_type: Optional[str] = None
    incident_sub_type: Optional[str] = None
    incident_cause: Optional[str] = None
    fixed_short_description: Optional[str] = None
    line_item: Optional[str] = None
    narrative: str = Field(..., description="Full verbatim text narrative of the safety report")
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    man_hours: Optional[float] = None
    lost_time: Optional[float] = None
    operational_time_lost: Optional[float] = None
    financial_implication: Optional[float] = None
    currency: Optional[str] = "INR"
    affected_person_type: Optional[str] = None
    employee_or_contractor: Optional[str] = None
    designation: Optional[str] = None
    contractor_name: Optional[str] = None
    actual_outcome: Optional[str] = None
    source_file: Optional[str] = None
    source_row_number: Optional[int] = None
    provenance: Optional[ProvenanceType] = ProvenanceType.OIL_EXPORT
    analysis_status: Optional[AnalysisStatus] = AnalysisStatus.NOT_ANALYZED

    # Intelligence & Screening Fields (Phase 4 & 5)
    sif_fpi_potential: Optional[SifDecision] = None
    screening_status: Optional[ScreeningStatus] = None
    primary_life_saving_rule: Optional[str] = None
    priority_score: Optional[float] = None
    priority_level: Optional[PriorityLevel] = None


class ReportCreate(ReportBase):
    pass


class ReportRead(ReportBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    items: List[ReportRead]
    total: int
    page: int
    size: int
    pages: int


class ReportStatsResponse(BaseModel):
    total_reports: int
    synthetic_count: int
    oil_export_count: int
    sites_count: int
    latest_report_date: Optional[date] = None
    field_completeness: Dict[str, float] = {}
