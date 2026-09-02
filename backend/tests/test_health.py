import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


@pytest.mark.asyncio
async def test_meta_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/meta")
    assert response.status_code == 200
    data = response.json()
    assert "application_name" in data
    assert data["application_name"] == "OIL SENTINEL"
    assert "version" in data
    assert "environment" in data
