import os
import sys

# Ensure project root is in sys.path so top-level modules like `ai` can be resolved
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.utils.logging import logger
from app.utils.errors import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)
from app.routes import (
    health_router,
    meta_router,
    reports_router,
    clusters_router,
    dashboard_router,
    reviews_router,
    evaluations_router,
)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} backend service (Env: {settings.APP_ENV})")
    yield
    logger.info(f"Shutting down {settings.APP_NAME} backend service")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI/NLP Engine to Detect Serious Injury & Fatality (SIF) Precursors in Safety Reports",
    version="0.1.0-phase9",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Exception Handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Include API Routers under /api/v1
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(meta_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)
app.include_router(clusters_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(reviews_router, prefix=settings.API_V1_PREFIX)
app.include_router(evaluations_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
