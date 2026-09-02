"""
Phase 6 — Canonical Semantic Text Builder

Generates normalized semantic text representations combining narrative text
with Phase 3 Safety Facts, location/asset details, and Phase 5 Life-Saving Rule.
"""

from typing import Dict, Any, Optional
from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis


class SemanticRepresentationService:
    """Generates canonical semantic text for report embedding and similarity search."""

    VERSION = "v1"

    @classmethod
    def build_canonical_text(
        cls,
        report: Report,
        sa: Optional[SafetyAnalysis] = None,
    ) -> str:
        """
        Builds canonical semantic text string from Report and SafetyAnalysis model fields.
        Does NOT overwrite original report.narrative.
        """
        narrative = report.narrative or report.fixed_short_description or ""
        activity = sa.activity if sa and sa.activity else "UNKNOWN"
        equipment = sa.equipment if sa and sa.equipment else "UNKNOWN"
        hazard = sa.hazard if sa and sa.hazard else "UNKNOWN"
        energy = sa.energy_source.value if sa and sa.energy_source else "UNKNOWN"
        exposure = sa.exposure if sa and sa.exposure else "UNKNOWN"
        location = report.functional_location or report.site or "UNKNOWN"
        barrier = sa.barrier if sa and sa.barrier else "UNKNOWN"
        barrier_cond = sa.barrier_condition.value if sa and sa.barrier_condition else "UNKNOWN"
        consequence = sa.potential_consequence if sa and sa.potential_consequence else "UNKNOWN"
        lsr = sa.primary_life_saving_rule if sa and sa.primary_life_saving_rule else (sa.life_saving_rule if sa and sa.life_saving_rule else "UNKNOWN")

        canonical_text = (
            f"ACTIVITY: {activity}\n"
            f"EQUIPMENT: {equipment}\n"
            f"HAZARD: {hazard}\n"
            f"ENERGY: {energy}\n"
            f"EXPOSURE: {exposure}\n"
            f"LOCATION: {location}\n"
            f"BARRIER: {barrier} ({barrier_cond})\n"
            f"CONSEQUENCE: {consequence}\n"
            f"LSR: {lsr}\n"
            f"NARRATIVE:\n"
            f'"{narrative}"'
        )
        return canonical_text
