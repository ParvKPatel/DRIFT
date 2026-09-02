"""
Phase 3 — Safety Fact Extraction Test Suite

Tests cover:
1. Pydantic extraction schema validation & UNKNOWN handling
2. FactField confidence bounds & enum validation
3. MockSafetyExtractionProvider structured output
4. Evidence text & offset calculation
5. SafetyExtractionService via in-memory SQLite DB
6. API endpoints: analyze one report, analyze nonexistent, fetch analysis, batch
7. Source field preservation after analysis
8. Analysis status lifecycle
9. Provider fallback when AI_API_KEY missing
10. Malformed / empty output handling
"""

import pytest
import sys
import os
from typing import Any

# Ensure the backend app is importable from tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.safety_extraction import (
    SafetyFactsExtractionResponse,
    FactField,
    AnalysisRequest,
    BatchAnalysisRequest,
    EvidenceItemResponse,
)
from app.schemas.enums import (
    EvidenceStatus,
    BarrierCondition,
    EnergySource,
    AnalysisStatus,
)
from app.services.extraction_service import _calculate_offsets


# ══════════════════════════════════════════════════════════════════════════════
# 1. SCHEMA TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestFactFieldSchema:
    def test_default_fact_field_is_unknown(self):
        ff = FactField()
        assert ff.value is None
        assert ff.evidence is None
        assert ff.evidence_status == EvidenceStatus.UNKNOWN
        assert ff.confidence == 0.0
        assert ff.start_offset is None
        assert ff.end_offset is None

    def test_explicit_fact_field(self):
        ff = FactField(
            value="Drilling operation",
            evidence="during drilling of the well",
            evidence_status=EvidenceStatus.EXPLICIT,
            confidence=0.92,
            start_offset=6,
            end_offset=31,
        )
        assert ff.value == "Drilling operation"
        assert ff.evidence_status == EvidenceStatus.EXPLICIT
        assert ff.confidence == 0.92
        assert ff.start_offset == 6
        assert ff.end_offset == 31

    def test_inferred_fact_field(self):
        ff = FactField(
            value="worker",
            evidence_status=EvidenceStatus.INFERRED,
            confidence=0.65,
        )
        assert ff.evidence_status == EvidenceStatus.INFERRED
        assert ff.confidence == 0.65

    def test_confidence_clamped_to_zero(self):
        """Confidence below 0.0 should be rejected by Pydantic validator."""
        with pytest.raises(Exception):
            FactField(confidence=-0.1)

    def test_confidence_clamped_to_one(self):
        """Confidence above 1.0 should be rejected by Pydantic validator."""
        with pytest.raises(Exception):
            FactField(confidence=1.1)

    def test_confidence_boundary_zero(self):
        ff = FactField(confidence=0.0)
        assert ff.confidence == 0.0

    def test_confidence_boundary_one(self):
        ff = FactField(confidence=1.0)
        assert ff.confidence == 1.0

    def test_unknown_evidence_status(self):
        ff = FactField(evidence_status=EvidenceStatus.UNKNOWN)
        assert ff.evidence_status == EvidenceStatus.UNKNOWN


