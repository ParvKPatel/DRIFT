"""
Phase 4 — SIF/FPI Intelligence Engine Comprehensive Test Suite

Tests cover:
1. Rule Engine Unit Tests (RULE-001 to RULE-008)
2. Signal Calculation & Bounding (0.0 to 1.0)
3. Rule Override Logic (critical rules override weak AI signals)
4. UNCERTAIN Handling & Poor Narrative Safety (vague reports -> UNCERTAIN, not false NO)
5. Counterfactual Tests (exposure vs no exposure changes SIF outcome)
6. False-Negative Safety Tests (strong hazard + exposure + low AI confidence -> YES/UNCERTAIN, never silent NO)
7. Source Category Leakage Prevention (narrative/facts drive screening, not source labels)
8. Actual Outcome vs Potential Consequence Distinction
9. API Endpoints Integration Tests (single report screen, get screening, batch screen)
"""

import pytest
import sys
import os

# Ensure backend root and project root are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.schemas.enums import (
    SifDecision,
    EvidenceStatus,
    BarrierCondition,
    EnergySource,
    ScreeningStatus,
)
from app.schemas.sif_screening import SifScreeningResult, ScreeningSignals
from app.services.sif_rule_engine import (
    SafetyRuleEngine,
    Rule001HighEnergyExposure,
    Rule002FallingObject,
    Rule003UnexpectedEjection,
    Rule004SuspendedLoad,
    Rule005ElectricalExposure,
    Rule006PressureRelease,
    Rule007FallFromHeight,
    Rule008CaughtInBetween,
)


# ══════════════════════════════════════════════════════════════════════════════
# 1. RULE ENGINE UNIT TESTS (RULE-001 to RULE-008)
# ══════════════════════════════════════════════════════════════════════════════


class TestDeterministicSafetyRules:

    def test_rule001_high_energy_exposure(self):
        rule = Rule001HighEnergyExposure()
        facts = {
            "energy_source": EnergySource.KINETIC,
            "hazard": "Pin ejection under tension",
            "exposure": "Rigman standing opposite",
            "barrier_condition": BarrierCondition.FAILED,
            "hazard_evidence": "came out at speed",
            "exposure_evidence": "rigger standing nearby",
            "barrier_evidence": "pin failed",
        }
        trigger = rule.evaluate(facts)
        assert trigger is not None
        assert trigger.rule_id == "RULE-001"
        assert trigger.reason_code == "SIF-001"

    def test_rule002_falling_object(self):
        rule = Rule002FallingObject()
        facts = {
            "energy_source": EnergySource.GRAVITATIONAL,
            "hazard": "Dropped object fall from height",
            "exposure": "Worker beneath load zone",
            "exposure_location": "directly below deck grating",
            "hazard_evidence": "shackle fell 10 meters",
            "exposure_evidence": "worker standing beneath",
        }
        trigger = rule.evaluate(facts)
        assert trigger is not None
        assert trigger.rule_id == "RULE-002"
        assert trigger.reason_code == "SIF-007"

    def test_rule003_unexpected_ejection(self):
        rule = Rule003UnexpectedEjection()
        facts = {
            "energy_source": EnergySource.KINETIC,
            "hazard": "Retaining pin came out at speed",
            "exposure": "Rigman in trajectory path",
            "exposure_location": "opposite side of trajectory",
            "hazard_evidence": "came out at speed",
            "exposure_evidence": "rigman nearby",
        }
        trigger = rule.evaluate(facts)
        assert trigger is not None
        assert trigger.rule_id == "RULE-003"
        assert trigger.reason_code == "SIF-002"

    def test_rule004_suspended_load(self):
        rule = Rule004SuspendedLoad()
        facts = {
            "activity": "Lifting container with crane",
            "hazard": "Suspended load movement",
            "equipment": "Deck crane and sling",
            "exposure": "Rigger beneath suspended load",
            "exposure_location": "directly under load path",
        }
        trigger = rule.evaluate(facts)
        assert trigger is not None
        assert trigger.rule_id == "RULE-004"
        assert trigger.reason_code == "SIF-011"

    def test_rule005_electrical_exposure(self):
        rule = Rule005ElectricalExposure()
        facts = {
            "energy_source": EnergySource.ELECTRICAL,
            "hazard": "Live electrical contact hazard",
            "exposure": "Electrician inspecting junction box",
            "barrier_condition": BarrierCondition.ABSENT,
        }
        trigger = rule.evaluate(facts)
        assert trigger is not None
        assert trigger.rule_id == "RULE-005"
        assert trigger.reason_code == "SIF-010"

    def test_rule006_pressure_release(self):
        rule = Rule006PressureRelease()
        facts = {
            "energy_source": EnergySource.PRESSURE,
            "hazard": "High pressure hydraulic pinhole leak under 200 bar",
            "exposure": "Operator testing valve skid",
        }
        trigger = rule.evaluate(facts)
        assert trigger is not None
        assert trigger.rule_id == "RULE-006"
        assert trigger.reason_code == "SIF-012"

    def test_rule007_fall_from_height(self):
        rule = Rule007FallFromHeight()
        facts = {
            "activity": "Working at height on scaffolding",
            "hazard": "Fall from height unprotected edge",
            "exposure": "Scaffolder on platform",
            "barrier_condition": BarrierCondition.FAILED,
        }
        trigger = rule.evaluate(facts)
        assert trigger is not None
        assert trigger.rule_id == "RULE-007"
        assert trigger.reason_code == "SIF-009"

    def test_rule008_caught_in_between(self):
        rule = Rule008CaughtInBetween()
        facts = {
            "energy_source": EnergySource.MECHANICAL,
            "hazard": "Caught in pinch point between rotating winch drum",
            "exposure": "Deck operator guiding cable",
        }
        trigger = rule.evaluate(facts)
        assert trigger is not None
        assert trigger.rule_id == "RULE-008"
        assert trigger.reason_code == "SIF-008"


