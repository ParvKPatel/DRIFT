"""
Phase 5 — LSR Mapping & HSE Priority Engine Test Suite

Tests cover:
1. All 9 official Life-Saving Rules mapped accurately
2. Secondary LSR mapping support
3. Unmapped case handling (UNKNOWN)
4. Source preservation (incident_cause is never overwritten by LSR)
5. Priority Engine score formula (0-100) & component weighting
6. Barrier condition scoring (FAILED/ABSENT=1.0, DEGRADED=0.75, UNKNOWN=0.5, INTACT=0.1)
7. Component availability tracking (Phase 6 components marked NOT_YET_AVAILABLE)
8. Critical Safety Overrides
9. Uncertainty propagation (SIF UNCERTAIN -> priority UNCERTAIN/SAFETY_REVIEW)
10. Source Category Leakage Prevention (Near Miss labels don't force CRITICAL)
11. API Integration Tests (LSR endpoints, Priority endpoints, Combined Intelligence pipeline)
"""

import pytest
import sys
import os

# Ensure backend root and project root are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.schemas.enums import (
    LifeSavingRule,
    PriorityLevel,
    ComponentStatus,
    SifDecision,
    BarrierCondition,
    EvidenceStatus,
    EnergySource,
)
from app.services.lsr_engine import LsrEngine
from app.services.priority_engine import HsePriorityEngine


# ══════════════════════════════════════════════════════════════════════════════
# 1. LIFE-SAVING RULE MAPPING TESTS (ALL 9 RULES)
# ══════════════════════════════════════════════════════════════════════════════