class TestSafetyFactsExtractionResponseSchema:
    def _make_explicit_fact(self, value: str) -> FactField:
        return FactField(
            value=value,
            evidence="some text",
            evidence_status=EvidenceStatus.EXPLICIT,
            confidence=0.8,
        )

    def test_empty_response_all_unknown(self):
        resp = SafetyFactsExtractionResponse()
        assert resp.activity.value is None
        assert resp.activity.evidence_status == EvidenceStatus.UNKNOWN
        assert resp.energy_source.value is None
        assert resp.barrier_condition.value is None
        assert resp.is_mock is False

    def test_all_nine_fields_populated(self):
        resp = SafetyFactsExtractionResponse(
            activity=self._make_explicit_fact("Pin removal"),
            equipment=self._make_explicit_fact("Structural pin"),
            hazard=self._make_explicit_fact("Pin ejection"),
            energy_source=FactField(
                value=EnergySource.KINETIC,
                evidence="came out at speed",
                evidence_status=EvidenceStatus.EXPLICIT,
                confidence=0.90,
            ),
            exposure=self._make_explicit_fact("Rigman in trajectory"),
            exposure_location=self._make_explicit_fact("Near ejection path"),
            barrier=self._make_explicit_fact("Exclusion zone"),
            barrier_condition=FactField(
                value=BarrierCondition.FAILED,
                evidence_status=EvidenceStatus.INFERRED,
                confidence=0.75,
            ),
            potential_consequence=self._make_explicit_fact("Struck-by serious injury"),
        )
        assert resp.activity.value == "Pin removal"
        assert resp.energy_source.value == EnergySource.KINETIC
        assert resp.barrier_condition.value == BarrierCondition.FAILED
        assert resp.is_mock is False

    def test_mock_flag_set(self):
        resp = SafetyFactsExtractionResponse(
            is_mock=True,
            extraction_notes="[DEMO] Mock heuristic result",
        )
        assert resp.is_mock is True

    def test_energy_source_unknown_valid(self):
        resp = SafetyFactsExtractionResponse(
            energy_source=FactField(value=EnergySource.UNKNOWN)
        )
        assert resp.energy_source.value == EnergySource.UNKNOWN

    def test_barrier_condition_absent(self):
        resp = SafetyFactsExtractionResponse(
            barrier_condition=FactField(
                value=BarrierCondition.ABSENT,
                evidence_status=EvidenceStatus.INFERRED,
                confidence=0.7,
            )
        )
        assert resp.barrier_condition.value == BarrierCondition.ABSENT

    def test_sif_field_not_present(self):
        """Phase 3 schema must NOT contain SIF/FPI fields."""
        resp = SafetyFactsExtractionResponse()
        assert not hasattr(resp, "sif_fpi_potential"), (
            "SIF/FPI field must NOT exist in Phase 3 extraction schema"
        )
        assert not hasattr(resp, "priority_score"), (
            "Priority score must NOT exist in Phase 3 extraction schema"
        )
        assert not hasattr(resp, "life_saving_rule"), (
            "LSR must NOT exist in Phase 3 extraction schema"
        )


class TestAnalysisStatusEnum:
    def test_all_states_present(self):
        states = {s.value for s in AnalysisStatus}
        assert "NOT_ANALYZED" in states
        assert "PROCESSING" in states
        assert "COMPLETED" in states
        assert "FAILED" in states
        assert "NEEDS_REVIEW" in states

    def test_not_analyzed_is_not_ai_clear(self):
        """NOT_ANALYZED means the AI has not run, NOT 'AI found no hazard'."""
        assert AnalysisStatus.NOT_ANALYZED != AnalysisStatus.COMPLETED


class TestBarrierConditionEnum:
    def test_all_values(self):
        values = {c.value for c in BarrierCondition}
        assert values == {"INTACT", "DEGRADED", "FAILED", "ABSENT", "UNKNOWN"}


class TestEnergySourceEnum:
    def test_contains_required_sources(self):
        values = {e.value for e in EnergySource}
        for required in ("MECHANICAL", "KINETIC", "GRAVITATIONAL", "PRESSURE",
                         "ELECTRICAL", "THERMAL", "CHEMICAL", "HYDROCARBON",
                         "STORED_ENERGY", "VEHICLE_MOTION", "UNKNOWN"):
            assert required in values, f"Missing energy source: {required}"


# ══════════════════════════════════════════════════════════════════════════════
# 2. EVIDENCE OFFSET CALCULATION TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestEvidenceOffsets:
    NARRATIVE = "During removing pin from a structure, one rigman hammered the pin to remove it and it came out at speed passing nearby to the rigman."

    def test_exact_match_found(self):
        start, end = _calculate_offsets(self.NARRATIVE, "came out at speed")
        assert start is not None
        assert end is not None
        assert self.NARRATIVE[start:end] == "came out at speed"

    def test_case_insensitive_match(self):
        start, end = _calculate_offsets(self.NARRATIVE, "CAME OUT AT SPEED")
        assert start is not None
        # Original text at offset should be original case
        assert self.NARRATIVE[start:end].lower() == "came out at speed"

    def test_not_found_returns_none(self):
        start, end = _calculate_offsets(self.NARRATIVE, "hydraulic pressure release")
        assert start is None
        assert end is None

    def test_empty_evidence_returns_none(self):
        start, end = _calculate_offsets(self.NARRATIVE, "")
        assert start is None
        assert end is None

    def test_empty_narrative_returns_none(self):
        start, end = _calculate_offsets("", "pin")
        assert start is None
        assert end is None

    def test_none_narrative_returns_none(self):
        start, end = _calculate_offsets(None, "pin")  # type: ignore
        assert start is None
        assert end is None

    def test_none_evidence_returns_none(self):
        start, end = _calculate_offsets(self.NARRATIVE, None)  # type: ignore
        assert start is None
        assert end is None

    def test_offset_range_correct(self):
        evidence = "rigman"
        start, end = _calculate_offsets(self.NARRATIVE, evidence)
        assert start is not None
        assert end == start + len(evidence)


