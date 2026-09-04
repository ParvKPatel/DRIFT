import asyncio
from httpx import AsyncClient
from app.main import app
from httpx import ASGITransport

async def main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/reports?size=100")
        reports = res.json().get("items", [])
        for r in reports:
            print(f"Reanalyzing {r['report_id']}...")
            await client.post(f"/api/v1/reports/{r['report_id']}/analyze", json={"force_reanalyze": True})

if __name__ == "__main__":
    asyncio.run(main())
