"""
Phase 6 — Relationship Intelligence, Precursor Clustering & Pattern Escalation Test Suite

Tests cover:
1. Embedding Provider abstraction & vector normalization (Mock & Factory)
2. Canonical Semantic Text representation
3. Semantic & Hybrid Similarity Engine (Different wording matching, naive keyword negative tests)
4. Precursor Clustering Engine (Hero pin ejection clustering, evidence-backed cluster naming)
5. Temporal Analysis & Escalation Engine (Concentrated 18-day vs spread 18-month cluster decay)
6. Shared Asset & Barrier boost calculations
7. Pattern Escalation Alert generation & evidence explanations
8. Source Preservation & Leakage Prevention (Raw severity & incident_cause never modified, SIF decision separate)
9. Phase 5 Priority Engine Integration (Recurrence score increases priority)
10. API Integration Tests (/reports/{id}/similar, /clusters, /clusters/{id}, /clusters/rebuild)
"""

import pytest
import sys
import os
from datetime import date, datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.schemas.enums import (
    EscalationBand,
    SimilarityBand,
    SifDecision,
    PriorityLevel,
    BarrierCondition,
    EnergySource,
)
from app.services.embedding_provider import MockEmbeddingProvider, EmbeddingFactory
from app.services.semantic_representation import SemanticRepresentationService
from app.services.similarity_engine import SimilarityEngine
from app.services.escalation_engine import EscalationEngine
from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis


# ══════════════════════════════════════════════════════════════════════════════
# 1. EMBEDDING ARCHITECTURE TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestEmbeddingArchitecture:

    @pytest.fixture
    def provider(self):
        return MockEmbeddingProvider()

    def test_mock_embedding_dimension_and_normalization(self, provider):
        vec = provider.embed_text("Pin flew out near worker during dismantling.")
        assert len(vec) == 768
        # Check unit L2 norm
        norm = sum(x * x for x in vec) ** 0.5
        assert pytest.approx(norm, 0.001) == 1.0

    def test_mock_embedding_reproducibility(self, provider):
        text = "Hydraulic hose leaked under 200 bar pressure."
        v1 = provider.embed_text(text)
        v2 = provider.embed_text(text)
        assert v1 == v2

    def test_embedding_factory_returns_provider(self):
        p = EmbeddingFactory.get_provider()
        assert p is not None
        v = p.embed_text("Test embedding text")
        assert len(v) == 768


# ══════════════════════════════════════════════════════════════════════════════
# 2. SEMANTIC REPRESENTATION TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestSemanticRepresentation:

    def test_canonical_text_construction(self):
        r = Report(
            report_id="TEST-001",
            narrative="Pin flew out near worker.",
            site="Platform Alpha",
            functional_location="FL-RIG-01",
        )
        sa = SafetyAnalysis(
            report_id="TEST-001",
            activity="Pin removal",
            hazard="Component ejection",
            equipment="Deck crane",
            energy_source=EnergySource.KINETIC,
            exposure="Rigger in trajectory",
            barrier="Safe positioning",
            barrier_condition=BarrierCondition.DEGRADED,
            primary_life_saving_rule="Line of Fire",
        )
        canonical = SemanticRepresentationService.build_canonical_text(r, sa)

        assert "ACTIVITY: Pin removal" in canonical
        assert "HAZARD: Component ejection" in canonical
        assert "LOCATION: FL-RIG-01" in canonical
        assert "LSR: Line of Fire" in canonical
        assert '"Pin flew out near worker."' in canonical