# ══════════════════════════════════════════════════════════════════════════════
# 3. MOCK PROVIDER TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestMockSafetyExtractionProvider:
    """Tests that MockSafetyExtractionProvider returns valid structured output."""

    @pytest.fixture
    def provider(self):
        from ai.providers.mock import MockSafetyExtractionProvider
        return MockSafetyExtractionProvider()

    @pytest.mark.asyncio
    async def test_returns_safety_facts_response(self, provider):
        narrative = "During removing pin from a structure, one rigman hammered the pin to remove it and it came out at speed passing nearby to the rigman."
        result = await provider.extract_safety_facts(narrative)
        assert isinstance(result, SafetyFactsExtractionResponse)

    @pytest.mark.asyncio
    async def test_is_mock_flag_set(self, provider):
        result = await provider.extract_safety_facts("worker near the crane")
        assert result.is_mock is True

    @pytest.mark.asyncio
    async def test_all_nine_fact_fields_present(self, provider):
        result = await provider.extract_safety_facts("During removing pin, the rigman was nearby when the pin came out at speed.")
        assert result.activity is not None
        assert result.equipment is not None
        assert result.hazard is not None
        assert result.energy_source is not None
        assert result.exposure is not None
        assert result.exposure_location is not None
        assert result.barrier is not None
        assert result.barrier_condition is not None
        assert result.potential_consequence is not None

    @pytest.mark.asyncio
    async def test_pin_narrative_extracts_kinetic_energy(self, provider):
        narrative = "The pin came out at speed and passed nearby to the rigman."
        result = await provider.extract_safety_facts(narrative)
        assert result.energy_source.value == EnergySource.KINETIC

    @pytest.mark.asyncio
    async def test_hydraulic_narrative_extracts_pressure_energy(self, provider):
        narrative = "A hydraulic hose burst during operations, spraying fluid."
        result = await provider.extract_safety_facts(narrative)
        assert result.energy_source.value == EnergySource.PRESSURE

    @pytest.mark.asyncio
    async def test_unknown_narrative_returns_unknowns(self, provider):
        narrative = "Something happened today at the site."
        result = await provider.extract_safety_facts(narrative)
        # At minimum energy_source and barrier_condition should be UNKNOWN for vague narrative
        assert result.energy_source.evidence_status in (EvidenceStatus.UNKNOWN, EvidenceStatus.INFERRED)

    @pytest.mark.asyncio
    async def test_confidence_within_bounds(self, provider):
        narrative = "During removing pin from a structure, the rigman was hit by the pin."
        result = await provider.extract_safety_facts(narrative)
        for field_name in ("activity", "equipment", "hazard", "energy_source",
                           "exposure", "exposure_location", "barrier",
                           "barrier_condition", "potential_consequence"):
            ff = getattr(result, field_name)
            assert 0.0 <= ff.confidence <= 1.0, (
                f"Confidence out of bounds for field '{field_name}': {ff.confidence}"
            )

    @pytest.mark.asyncio
    async def test_evidence_text_from_narrative(self, provider):
        narrative = "The pin came out at speed passing nearby to the rigman."
        result = await provider.extract_safety_facts(narrative)
        # If energy evidence is set, it should be found in the narrative
        if result.energy_source.evidence:
            assert result.energy_source.evidence.lower() in narrative.lower()

    @pytest.mark.asyncio
    async def test_no_sif_fields_in_result(self, provider):
        """Mock provider MUST NOT return SIF/FPI classification."""
        result = await provider.extract_safety_facts("pin came out at speed nearby rigman")
        assert not hasattr(result, "sif_fpi_potential")
        assert not hasattr(result, "priority_score")

    @pytest.mark.asyncio
    async def test_failed_barrier_condition_for_ejection(self, provider):
        narrative = "The pin came out and passed nearby the rigman."
        result = await provider.extract_safety_facts(narrative)
        # "came out" should trigger FAILED barrier condition
        assert result.barrier_condition.value in (
            BarrierCondition.FAILED, BarrierCondition.UNKNOWN
        )


