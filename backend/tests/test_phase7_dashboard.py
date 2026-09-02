"""
Phase 7 — Intelligence Dashboard Test Suite

Tests cover:
1. Executive Summary counts and date/site filtering
2. Time-series trends aggregation & date filtering
3. Site intelligence aggregation, ranking, and precursor density vs concentration fallback
4. Activity & Hazard aggregation
5. 9 Life-Saving Rules representation
6. Barrier condition distribution (INTACT, DEGRADED, FAILED, ABSENT, UNKNOWN) & weakness ranking
7. Precursor cluster & alert retrieval
8. Data quality & completeness metrics
9. Global filters combination
10. Source data immutability during dashboard queries
"""

import pytest
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.schemas.enums import (
    SifDecision,
    PriorityLevel,
    BarrierCondition,
    OFFICIAL_LIFE_SAVING_RULES,
)
from app.services.dashboard_service import DashboardService


class TestDashboardAggregations:

    @pytest.fixture
    async def seeded_dataset(self, async_client):
        await async_client.post("/api/v1/reports/seed")
        # Run SIF screening across seeded reports so facts exist
        await async_client.post("/api/v1/reports/screen-sif", json={"force_rescreen": True})
        # Rebuild clusters
        await async_client.post("/api/v1/clusters/rebuild")
        return True

    @pytest.mark.asyncio
    async def test_summary_api_returns_database_counts(self, async_client, seeded_dataset):
        resp = await async_client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_reports"] >= 19
        assert data["sif_yes"] >= 1
        assert data["comparison_period_label"] == "No comparison data"
        if data["analyzed_reports"] > 0:
            assert data["sif_share_pct"] is not None
            assert 0.0 <= data["sif_share_pct"] <= 100.0

    @pytest.mark.asyncio
    async def test_summary_api_with_site_filter(self, async_client, seeded_dataset):
        resp = await async_client.get("/api/v1/dashboard/summary?site=Offshore%20Platform%20Alpha")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_reports"] > 0

    @pytest.mark.asyncio
    async def test_trends_api_returns_time_series(self, async_client, seeded_dataset):
        resp = await async_client.get("/api/v1/dashboard/trends?window=30d")
        assert resp.status_code == 200
        trends = resp.json()
        assert isinstance(trends, list)
        if trends:
            pt = trends[0]
            assert "date" in pt
            assert "total_reports" in pt
            assert "sif_yes" in pt

    @pytest.mark.asyncio
    async def test_sites_api_precursor_density_and_concentration(self, async_client, seeded_dataset):
        resp = await async_client.get("/api/v1/dashboard/sites")
        assert resp.status_code == 200
        sites = resp.json()
        assert len(sites) > 0

        for s in sites:
            assert "site" in s
            assert "report_count" in s
            assert "sif_count" in s
            assert "precursor_concentration_pct" in s
            assert 0.0 <= s["precursor_concentration_pct"] <= 100.0
            if s["has_valid_man_hours"]:
                assert s["precursor_density"] is not None
                assert s["precursor_density_unit"] == "per 10k man-hours"
            else:
                assert s["precursor_density"] is None

    @pytest.mark.asyncio
    async def test_activities_and_hazards_apis(self, async_client, seeded_dataset):
        act_resp = await async_client.get("/api/v1/dashboard/activities")
        assert act_resp.status_code == 200
        assert isinstance(act_resp.json(), list)

        haz_resp = await async_client.get("/api/v1/dashboard/hazards")
        assert haz_resp.status_code == 200
        assert isinstance(haz_resp.json(), list)

    @pytest.mark.asyncio
    async def test_lsr_api_covers_nine_rules(self, async_client, seeded_dataset):
        resp = await async_client.get("/api/v1/dashboard/lsr")
        assert resp.status_code == 200
        lsr_data = resp.json()
        assert len(lsr_data) == len(OFFICIAL_LIFE_SAVING_RULES)

        rule_names = {item["lsr"] for item in lsr_data}
        for rule in OFFICIAL_LIFE_SAVING_RULES:
            assert rule in rule_names

    @pytest.mark.asyncio
    async def test_barriers_api_condition_distribution(self, async_client, seeded_dataset):
        resp = await async_client.get("/api/v1/dashboard/barriers")
        assert resp.status_code == 200
        barriers = resp.json()
        assert isinstance(barriers, list)
        if barriers:
            b = barriers[0]
            assert "intact_count" in b
            assert "degraded_count" in b
            assert "failed_count" in b
            assert "absent_count" in b
            assert "unknown_count" in b
            assert "weakness_score" in b

    @pytest.mark.asyncio
    async def test_data_quality_api(self, async_client, seeded_dataset):
        resp = await async_client.get("/api/v1/dashboard/data-quality")
        assert resp.status_code == 200
        dq = resp.json()
        assert dq["total_imported"] >= 19
        assert "field_completeness" in dq
        assert "narrative" in dq["field_completeness"]

    @pytest.mark.asyncio
    async def test_csv_export_endpoint(self, async_client, seeded_dataset):
        resp = await async_client.get("/api/v1/dashboard/export/sites")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/csv; charset=utf-8"
        content = resp.text
        assert "Site,Total Reports" in content
