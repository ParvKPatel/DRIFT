import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
import json

async def main():
    print("Testing Duplicates...")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a small CSV string
        csv_data = "report_id,narrative\nTEST-001,Narrative 1\nTEST-002,Narrative 2\n"
        
        # 1. Initial Upload
        res1 = await client.post("/api/v1/reports/upload", files={"file": ("test.csv", csv_data.encode("utf-8"), "text/csv")})
        print(f"Upload 1 -> Status: {res1.status_code}, Response: {res1.json()}")
        
        # 2. Re-upload
        res2 = await client.post("/api/v1/reports/upload", files={"file": ("test.csv", csv_data.encode("utf-8"), "text/csv")})
        print(f"Upload 2 -> Status: {res2.status_code}, Response: {res2.json()}")

        # 3. Mixed Upload
        csv_data_mixed = "report_id,narrative\nTEST-001,Narrative 1\nTEST-003,Narrative 3\nTEST-004,Narrative 4\n"
        res3 = await client.post("/api/v1/reports/upload", files={"file": ("test_mixed.csv", csv_data_mixed.encode("utf-8"), "text/csv")})
        print(f"Upload 3 -> Status: {res3.status_code}, Response: {res3.json()}")


if __name__ == "__main__":
    asyncio.run(main())