# ══════════════════════════════════════════════════════════════════════════════
# 2. SIGNAL CALCULATION & BOUNDING TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestSignalCalculation:

    def test_signals_within_bounds_zero_to_one(self):
        engine = SafetyRuleEngine()
        facts = {
            "energy_source": EnergySource.KINETIC,
            "hazard": "Pin ejection",
            "exposure": "Rigman nearby",
            "exposure_location": "trajectory",
            "barrier_condition": BarrierCondition.FAILED,
            "potential_consequence": "Serious struck-by injury",
            "activity_confidence": 0.9,
            "hazard_confidence": 0.85,
        }
        narrative = "The pin came out at speed passing nearby to the rigman."
        res = engine.screen("TEST-SIG-01", facts, narrative)

        assert 0.0 <= res.signals.mechanism_signal <= 1.0
        assert 0.0 <= res.signals.exposure_signal <= 1.0
        assert 0.0 <= res.signals.barrier_signal <= 1.0
        assert 0.0 <= res.signals.consequence_signal <= 1.0
        assert 0.0 <= res.signals.evidence_signal <= 1.0

    def test_no_fake_probability_of_death_fields(self):
        """Phase 4 screening response MUST NOT contain fake probability of death metrics."""
        engine = SafetyRuleEngine()
        facts = {"hazard": "None"}
        res = engine.screen("TEST-SIG-02", facts, "Routine housekeeping")
        assert not hasattr(res, "probability_of_death")
        assert not hasattr(res, "fatality_percentage")


# ══════════════════════════════════════════════════════════════════════════════
# 3. COUNTERFACTUAL TESTS (EXPOSURE MATTERS)
# ══════════════════════════════════════════════════════════════════════════════


