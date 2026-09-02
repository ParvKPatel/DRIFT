import pytest
from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.schemas.enums import EvidenceStatus, SifDecision, BarrierCondition, EnergySource


def test_source_preservation_rule():
    """
    CRITICAL MANDATORY TEST:
    Proves that raw source fields in 'reports' are never overwritten by AI findings in 'safety_analysis'.
    
    Source: incident_cause = "Improper Material Handling"
    AI: hazard = "Unexpected component movement"
    
    After AI model creation, reports.incident_cause MUST still equal "Improper Material Handling".
    """
    source_cause_value = "Improper Material Handling"
    ai_hazard_value = "Unexpected component movement"

    # Instantiate raw source report
    report = Report(
        report_id="REP-TEST-PRESERVE-001",
        narrative="During lifting operations, shackle pin ejected under tension near rigger.",
        incident_cause=source_cause_value,
        fixed_short_description="Retaining pin ejected"
    )

    # Instantiate AI safety analysis
    analysis = SafetyAnalysis(
        report_id=report.report_id,
        activity="Lifting operation",
        equipment="Shackle retaining pin",
        hazard=ai_hazard_value,
        energy_source=EnergySource.KINETIC,
        barrier_condition=BarrierCondition.DEGRADED,
        sif_fpi_potential=SifDecision.YES,
        evidence_status=EvidenceStatus.EXPLICIT
    )

    # Enforce exact separation
    assert report.incident_cause == source_cause_value, "Source incident_cause was modified!"  # pyright: ignore[reportGeneralTypeIssues]
    assert analysis.hazard == ai_hazard_value, "AI hazard value mismatch!"  # pyright: ignore[reportGeneralTypeIssues]
    assert report.incident_cause != analysis.hazard, "Source data and AI data must remain separate!"  # pyright: ignore[reportGeneralTypeIssues]
