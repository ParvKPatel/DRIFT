import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reports import Report

@pytest.mark.asyncio
async def test_analyze_missing_report(async_client: AsyncClient):
    """Verify that requesting analysis for a non-existent report returns 404."""
    response = await async_client.post("/api/v1/reports/INVALID-ID/analyze", json={"force_reanalyze": True})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_analysis_missing_report(async_client: AsyncClient):
    """Verify that getting analysis for a non-existent report returns 404."""
    response = await async_client.get("/api/v1/reports/INVALID-ID/analysis")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_extract_and_suggest_actions(async_client: AsyncClient):
    """Verify that the extraction pipeline generates and returns suggested actions."""
    # Seed data
    await async_client.post("/api/v1/reports/seed")
    
    # Get a report
    res = await async_client.get("/api/v1/reports?size=1")
    report_id = res.json()["items"][0]["report_id"]

    # Trigger analysis
    response = await async_client.post(
        f"/api/v1/reports/{report_id}/analyze", 
        json={"force_reanalyze": True}
    )
    
    assert response.status_code == 200, f"Analysis failed: {response.text}"
    data = response.json()
    
    # Verify the structure has suggested_actions
    assert "suggested_actions" in data
    assert "suggested_actions_reasoning" in data
    assert data["analysis_status"] == "COMPLETED"
    
    # Retrieve it via GET
    get_response = await async_client.get(f"/api/v1/reports/{report_id}/analysis")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert "suggested_actions" in get_data
    assert get_data["suggested_actions"] == data["suggested_actions"]
