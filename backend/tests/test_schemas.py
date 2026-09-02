import pytest
from app.schemas.reports import ReportCreate
from app.schemas.safety_analysis import SafetyAnalysisCreate
from app.schemas.enums import EvidenceStatus, SifDecision, BarrierCondition, PriorityLevel, EnergySource


def test_source_report_schema_validation():
    # Test valid complete report schema
    valid_report_data = {
        "report_id": "REP-2026-001",
        "source_system_id": "SYS-998",
        "site": "Offshore Platform Alpha",
        "unit": "Drilling Rig 4",
        "incident_type": "Near Miss",
        "incident_cause": "Improper Material Handling",
        "narrative": "Pin came out at speed and passed near the rigger during lifting operation.",
        "corrective_action": "Secured pin with secondary retaining clip.",
        "currency": "INR",
        "financial_implication": 0.0
    }
    report = ReportCreate(**valid_report_data)
    assert report.report_id == "REP-2026-001"
    assert report.site == "Offshore Platform Alpha"
    assert report.narrative == "Pin came out at speed and passed near the rigger during lifting operation."
    assert report.preventive_action is None  # Nullable preservation


def test_ai_analysis_schema_validation():
    analysis_data = {
        "report_id": "REP-2026-001",
        "activity": "Material Handling / Rigging",
        "equipment": "Pin & Shackle Assembly",
        "hazard": "Unexpected component movement",
        "energy_source": EnergySource.KINETIC,
        "exposure": "Person in trajectory",
        "exposure_location": "Deck Rigging Area",
        "barrier": "safe positioning",
        "barrier_condition": BarrierCondition.DEGRADED,
        "potential_consequence": "Struck by ejected metal pin",
        "sif_fpi_potential": SifDecision.YES,
        "sif_confidence": 0.88,
        "evidence_status": EvidenceStatus.EXPLICIT,
        "evidence_span": "Pin came out at speed and passed near the rigger",
        "life_saving_rule": "LSR-07",
        "priority_score": 85.0,
        "priority_level": PriorityLevel.HIGH_PRIORITY_SIF_FPI_PRECURSOR
    }
    analysis = SafetyAnalysisCreate(**analysis_data)
    assert analysis.evidence_status == EvidenceStatus.EXPLICIT
    assert analysis.sif_fpi_potential == SifDecision.YES
    assert analysis.priority_level == PriorityLevel.HIGH_PRIORITY_SIF_FPI_PRECURSOR


def test_evidence_enums():
    assert EvidenceStatus.EXPLICIT == "EXPLICIT"
    assert EvidenceStatus.INFERRED == "INFERRED"
    assert EvidenceStatus.UNKNOWN == "UNKNOWN"

    assert SifDecision.YES == "YES"
    assert SifDecision.NO == "NO"
    assert SifDecision.UNCERTAIN == "UNCERTAIN"