class TestCounterfactualScenarios:
    """Demonstrates that human exposure directly changes SIF outcome."""

    def test_counterfactual_exposure_vs_no_exposure(self):
        engine = SafetyRuleEngine()

        # Scenario A: Pin ejects WITH human exposure in trajectory
        facts_exposed = {
            "energy_source": EnergySource.KINETIC,
            "hazard": "Pin ejected under pressure",
            "exposure": "Rigman standing in trajectory path",
            "exposure_location": "opposite side of trajectory",
            "barrier_condition": BarrierCondition.FAILED,
            "potential_consequence": "Serious struck-by injury",
            "hazard_confidence": 0.9,
        }
        narr_a = "The pin came out at speed passing nearby to the rigman."
        res_a = engine.screen("TEST-CF-A", facts_exposed, narr_a)

        # Scenario B: Same pin ejection WITHOUT human exposure (controlled zone)
        facts_unexposed = {
            "energy_source": EnergySource.KINETIC,
            "hazard": "Pin ejected under pressure",
            "exposure": "none",
            "exposure_location": "empty exclusion zone",
            "barrier_condition": BarrierCondition.INTACT,
            "potential_consequence": "No injury potential",
            "hazard_confidence": 0.9,
        }
        narr_b = "During pin removal in barricaded area, pin released inside empty enclosure with no personnel present."
        res_b = engine.screen("TEST-CF-B", facts_unexposed, narr_b)

        assert res_a.sif_fpi_potential == SifDecision.YES, "Exposed scenario must trigger SIF = YES"
        assert res_b.sif_fpi_potential in (SifDecision.NO, SifDecision.UNCERTAIN), "Unexposed scenario must not trigger SIF = YES"
        assert res_a.signals.exposure_signal > res_b.signals.exposure_signal, "Exposure signal must be higher for Scenario A"


# ══════════════════════════════════════════════════════════════════════════════
# 4. FALSE-NEGATIVE SAFETY TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestFalseNegativeSafety:
    """Ensures critical safety rules override low extraction confidence to prevent silent false negatives."""

    def test_rule_override_prevents_false_negative_on_low_confidence(self):
        engine = SafetyRuleEngine()

        # Strong high-energy mechanism + human exposure + failed barrier, BUT low AI confidence
        facts = {
            "energy_source": EnergySource.KINETIC,
            "hazard": "Retaining pin came out at speed",
            "exposure": "Rigman in trajectory path",
            "barrier_condition": BarrierCondition.FAILED,
            "hazard_confidence": 0.20,  # AI extraction was uncertain
            "exposure_confidence": 0.15,
        }
        narrative = "Pin came out at speed near rigman."
        res = engine.screen("TEST-FN-01", facts, narrative)

        assert res.sif_fpi_potential != SifDecision.NO, (
            "Critical safety rule MUST NOT silently fall through to NO when high energy & exposure are present!"
        )
        assert len(res.rule_ids_triggered) > 0, "Deterministic safety rule MUST trigger override."


# ══════════════════════════════════════════════════════════════════════════════
# 5. POOR NARRATIVE & UNCERTAIN HANDLING TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestPoorNarrativeHandling:

    def test_vague_narrative_yields_uncertain_not_no(self):
        engine = SafetyRuleEngine()
        facts = {
            "hazard": None,
            "exposure": None,
            "equipment": None,
        }
        vague_narrative = "Worker was unsafe today."
        res = engine.screen("TEST-VAGUE-01", facts, vague_narrative)

        assert res.sif_fpi_potential == SifDecision.UNCERTAIN
        assert res.review_required is True
        assert "SIF-013" in res.reason_codes

    def test_missing_exposure_on_hazard_yields_uncertain(self):
        engine = SafetyRuleEngine()
        facts = {
            "energy_source": EnergySource.PRESSURE,
            "hazard": "High pressure steam line leakage",
            "exposure": None,
            "exposure_evidence_status": EvidenceStatus.UNKNOWN,
            "barrier_condition": BarrierCondition.UNKNOWN,
        }
        narrative = "Steam leakage noticed near compressor area during inspection."
        res = engine.screen("TEST-UNCERTAIN-02", facts, narrative)

        assert res.sif_fpi_potential == SifDecision.UNCERTAIN
        assert res.review_required is True


# ══════════════════════════════════════════════════════════════════════════════
# 6. SOURCE CATEGORY LEAKAGE PREVENTION TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestSourceCategoryLeakagePrevention:
    """Verifies that extracted safety facts & narrative drive screening, not source category labels."""

    def test_eyewash_unsafe_condition_not_classified_as_sif(self):
        engine = SafetyRuleEngine()
        facts = {
            "activity": "Eyewash station weekly check",
            "equipment": "Eyewash station EW-03",
            "hazard": "Low water pressure in eyewash station",
            "energy_source": EnergySource.UNKNOWN,
            "exposure": "None",
            "barrier_condition": BarrierCondition.ABSENT,
            "potential_consequence": "Delayed eye flushing",
        }
        narrative = "Weekly inspection revealed low water flow at eyewash station."
        res = engine.screen("TEST-LEAK-01", facts, narrative)

        assert res.sif_fpi_potential == SifDecision.NO

    def test_trip_hazard_unsafe_condition_not_classified_as_sif(self):
        engine = SafetyRuleEngine()
        facts = {
            "activity": "Housekeeping walkthrough",
            "equipment": "Extension cable",
            "hazard": "Trip hazard across walkway",
            "energy_source": EnergySource.UNKNOWN,
            "exposure": "Passing operator",
            "barrier_condition": BarrierCondition.DEGRADED,
            "potential_consequence": "Trip and fall",
        }
        narrative = "Operator noticed extension cable laid across main walkway without ramp."
        res = engine.screen("TEST-LEAK-02", facts, narrative)

        assert res.sif_fpi_potential in (SifDecision.NO, SifDecision.UNCERTAIN)


