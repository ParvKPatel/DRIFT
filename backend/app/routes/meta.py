from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/meta", tags=["Metadata"])


@router.get("", summary="Application Metadata")
async def get_metadata():
    """Returns application name, version, environment, and API settings."""
    return {
        "application_name": settings.APP_NAME,
        "version": "0.1.0-phase1",
        "environment": settings.APP_ENV,
        "api_prefix": settings.API_V1_PREFIX,
        "ai_provider": settings.AI_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
    }
