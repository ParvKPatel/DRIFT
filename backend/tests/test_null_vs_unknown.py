import pytest
from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.schemas.enums import EvidenceStatus, SifDecision, BarrierCondition, EnergySource


def test_null_vs_unknown_distinction():
    """
    CRITICAL MANDATORY TEST:
    Proves the system distinguishes missing source data (NULL / None)
    from AI-derived analytical uncertainty (UNKNOWN).
    
    Example:
    Pressure is not mentioned in source report narrative.
    Source field (e.g. man_hours, unit) is missing -> None (NULL).
    AI analytical uncertainty -> EnergySource.UNKNOWN / EvidenceStatus.UNKNOWN.
    """
    # Source report with missing optional fields
    report = Report(
        report_id="REP-TEST-NULL-001",
        narrative="Pin came out at speed during rigging.",
        site="Offshore Platform Alpha",
        unit=None,        # Missing source data MUST be None (NULL)
        man_hours=None,   # Missing source data MUST be None (NULL)
        lost_time=None    # Missing source data MUST be None (NULL)
    )

    # AI analysis for report with unmentioned pressure
    analysis = SafetyAnalysis(
        report_id=report.report_id,
        hazard="Component ejection",
        energy_source=EnergySource.UNKNOWN,       # Analytical uncertainty
        barrier_condition=BarrierCondition.UNKNOWN, # Analytical uncertainty
        evidence_status=EvidenceStatus.UNKNOWN,     # Analytical uncertainty
        sif_fpi_potential=SifDecision.UNCERTAIN
    )

    # Assert missing source data is None (NULL), NOT string "Unknown" or "N/A"
    assert report.unit is None, "Missing source unit should be None (NULL)"
    assert report.man_hours is None, "Missing source man_hours should be None (NULL)"
    assert report.lost_time is None, "Missing source lost_time should be None (NULL)"

    # Assert AI uncertainty uses explicit UNKNOWN enum
    assert analysis.energy_source == EnergySource.UNKNOWN  # pyright: ignore[reportGeneralTypeIssues]
    assert analysis.barrier_condition == BarrierCondition.UNKNOWN  # pyright: ignore[reportGeneralTypeIssues]
    assert analysis.evidence_status == EvidenceStatus.UNKNOWN  # pyright: ignore[reportGeneralTypeIssues]
    assert analysis.sif_fpi_potential == SifDecision.UNCERTAIN  # pyright: ignore[reportGeneralTypeIssues]