# ══════════════════════════════════════════════════════════════════════════════
# 7. ACTUAL OUTCOME VS POTENTIAL CONSEQUENCE TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestActualOutcomeVsPotentialConsequence:

    def test_no_actual_injury_does_not_prevent_sif_yes(self):
        """Absence of actual injury ('Near Miss - No injury') MUST NOT lower SIF potential to NO."""
        engine = SafetyRuleEngine()
        facts = {
            "energy_source": EnergySource.KINETIC,
            "hazard": "Pin ejected at high velocity",
            "exposure": "Rigman standing in trajectory",
            "barrier_condition": BarrierCondition.FAILED,
            "potential_consequence": "Person could have been killed or seriously injured by ejected pin",
        }
        narrative = "Pin came out at speed near rigman. Actual outcome: No injury recorded."
        res = engine.screen("TEST-OUTCOME-01", facts, narrative)

        assert res.sif_fpi_potential == SifDecision.YES, (
            "Near Miss with high energy & exposure MUST be classified as SIF = YES even with zero actual injury!"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 8. API INTEGRATION TESTS (using in-memory SQLite via async_client)
# ══════════════════════════════════════════════════════════════════════════════


class TestSifScreeningApi:

    @pytest.fixture
    async def seeded_report_id(self, async_client):
        """Seed demo data and return SYN-2026-001 report_id."""
        await async_client.post("/api/v1/reports/seed")
        return "SYN-2026-001"

    @pytest.mark.asyncio
    async def test_screen_report_endpoint_returns_200(self, async_client, seeded_report_id):
        resp = await async_client.post(
            f"/api/v1/reports/{seeded_report_id}/screen-sif",
            json={"force_rescreen": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_id"] == seeded_report_id
        assert data["sif_fpi_potential"] in ("YES", "NO", "UNCERTAIN")
        assert "signals" in data
        assert "rule_ids_triggered" in data

    @pytest.mark.asyncio
    async def test_pin_ejection_report_screens_yes(self, async_client, seeded_report_id):
        """SYN-2026-001 (pin ejection) must be screened as SIF = YES."""
        resp = await async_client.post(
            f"/api/v1/reports/{seeded_report_id}/screen-sif",
            json={"force_rescreen": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["sif_fpi_potential"] == "YES"
        assert len(data["rule_ids_triggered"]) > 0

    @pytest.mark.asyncio
    async def test_get_sif_analysis_endpoint(self, async_client, seeded_report_id):
        # First screen it
        await async_client.post(
            f"/api/v1/reports/{seeded_report_id}/screen-sif",
            json={"force_rescreen": True},
        )
        # Then fetch existing result
        resp = await async_client.get(f"/api/v1/reports/{seeded_report_id}/sif-analysis")
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_id"] == seeded_report_id

    @pytest.mark.asyncio
    async def test_batch_sif_screening_endpoint(self, async_client, seeded_report_id):
        resp = await async_client.post(
            "/api/v1/reports/screen-sif",
            json={
                "report_ids": [seeded_report_id],
                "force_rescreen": True,
                "batch_size": 1,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["requested"] == 1
        assert data["succeeded"] == 1

    @pytest.mark.asyncio
    async def test_screen_nonexistent_report_returns_404(self, async_client):
        resp = await async_client.post(
            "/api/v1/reports/NONEXISTENT-REPORT-999/screen-sif",
            json={"force_rescreen": False},
        )
        assert resp.status_code == 404