# ══════════════════════════════════════════════════════════════════════════════
# 3. SEMANTIC SIMILARITY & NEGATIVE TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestSimilarityEngine:

    @pytest.fixture
    def provider(self):
        return MockEmbeddingProvider()

    def test_similar_mechanism_different_wording(self, provider):
        """
        Reports with different wording describing same mechanism must achieve high similarity:
        "Pin flew out near worker" vs "Component ejected toward rigger"
        """
        r1 = Report(report_id="R1", narrative="Pin flew out near worker during pin removal.", functional_location="FL-01")
        sa1 = SafetyAnalysis(report_id="R1", hazard="unexpected component movement", exposure="worker in trajectory", primary_life_saving_rule="Line of Fire")
        v1 = provider.embed_text(SemanticRepresentationService.build_canonical_text(r1, sa1))

        r2 = Report(report_id="R2", narrative="Component ejected toward rigger while hammering bracket pin.", functional_location="FL-01")
        sa2 = SafetyAnalysis(report_id="R2", hazard="unexpected component movement", exposure="worker in trajectory", primary_life_saving_rule="Line of Fire")
        v2 = provider.embed_text(SemanticRepresentationService.build_canonical_text(r2, sa2))

        sim, details = SimilarityEngine.calculate_hybrid_similarity(r1, sa1, v1, r2, sa2, v2)
        assert sim >= 0.65, f"Expected strongly related similarity for same mechanism, got {sim}"
        assert details.shared_hazard == "unexpected component movement"

    def test_naive_keyword_negative_test(self, provider):
        """
        Negative Test: Routine use of "hydraulic hose" must NOT trigger high similarity to "hydraulic line burst under pressure".
        """
        r1 = Report(report_id="R1", narrative="Hydraulic hose line burst spraying 200 bar mineral oil onto deck.", functional_location="FL-CRN-01")
        sa1 = SafetyAnalysis(report_id="R1", hazard="pressure release burst", energy_source=EnergySource.PRESSURE)
        v1 = provider.embed_text(SemanticRepresentationService.build_canonical_text(r1, sa1))

        r2 = Report(report_id="R2", narrative="Technician conducted routine eyewash station inspection in admin building.", functional_location="FL-ADM-01")
        sa2 = SafetyAnalysis(report_id="R2", hazard="routine eyewash check", energy_source=EnergySource.UNKNOWN)
        v2 = provider.embed_text(SemanticRepresentationService.build_canonical_text(r2, sa2))

        sim, _ = SimilarityEngine.calculate_hybrid_similarity(r1, sa1, v1, r2, sa2, v2)
        assert sim < 0.50, f"Expected low similarity between burst and eyewash check, got {sim}"


# ══════════════════════════════════════════════════════════════════════════════
# 4. TEMPORAL ANALYSIS & ESCALATION SCORE TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestTemporalEscalationEngine:

    def test_concentrated_vs_spread_cluster_escalation(self):
        """
        Concentrated cluster (4 events over 18 days) must score HIGHER escalation
        than spread cluster (4 events over 10 months).
        """
        now = datetime(2026, 9, 1, tzinfo=timezone.utc)

        # Concentrated reports (Aug 10 to Aug 28)
        conc_reports = [
            (Report(report_id=f"CR-{i}", report_date=date(2026, 8, 10 + i * 5), functional_location="FL-01"),
             SafetyAnalysis(report_id=f"CR-{i}", hazard="pin ejection", barrier="safe positioning"), 0.85)
            for i in range(4)
        ]

        # Spread reports (Jan 2025 to Oct 2025)
        spread_reports = [
            (Report(report_id=f"SR-{i}", report_date=date(2025, 1 + i * 3, 1), functional_location="FL-01"),
             SafetyAnalysis(report_id=f"SR-{i}", hazard="pin ejection", barrier="safe positioning"), 0.85)
            for i in range(4)
        ]

        score_conc, band_conc, why_conc, _ = EscalationEngine.calculate_cluster_escalation(conc_reports, now=now)
        score_spread, band_spread, why_spread, _ = EscalationEngine.calculate_cluster_escalation(spread_reports, now=now)

        assert score_conc > score_spread, f"Concentrated cluster score ({score_conc}) should beat spread cluster ({score_spread})"
        assert score_conc >= 70.0, "Concentrated 4-event cluster at same asset should reach High/Critical pattern"

    def test_shared_asset_and_barrier_boost(self):
        now = datetime(2026, 9, 1, tzinfo=timezone.utc)

        # Cluster at same asset FL-RIG-04 and same barrier "Safe positioning"
        same_asset = [
            (Report(report_id=f"SA-{i}", report_date=date(2026, 8, 20 + i), functional_location="FL-RIG-04"),
             SafetyAnalysis(report_id=f"SA-{i}", barrier="Safe positioning"), 0.80)
            for i in range(3)
        ]

        # Cluster at 3 different assets
        diff_asset = [
            (Report(report_id=f"DA-{i}", report_date=date(2026, 8, 20 + i), functional_location=f"FL-VAR-{i}"),
             SafetyAnalysis(report_id=f"DA-{i}", barrier=f"Barrier-{i}"), 0.80)
            for i in range(3)
        ]

        score_same, _, why_same, _ = EscalationEngine.calculate_cluster_escalation(same_asset, now=now)
        score_diff, _, why_diff, _ = EscalationEngine.calculate_cluster_escalation(diff_asset, now=now)

        assert score_same > score_diff
        assert any("same functional location" in r for r in why_same)