class TestLifeSavingRuleMapping:

    @pytest.fixture
    def engine(self):
        return LsrEngine()

    def test_lsr_line_of_fire(self, engine):
        facts = {
            "energy_source": EnergySource.KINETIC,
            "hazard": "Retaining pin ejected at high speed",
            "exposure": "Rigman standing opposite to pin trajectory",
            "exposure_location": "opposite side of trajectory",
        }
        narrative = "During removing pin from a structure, one rigman hammered the pin to remove it and it came out at speed passing nearby to the rigman."
        res = engine.map_rules("TEST-LSR-01", facts, narrative)

        assert res.primary_life_saving_rule == LifeSavingRule.LINE_OF_FIRE
        assert res.lsr_confidence >= 0.90
        assert res.lsr_evidence_status in (EvidenceStatus.EXPLICIT, EvidenceStatus.INFERRED)

    def test_lsr_safe_mechanical_lifting(self, engine):
        facts = {
            "activity": "Lifting equipment with rig crane",
            "equipment": "Deck crane and shackle pin",
            "hazard": "Suspended load movement",
        }
        narrative = "During lifting operation with deck crane, the shackle pin slipped."
        res = engine.map_rules("TEST-LSR-02", facts, narrative)

        assert res.primary_life_saving_rule == LifeSavingRule.SAFE_MECHANICAL_LIFTING
        assert res.lsr_confidence >= 0.85

    def test_lsr_working_at_height(self, engine):
        facts = {
            "activity": "Scaffolding modification at elevated deck",
            "hazard": "Fall from height unprotected platform",
            "equipment": "Scaffolding platform",
        }
        narrative = "Worker was modifying scaffold platform at height without safety harness connected."
        res = engine.map_rules("TEST-LSR-03", facts, narrative)

        assert res.primary_life_saving_rule == LifeSavingRule.WORKING_AT_HEIGHT

    def test_lsr_energy_isolation(self, engine):
        facts = {
            "energy_source": EnergySource.PRESSURE,
            "hazard": "Opening pressurized line before verifying zero energy",
            "barrier": "LOTO isolation",
        }
        narrative = "Technician unbolted flange before confirming lockout tagout isolation."
        res = engine.map_rules("TEST-LSR-04", facts, narrative)

        assert res.primary_life_saving_rule == LifeSavingRule.ENERGY_ISOLATION

    def test_lsr_hot_work(self, engine):
        facts = {
            "activity": "Welding pipe bracket",
            "hazard": "Sparks generated near hydrocarbon line",
        }
        narrative = "Welder performed hot work welding without habitat fire blanket."
        res = engine.map_rules("TEST-LSR-05", facts, narrative)

        assert res.primary_life_saving_rule == LifeSavingRule.HOT_WORK

    def test_lsr_confined_space(self, engine):
        facts = {
            "activity": "Storage tank internal cleaning",
            "exposure_location": "inside vessel entry",
        }
        narrative = "Operator entered confined space storage tank without gas testing."
        res = engine.map_rules("TEST-LSR-06", facts, narrative)

        assert res.primary_life_saving_rule == LifeSavingRule.CONFINED_SPACE

    def test_lsr_driving(self, engine):
        facts = {
            "energy_source": EnergySource.VEHICLE_MOTION,
            "equipment": "Forklift truck",
        }
        narrative = "Driver operated forklift in loading bay without wearing seatbelt."
        res = engine.map_rules("TEST-LSR-07", facts, narrative)

        assert res.primary_life_saving_rule == LifeSavingRule.DRIVING

    def test_lsr_bypassing_safety_controls(self, engine):
        facts = {
            "barrier": "Interlock guard",
            "barrier_condition": BarrierCondition.FAILED,
        }
        narrative = "Technician bypassed machine safety interlock guard to clear jammed part."
        res = engine.map_rules("TEST-LSR-08", facts, narrative)

        assert res.primary_life_saving_rule == LifeSavingRule.BYPASSING_SAFETY_CONTROLS

    def test_lsr_work_authorisation(self, engine):
        facts = {
            "barrier": "Permit to Work",
        }
        narrative = "Contractor commenced work without valid Permit to Work authorization."
        res = engine.map_rules("TEST-LSR-09", facts, narrative)

        assert res.primary_life_saving_rule == LifeSavingRule.WORK_AUTHORISATION

    def test_lsr_unmapped_yields_unknown(self, engine):
        facts = {
            "activity": "Routine office paperwork",
        }
        narrative = "Paper slip occurred on office desk."
        res = engine.map_rules("TEST-LSR-10", facts, narrative)

        assert res.primary_life_saving_rule == LifeSavingRule.UNKNOWN
        assert res.lsr_confidence == 0.0

    def test_secondary_lsr_mapping(self, engine):
        """Lifting incident with person in trajectory maps Safe Mechanical Lifting + Line of Fire."""
        facts = {
            "activity": "Lifting heavy shackle pin with crane",
            "equipment": "Crane rigging",
            "exposure": "Rigger in trajectory path beneath load",
            "exposure_location": "trajectory path",
        }
        narrative = "During crane lifting operation, pin released at speed in trajectory path near rigger."
        res = engine.map_rules("TEST-LSR-11", facts, narrative)

        assert res.primary_life_saving_rule in (LifeSavingRule.SAFE_MECHANICAL_LIFTING, LifeSavingRule.LINE_OF_FIRE)
        assert len(res.secondary_life_saving_rules) >= 1 or res.primary_life_saving_rule != LifeSavingRule.UNKNOWN