# ══════════════════════════════════════════════════════════════════════════════
# 4. AI FACTORY TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestAIFactory:
    def test_mock_provider_returned_when_no_api_key(self, monkeypatch):
        """With AI_PROVIDER=openai but no key, factory must fall back to mock."""
        monkeypatch.setattr("app.config.settings.AI_PROVIDER", "openai")
        monkeypatch.setattr("app.config.settings.AI_API_KEY", None)

        from ai.factory import get_safety_extraction_provider
        from ai.providers.mock import MockSafetyExtractionProvider
        provider = get_safety_extraction_provider()
        assert isinstance(provider, MockSafetyExtractionProvider)

    def test_mock_provider_returned_explicitly(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.AI_PROVIDER", "mock")
        monkeypatch.setattr("app.config.settings.AI_API_KEY", None)

        from ai.factory import get_safety_extraction_provider
        from ai.providers.mock import MockSafetyExtractionProvider
        provider = get_safety_extraction_provider()
        assert isinstance(provider, MockSafetyExtractionProvider)

    def test_unknown_provider_falls_back_to_mock(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.AI_PROVIDER", "some_future_provider")
        monkeypatch.setattr("app.config.settings.AI_API_KEY", None)

        from ai.factory import get_safety_extraction_provider
        from ai.providers.mock import MockSafetyExtractionProvider
        provider = get_safety_extraction_provider()
        assert isinstance(provider, MockSafetyExtractionProvider)

    def test_factory_always_returns_provider(self, monkeypatch):
        """Factory must NEVER return None regardless of configuration."""
        monkeypatch.setattr("app.config.settings.AI_PROVIDER", "invalid_provider_xyz")
        monkeypatch.setattr("app.config.settings.AI_API_KEY", None)

        from ai.factory import get_safety_extraction_provider
        provider = get_safety_extraction_provider()
        assert provider is not None


# ══════════════════════════════════════════════════════════════════════════════
# 5. EXTRACTION SERVICE INTEGRATION TESTS (using in-memory SQLite via conftest)
# ══════════════════════════════════════════════════════════════════════════════


class TestExtractionService:
    """Integration tests using the in-memory test DB from conftest."""

    @pytest.fixture
    async def seeded_report(self, async_client):
        """Seed demo data and return first report_id available."""
        resp = await async_client.post("/api/v1/reports/seed")
        assert resp.status_code == 200
        # Get first report
        list_resp = await async_client.get("/api/v1/reports?size=1")
        assert list_resp.status_code == 200
        items = list_resp.json()["items"]
        assert len(items) >= 1
        return items[0]["report_id"]

    @pytest.mark.asyncio
    async def test_analyze_report_returns_200(self, async_client, seeded_report):
        resp = await async_client.post(
            f"/api/v1/reports/{seeded_report}/analyze",
            json={"force_reanalyze": False},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_analyze_report_has_analysis_status_completed(self, async_client, seeded_report):
        resp = await async_client.post(
            f"/api/v1/reports/{seeded_report}/analyze",
            json={"force_reanalyze": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["analysis_status"] == "COMPLETED"

    @pytest.mark.asyncio
    async def test_analyze_returns_all_nine_fact_fields(self, async_client, seeded_report):
        resp = await async_client.post(
            f"/api/v1/reports/{seeded_report}/analyze",
            json={"force_reanalyze": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        for field in ("activity", "equipment", "hazard", "energy_source", "exposure",
                      "exposure_location", "barrier", "barrier_condition", "potential_consequence"):
            assert field in data, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_analyze_returns_provider_metadata(self, async_client, seeded_report):
        resp = await async_client.post(
            f"/api/v1/reports/{seeded_report}/analyze",
            json={"force_reanalyze": True},
        )
        data = resp.json()
        assert "analysis_version" in data
        assert "provider_name" in data
        assert "model_name" in data

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_report_returns_404(self, async_client):
        resp = await async_client.post(
            "/api/v1/reports/NONEXISTENT-999/analyze",
            json={"force_reanalyze": False},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_analysis_endpoint(self, async_client, seeded_report):
        # First run analysis
        await async_client.post(
            f"/api/v1/reports/{seeded_report}/analyze",
            json={"force_reanalyze": True},
        )
        # Then fetch it
        resp = await async_client.get(f"/api/v1/reports/{seeded_report}/analysis")
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_id"] == seeded_report

    @pytest.mark.asyncio
    async def test_get_analysis_before_analysis_returns_404(self, async_client):
        """A report that was never analyzed should return 404 from GET /analysis."""
        # Use a fresh unique ID that's not been seeded or analyzed
        resp = await async_client.get("/api/v1/reports/FRESH-UNANALYZED-XYZ/analysis")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_source_report_fields_unchanged_after_analysis(self, async_client, seeded_report):
        # Get original report data
        original = await async_client.get(f"/api/v1/reports/{seeded_report}")
        original_data = original.json()
        original_narrative = original_data["narrative"]
        original_incident_cause = original_data.get("incident_cause")

        # Run analysis
        await async_client.post(
            f"/api/v1/reports/{seeded_report}/analyze",
            json={"force_reanalyze": True},
        )

        # Fetch report again
        after = await async_client.get(f"/api/v1/reports/{seeded_report}")
        after_data = after.json()

        assert after_data["narrative"] == original_narrative, (
            "Narrative must be immutable — AI analysis must NOT modify source narrative"
        )
        assert after_data.get("incident_cause") == original_incident_cause, (
            "incident_cause must be immutable"
        )

    @pytest.mark.asyncio
    async def test_report_analysis_status_updates_after_analysis(self, async_client, seeded_report):
        resp = await async_client.post(
            f"/api/v1/reports/{seeded_report}/analyze",
            json={"force_reanalyze": True},
        )
        assert resp.status_code == 200
        # Fetch the report to verify analysis_status
        report_resp = await async_client.get(f"/api/v1/reports/{seeded_report}")
        data = report_resp.json()
        assert data.get("analysis_status") == "COMPLETED"

    @pytest.mark.asyncio
    async def test_batch_analyze_endpoint(self, async_client, seeded_report):
        resp = await async_client.post(
            "/api/v1/reports/analyze",
            json={
                "report_ids": [seeded_report],
                "force_reanalyze": True,
                "batch_size": 1,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "requested" in data
        assert "succeeded" in data
        assert data["requested"] == 1

    @pytest.mark.asyncio
    async def test_mock_flag_in_response(self, async_client, seeded_report):
        """When using mock provider, is_mock should be True."""
        resp = await async_client.post(
            f"/api/v1/reports/{seeded_report}/analyze",
            json={"force_reanalyze": True},
        )
        data = resp.json()
        # Default provider is mock, so is_mock should be True
        assert data["is_mock"] is True

    @pytest.mark.asyncio
    async def test_no_sif_score_in_response(self, async_client, seeded_report):
        """Phase 3 response must NOT contain SIF classification."""
        resp = await async_client.post(
            f"/api/v1/reports/{seeded_report}/analyze",
            json={"force_reanalyze": True},
        )
        data = resp.json()
        assert "sif_fpi_potential" not in data or data.get("sif_fpi_potential") is None, (
            "Phase 3 must NOT return SIF/FPI classification"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 6. OPENAI PROVIDER OUTPUT VALIDATION TESTS (no real API calls)
# ══════════════════════════════════════════════════════════════════════════════


class TestOpenAIProviderValidation:
    """Tests the _parse_and_validate logic in isolation, without real API calls."""

    @pytest.fixture
    def provider(self):
        from ai.providers.openai_provider import OpenAISafetyExtractionProvider
        return OpenAISafetyExtractionProvider(api_key="sk-test-key", model="gpt-4o")

    def test_valid_raw_dict_parsed_correctly(self, provider):
        raw = {
            "activity": {"value": "Pin removal", "evidence": "removing pin", "evidence_status": "EXPLICIT", "confidence": 0.9, "start_offset": None, "end_offset": None},
            "equipment": {"value": "Structural pin", "evidence": None, "evidence_status": "INFERRED", "confidence": 0.75, "start_offset": None, "end_offset": None},
            "hazard": {"value": "Pin ejection", "evidence": "came out at speed", "evidence_status": "EXPLICIT", "confidence": 0.92, "start_offset": 50, "end_offset": 67},
            "energy_source": {"value": "KINETIC", "evidence": "at speed", "evidence_status": "EXPLICIT", "confidence": 0.85, "start_offset": None, "end_offset": None},
            "exposure": {"value": "Rigman", "evidence": "nearby to the rigman", "evidence_status": "EXPLICIT", "confidence": 0.88, "start_offset": None, "end_offset": None},
            "exposure_location": {"value": "Near ejection path", "evidence": None, "evidence_status": "INFERRED", "confidence": 0.70, "start_offset": None, "end_offset": None},
            "barrier": {"value": "Safe positioning", "evidence": None, "evidence_status": "INFERRED", "confidence": 0.55, "start_offset": None, "end_offset": None},
            "barrier_condition": {"value": "FAILED", "evidence": None, "evidence_status": "INFERRED", "confidence": 0.78, "start_offset": None, "end_offset": None},
            "potential_consequence": {"value": "Struck-by serious injury", "evidence": None, "evidence_status": "INFERRED", "confidence": 0.82, "start_offset": None, "end_offset": None},
            "is_mock": False,
            "extraction_notes": None,
        }
        result = provider._parse_and_validate(raw, "TEST-001")
        assert result.activity.value == "Pin removal"
        assert result.energy_source.value == EnergySource.KINETIC
        assert result.barrier_condition.value == BarrierCondition.FAILED
        assert result.is_mock is False

    def test_missing_field_defaults_to_unknown(self, provider):
        raw = {
            "activity": {"value": "Drilling", "evidence": None, "evidence_status": "EXPLICIT", "confidence": 0.8, "start_offset": None, "end_offset": None},
            # All other fields missing
        }
        result = provider._parse_and_validate(raw, "TEST-002")
        assert result.activity.value == "Drilling"
        assert result.equipment.value is None
        assert result.equipment.evidence_status == EvidenceStatus.UNKNOWN
        assert result.hazard.value is None

    def test_invalid_enum_value_defaults_to_none(self, provider):
        raw = {
            "energy_source": {"value": "NUCLEAR_FUSION", "evidence": None, "evidence_status": "EXPLICIT", "confidence": 0.5, "start_offset": None, "end_offset": None},
            "barrier_condition": {"value": "TOTALLY_FINE", "evidence": None, "evidence_status": "UNKNOWN", "confidence": 0.0, "start_offset": None, "end_offset": None},
        }
        result = provider._parse_and_validate(raw, "TEST-003")
        assert result.energy_source.value is None
        assert result.barrier_condition.value is None

    def test_invalid_evidence_status_defaults_to_unknown(self, provider):
        raw = {
            "activity": {"value": "Test", "evidence": None, "evidence_status": "DEFINITELY_TRUE", "confidence": 0.5, "start_offset": None, "end_offset": None},
        }
        result = provider._parse_and_validate(raw, "TEST-004")
        assert result.activity.evidence_status == EvidenceStatus.UNKNOWN

    def test_confidence_out_of_range_clamped(self, provider):
        raw = {
            "activity": {"value": "Test", "evidence": None, "evidence_status": "EXPLICIT", "confidence": 99.9, "start_offset": None, "end_offset": None},
        }
        result = provider._parse_and_validate(raw, "TEST-005")
        assert result.activity.confidence == 1.0

    def test_non_integer_offsets_become_none(self, provider):
        raw = {
            "hazard": {"value": "Test", "evidence": "some text", "evidence_status": "EXPLICIT", "confidence": 0.8, "start_offset": "six", "end_offset": "ten"},
        }
        result = provider._parse_and_validate(raw, "TEST-006")
        assert result.hazard.start_offset is None
        assert result.hazard.end_offset is None

    def test_entire_raw_is_non_dict_for_field(self, provider):
        raw = {
            "activity": "just a string not a dict",
        }
        result = provider._parse_and_validate(raw, "TEST-007")
        assert result.activity.value is None
        assert result.activity.evidence_status == EvidenceStatus.UNKNOWN
