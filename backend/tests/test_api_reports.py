import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoints(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_reports_list_api(async_client: AsyncClient):
    response = await async_client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_reports_stats_api(async_client: AsyncClient):
    response = await async_client.get("/api/v1/reports/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_reports" in data
    assert "synthetic_count" in data
    assert "field_completeness" in data


@pytest.mark.asyncio
async def test_csv_upload_api_invalid_filetype(async_client: AsyncClient):
    files = {"file": ("test.txt", b"some text content", "text/plain")}
    response = await async_client.post("/api/v1/reports/upload", files=files)
    assert response.status_code == 400
    assert "Only CSV dataset files are supported" in response.json()["detail"]
