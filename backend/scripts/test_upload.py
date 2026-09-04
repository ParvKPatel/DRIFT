import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
import json

async def main():
    print("Testing Upload Pipeline...")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Initial Upload
        with open("/Users/parvpatel/SIH MVP/oil_sample_dataset.csv", "rb") as f:
            res1 = await client.post("/api/v1/reports/upload", files={"file": ("oil_sample_dataset.csv", f, "text/csv")})
        
        data1 = res1.json()
        print(f"Upload 1 -> Imported: {data1.get('imported_count')}, Duplicates: {data1.get('duplicate_count')}")
        
        # 2. Re-upload (Duplicate test)
        with open("/Users/parvpatel/SIH MVP/oil_sample_dataset.csv", "rb") as f:
            res2 = await client.post("/api/v1/reports/upload", files={"file": ("oil_sample_dataset.csv", f, "text/csv")})
        
        data2 = res2.json()
        print(f"Upload 2 -> Imported: {data2.get('imported_count')}, Duplicates: {data2.get('duplicate_count')}")

if __name__ == "__main__":
    asyncio.run(main())
