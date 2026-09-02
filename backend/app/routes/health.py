from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.utils.logging import logger

router = APIRouter(prefix="/health", tags=["Health Checks"])


@router.get("", summary="Liveness Health Check")
async def health_check():
    """Returns basic liveness status of the API server."""
    return {"status": "ok"}


@router.get("/database", summary="Database Connectivity Check")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Verifies live PostgreSQL database connectivity."""
    try:
        result = await db.execute(text("SELECT 1"))
        val = result.scalar()
        if val == 1:
            return {"status": "ok", "database": "connected"}
        else:
            raise Exception("Unexpected scalar result from database query")
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connectivity check failed: {str(e)}"
        )
