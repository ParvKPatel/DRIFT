import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def main():
    print("Cleaning up old ONGC reports...")
    async with AsyncSessionLocal() as session:
        # We must delete the analysis first due to foreign keys, or they are set to cascade.
        # Let's delete from reports and see if cascade handles it, if not we delete both.
        # Usually reports CASCADE, but just in case:
        await session.execute(text("DELETE FROM safety_analysis WHERE report_id LIKE 'ONGC-%'"))
        await session.execute(text("DELETE FROM evidence WHERE report_id LIKE 'ONGC-%'"))
        await session.execute(text("DELETE FROM reports WHERE report_id LIKE 'ONGC-%'"))
        await session.commit()
        print("Cleanup completed.")

if __name__ == "__main__":
    asyncio.run(main())
