"""
Phase 9 — Evaluation Router

Endpoints for managing and querying evaluation benchmarking runs:
- GET  /api/v1/evaluations/latest — Fetch latest persisted evaluation run
- POST /api/v1/evaluations/run    — Trigger a reproducible benchmark run
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.schemas.evaluation_schemas import EvaluationRunResponse
from app.services.evaluation_service import EvaluationService
from app.utils.logging import logger

router = APIRouter(prefix="/evaluations", tags=["Evaluation & Benchmarking"])


@router.get(
    "/latest",
    response_model=Optional[EvaluationRunResponse],
    summary="Get Latest Model Evaluation Run",
)
async def get_latest_evaluation(db: AsyncSession = Depends(get_db)):
    """
    Returns the most recent persistent evaluation benchmark run from the database.
    Returns null if no evaluation run has been executed yet.
    """
    latest = await EvaluationService.get_latest_evaluation(db)
    return latest


@router.post(
    "/run",
    response_model=EvaluationRunResponse,
    summary="Trigger Model Evaluation Benchmark Run",
)
async def trigger_evaluation_run(db: AsyncSession = Depends(get_db)):
    """
    Triggers an evaluation benchmark run across the reference dataset:
    - Runs safety facts extraction and deterministic rules
    - Computes precision, recall, F1, F2, confusion matrix, and critical misses
    - Audits data leakage and synonym robustness
    - Persists the run in the database and returns the metrics payload
    """
    logger.info("Triggering model evaluation benchmarking run")
    try:
        result = await EvaluationService.run_evaluation(db=db)
        return result
    except Exception as exc:
        logger.error(f"Evaluation benchmark execution failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(exc)}",
        )
