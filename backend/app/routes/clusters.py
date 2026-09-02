"""
Phase 6 — Precursor Clustering & Escalation API Endpoints

Provides endpoints for managing, viewing, and rebuilding precursor safety clusters:
- GET /clusters
- GET /clusters/{cluster_id}
- POST /clusters/rebuild
- GET /reports/{report_id}/clusters
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.database import get_db
from app.schemas.cluster_schemas import (
    ClusterResponse,
    ClusterDetailResponse,
    ClusterRebuildResponse,
)
from app.services.clustering_service import ClusteringService
from app.utils.logging import logger

router = APIRouter(prefix="/clusters", tags=["Precursor Clusters"])


@router.get(
    "",
    response_model=List[ClusterResponse],
    summary="List Precursor Safety Clusters",
)
async def list_clusters(db: AsyncSession = Depends(get_db)):
    """Returns all precursor safety clusters sorted primarily by escalation score descending."""
    return await ClusteringService.get_clusters(db)


@router.post(
    "/rebuild",
    response_model=ClusterRebuildResponse,
    summary="Rebuild Precursor Clusters Across All Reports",
)
async def rebuild_clusters(db: AsyncSession = Depends(get_db)):
    """
    Recomputes report-to-report relationships, updates cluster memberships,
    calculates temporal pattern escalation scores, and generates Pattern Escalation Alerts.
    Preserves all original source report data.
    """
    try:
        return await ClusteringService.rebuild_clusters(db)
    except Exception as exc:
        logger.error(f"Cluster rebuild failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cluster rebuild failed: {exc}",
        )


@router.get(
    "/{cluster_id}",
    response_model=ClusterDetailResponse,
    summary="Get Cluster Details & Timeline",
)
async def get_cluster_detail(
    cluster_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns detailed cluster information including member reports, temporal timeline
    visualization events, common safety mechanism breakdown, and 'Why Escalating?' explanation.
    """
    detail = await ClusteringService.get_cluster_detail(cluster_id, db)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Precursor cluster '{cluster_id}' not found.",
        )
    return detail