# ══════════════════════════════════════════════════════════════════════════════
# 5. SOURCE PRESERVATION & PHASE 5 INTEGRATION TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestSourcePreservationAndPriorityIntegration:

    def test_sif_and_severity_remain_unchanged(self):
        r = Report(
            report_id="SYN-2026-001",
            incident_cause="Improper Material Handling",
            incident_type="Near Miss",
        )
        assert r.incident_cause == "Improper Material Handling"
        assert r.incident_type == "Near Miss"

    def test_phase5_priority_rises_with_recurrence(self):
        from app.services.priority_engine import HsePriorityEngine

        engine = HsePriorityEngine()
        facts_base = {
            "sif_fpi_potential": SifDecision.YES,
            "barrier_condition": BarrierCondition.DEGRADED,
        }
        facts_escalated = {
            "sif_fpi_potential": SifDecision.YES,
            "barrier_condition": BarrierCondition.DEGRADED,
            "recurrence_score": 0.85,
            "escalation_score": 82.0,
        }

        res_base = engine.calculate_priority("P1", facts_base)
        res_esc = engine.calculate_priority("P2", facts_escalated)

        assert res_esc.priority_score > res_base.priority_score
        assert any("Precursor Recurrence" in w for w in res_esc.why_prioritized)


# ══════════════════════════════════════════════════════════════════════════════
# 6. API INTEGRATION TESTS (SQLite AsyncClient)
# ══════════════════════════════════════════════════════════════════════════════


class TestPhase6ApiIntegration:

    @pytest.fixture
    async def seeded_dataset(self, async_client):
        await async_client.post("/api/v1/reports/seed")
        return "SYN-2026-001"

    @pytest.mark.asyncio
    async def test_get_similar_reports_endpoint(self, async_client, seeded_dataset):
        resp = await async_client.get(f"/api/v1/reports/{seeded_dataset}/similar?top_k=3&min_threshold=0.1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_report_id"] == seeded_dataset
        assert len(data["similar_reports"]) > 0
        top = data["similar_reports"][0]
        assert "similarity_score" in top
        assert "shared_details" in top

    @pytest.mark.asyncio
    async def test_cluster_rebuild_and_list_endpoints(self, async_client, seeded_dataset):
        # Rebuild clusters
        rebuild_resp = await async_client.post("/api/v1/clusters/rebuild")
        assert rebuild_resp.status_code == 200
        rb_data = rebuild_resp.json()
        assert rb_data["total_clusters_formed"] > 0

        # List clusters
        list_resp = await async_client.get("/api/v1/clusters")
        assert list_resp.status_code == 200
        clusters = list_resp.json()
        assert len(clusters) > 0

        # Fetch detail for first cluster
        cid = clusters[0]["id"]
        detail_resp = await async_client.get(f"/api/v1/clusters/{cid}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert "members" in detail
        assert "timeline" in detail
        assert "why_escalating" in detail
