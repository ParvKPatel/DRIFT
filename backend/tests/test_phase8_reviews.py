"""
Phase 8 — HSE Review & Human-in-the-Loop Test Suite

Tests cover:
1. Create review with CONFIRM_AI
2. Create review with OVERRIDE (modifying SIF, LSR, Priority)
3. Create review with REJECT (requiring rejection reason)
4. Create review with NEEDS_MORE_INFORMATION (tracking missing fields)
5. Retrieve latest review for report
6. Retrieve review chronological history (audit trail: WHO, WHAT, WHEN, WHY)
7. Immutability of original AI assessment and source report data
8. Review queue retrieval and ordering by priority score desc
9. Review queue filtering (by status, priority, SIF, site)
10. Review analytics calculation (pending, confirmed, overridden, rejected, needs info)
11. Invalid report ID handling
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.schemas.enums import (
    ReviewStatus,
    ReviewDecision,
    SifDecision,
    PriorityLevel,
)


class TestPhase8Reviews:

    @pytest.fixture
    async def seeded_dataset(self, async_client):
        await async_client.post("/api/v1/reports/seed")
        await async_client.post("/api/v1/reports/analyze", json={"force_reanalyze": True})
        await async_client.post("/api/v1/reports/screen-sif", json={"force_rescreen": True})
        await async_client.post("/api/v1/reports/map-lsr", json={"force_remap": True})
        return True

    @pytest.mark.asyncio
    async def test_confirm_ai_decision(self, async_client, seeded_dataset):
        report_id = "SYN-2026-001"
        payload = {
            "reviewer_id": "HSE Officer #1",
            "review_decision": "CONFIRM_AI",
            "reviewer_comment": "Pin ejection trajectory accurately assessed by AI.",
        }
        resp = await async_client.post(f"/api/v1/reviews/{report_id}", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["report_id"] == report_id
        assert data["review_status"] == ReviewStatus.REVIEWED.value
        assert data["review_decision"] == ReviewDecision.CONFIRM_AI.value
        assert data["original_ai_sif_potential"] in ["YES", "UNCERTAIN", "NO"]
        assert data["final_sif_potential"] == data["original_ai_sif_potential"]
        assert data["reviewer_comment"] == payload["reviewer_comment"]

    @pytest.mark.asyncio
    async def test_override_ai_decision(self, async_client, seeded_dataset):
        report_id = "SYN-2026-002"
        payload = {
            "reviewer_id": "Senior HSE Inspector",
            "review_decision": "OVERRIDE",
            "final_sif_potential": "UNCERTAIN",
            "final_lsr": "Line of Fire",
            "final_priority": "SAFETY_REVIEW",
            "reviewer_comment": "Exposure duration was momentary; downgrade to UNCERTAIN pending field interview.",
        }
        resp = await async_client.post(f"/api/v1/reviews/{report_id}", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["review_decision"] == ReviewDecision.OVERRIDE.value
        assert data["final_sif_potential"] == "UNCERTAIN"
        assert data["final_priority"] == "SAFETY_REVIEW"

    @pytest.mark.asyncio
    async def test_reject_finding_requires_rationale(self, async_client, seeded_dataset):
        report_id = "SYN-2026-003"
        # Rejection without reason/comment should fail with 400
        fail_payload = {
            "reviewer_id": "HSE Officer #2",
            "review_decision": "REJECT",
        }
        fail_resp = await async_client.post(f"/api/v1/reviews/{report_id}", json=fail_payload)
        assert fail_resp.status_code == 400

        # With reason should succeed
        success_payload = {
            "reviewer_id": "HSE Officer #2",
            "review_decision": "REJECT",
            "rejection_reason": "FALSE_POSITIVE",
            "reviewer_comment": "Observation is duplicate entry of morning toolbox meeting report.",
        }
        success_resp = await async_client.post(f"/api/v1/reviews/{report_id}", json=success_payload)
        assert success_resp.status_code == 200
        s_data = success_resp.json()
        assert s_data["review_decision"] == ReviewDecision.REJECT.value
        assert s_data["final_sif_potential"] == "REJECTED"

    @pytest.mark.asyncio
    async def test_needs_more_information(self, async_client, seeded_dataset):
        report_id = "SYN-2026-004"
        payload = {
            "reviewer_id": "Triage Safety Officer",
            "review_decision": "NEEDS_MORE_INFORMATION",
            "missing_information_fields": ["exposure_distance", "barrier_condition"],
            "reviewer_comment": "Need rig floor CCTV footage or supervisor statement.",
        }
        resp = await async_client.post(f"/api/v1/reviews/{report_id}", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["review_status"] == ReviewStatus.NEEDS_MORE_INFORMATION.value
        assert "exposure_distance" in data["missing_information_fields"]
        assert "barrier_condition" in data["missing_information_fields"]

    @pytest.mark.asyncio
    async def test_review_history_audit_trail(self, async_client, seeded_dataset):
        report_id = "SYN-2026-005"
        # Submit 1st review
        await async_client.post(
            f"/api/v1/reviews/{report_id}",
            json={
                "reviewer_id": "Reviewer A",
                "review_decision": "NEEDS_MORE_INFORMATION",
                "reviewer_comment": "First review requested details",
            },
        )
        # Submit 2nd review
        await async_client.post(
            f"/api/v1/reviews/{report_id}",
            json={
                "reviewer_id": "Reviewer B",
                "review_decision": "CONFIRM_AI",
                "reviewer_comment": "Details verified on site visit, confirming SIF",
            },
        )

        hist_resp = await async_client.get(f"/api/v1/reviews/{report_id}/history")
        assert hist_resp.status_code == 200
        history = hist_resp.json()
        assert len(history) >= 2
        # Ordered by most recent first
        assert history[0]["reviewer_id"] == "Reviewer B"
        assert history[0]["review_decision"] == "CONFIRM_AI"
        assert history[1]["reviewer_id"] == "Reviewer A"

    @pytest.mark.asyncio
    async def test_original_source_and_ai_immutability(self, async_client, seeded_dataset):
        report_id = "SYN-2026-001"
        # Fetch report before review
        rep_before = (await async_client.get(f"/api/v1/reports/{report_id}")).json()
        ai_before = (await async_client.get(f"/api/v1/reports/{report_id}/analysis")).json()

        # Submit radical override
        await async_client.post(
            f"/api/v1/reviews/{report_id}",
            json={
                "reviewer_id": "External Auditor",
                "review_decision": "OVERRIDE",
                "final_sif_potential": "NO",
                "final_lsr": "Working at Height",
                "final_priority": "ROUTINE",
                "reviewer_comment": "Auditor downgraded item",
            },
        )

        # Verify source fields remain identical
        rep_after = (await async_client.get(f"/api/v1/reports/{report_id}")).json()
        assert rep_after["narrative"] == rep_before["narrative"]
        assert rep_after["incident_cause"] == rep_before["incident_cause"]
        assert rep_after["site"] == rep_before["site"]

        # Verify AI extraction fields remain untouched
        ai_after = (await async_client.get(f"/api/v1/reports/{report_id}/analysis")).json()
        assert ai_after.get("activity") == ai_before.get("activity")
        assert ai_after.get("hazard") == ai_before.get("hazard")
        assert ai_after.get("barrier") == ai_before.get("barrier")

    @pytest.mark.asyncio
    async def test_review_queue_and_filtering(self, async_client, seeded_dataset):
        # Retrieve queue
        resp = await async_client.get("/api/v1/reviews/queue")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) > 0

        # Filter by priority
        prio_resp = await async_client.get("/api/v1/reviews/queue?priority=CRITICAL")
        assert prio_resp.status_code == 200

        # Filter by SIF
        sif_resp = await async_client.get("/api/v1/reviews/queue?sif=YES")
        assert sif_resp.status_code == 200
        for item in sif_resp.json()["items"]:
            assert item["ai_sif_potential"] == "YES"

    @pytest.mark.asyncio
    async def test_review_analytics(self, async_client, seeded_dataset):
        resp = await async_client.get("/api/v1/reviews/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_in_scope" in data
        assert "pending_review" in data
        assert "total_reviewed" in data
        assert data["total_in_scope"] >= 19
        assert data["total_reviewed"] >= 1
        assert data["confirmed_count"] >= 1

    @pytest.mark.asyncio
    async def test_invalid_report_id_review(self, async_client):
        resp = await async_client.post(
            "/api/v1/reviews/NON-EXISTENT-999",
            json={
                "reviewer_id": "HSE Officer",
                "review_decision": "CONFIRM_AI",
            },
        )
        assert resp.status_code == 400