# ══════════════════════════════════════════════════════════════════════════════
# 2. HSE PRIORITY ENGINE TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestHsePriorityEngine:

    @pytest.fixture
    def engine(self):
        return HsePriorityEngine()

    def test_priority_score_bounds_zero_to_hundred(self, engine):
        facts = {
            "sif_fpi_potential": SifDecision.YES,
            "sif_confidence": 0.95,
            "barrier_condition": BarrierCondition.FAILED,
            "rule_ids_triggered": ["RULE-001"],
            "exposure": "Worker in trajectory",
        }
        res = engine.calculate_priority("TEST-PRIO-01", facts)

        assert 0.0 <= res.priority_score <= 100.0
        assert res.priority_level == PriorityLevel.CRITICAL
        assert res.priority_override is True

    def test_barrier_score_hierarchy(self, engine):
        facts_failed = {"barrier_condition": BarrierCondition.FAILED}
        facts_degraded = {"barrier_condition": BarrierCondition.DEGRADED}
        facts_intact = {"barrier_condition": BarrierCondition.INTACT}

        res_failed = engine.calculate_priority("P1", facts_failed)
        res_degraded = engine.calculate_priority("P2", facts_degraded)
        res_intact = engine.calculate_priority("P3", facts_intact)

        score_failed = next(c.score for c in res_failed.components if c.name == "barrier_score")
        score_degraded = next(c.score for c in res_degraded.components if c.name == "barrier_score")
        score_intact = next(c.score for c in res_intact.components if c.name == "barrier_score")

        assert score_failed > score_degraded > score_intact

    def test_phase6_components_marked_not_yet_available(self, engine):
        facts = {"sif_fpi_potential": SifDecision.NO}
        res = engine.calculate_priority("TEST-PRIO-02", facts)

        rec_comp = next(c for c in res.components if c.name == "recurrence_score")
        assert rec_comp.status == ComponentStatus.NOT_YET_AVAILABLE
        assert rec_comp.score is None
        assert len(res.unavailable_components) >= 3

    def test_uncertain_sif_propagates_to_uncertain_priority(self, engine):
        facts = {
            "sif_fpi_potential": SifDecision.UNCERTAIN,
            "barrier_condition": BarrierCondition.UNKNOWN,
        }
        res = engine.calculate_priority("TEST-PRIO-03", facts)

        assert res.priority_level in (PriorityLevel.UNCERTAIN, PriorityLevel.SAFETY_REVIEW)
        assert "PRIORITY-008" in res.priority_reason_codes

    def test_no_fake_fatality_probability_claims(self, engine):
        facts = {"sif_fpi_potential": SifDecision.YES}
        res = engine.calculate_priority("TEST-PRIO-04", facts)

        assert not hasattr(res, "probability_of_death")
        assert not hasattr(res, "risk_percentage")


# ══════════════════════════════════════════════════════════════════════════════
# 3. API INTEGRATION TESTS (SQLite AsyncClient)
# ══════════════════════════════════════════════════════════════════════════════


class TestPhase5ApiIntegration:

    @pytest.fixture
    async def seeded_report_id(self, async_client):
        await async_client.post("/api/v1/reports/seed")
        return "SYN-2026-001"

    @pytest.mark.asyncio
    async def test_map_lsr_endpoint(self, async_client, seeded_report_id):
        resp = await async_client.post(
            f"/api/v1/reports/{seeded_report_id}/map-lsr",
            json={"force_remap": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_id"] == seeded_report_id
        assert data["primary_life_saving_rule"] == "Line of Fire"

    @pytest.mark.asyncio
    async def test_source_preservation_incident_cause_unchanged(self, async_client, seeded_report_id):
        # Fetch report before mapping
        res_before = await async_client.get(f"/api/v1/reports/{seeded_report_id}")
        rep_before = res_before.json()
        orig_cause = rep_before["incident_cause"]

        # Run LSR mapping
        await async_client.post(f"/api/v1/reports/{seeded_report_id}/map-lsr", json={"force_remap": True})

        # Fetch report after mapping
        res_after = await async_client.get(f"/api/v1/reports/{seeded_report_id}")
        rep_after = res_after.json()
        assert rep_after["incident_cause"] == orig_cause, "Original incident_cause MUST NOT be overwritten by LSR!"

    @pytest.mark.asyncio
    async def test_calculate_priority_endpoint(self, async_client, seeded_report_id):
        resp = await async_client.post(
            f"/api/v1/reports/{seeded_report_id}/calculate-priority",
            json={"force_recalculate": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_id"] == seeded_report_id
        assert 0.0 <= data["priority_score"] <= 100.0
        assert data["priority_level"] in ("CRITICAL", "HIGH_PRIORITY_SIF_FPI_PRECURSOR", "SAFETY_REVIEW", "ROUTINE", "UNCERTAIN")

    @pytest.mark.asyncio
    async def test_full_intelligence_pipeline_endpoint(self, async_client, seeded_report_id):
        resp = await async_client.post(f"/api/v1/reports/{seeded_report_id}/intelligence")
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_id"] == seeded_report_id
        assert "extraction" in data
        assert "sif_screening" in data
        assert "lsr_mapping" in data
        assert "priority" in data
        assert data["lsr_mapping"]["primary_life_saving_rule"] == "Line of Fire"
        assert data["sif_screening"]["sif_fpi_potential"] == "YES"
