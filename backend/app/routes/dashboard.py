"""
Phase 7 — Dashboard API Router

Exposes real, database-driven endpoints for the OIL SENTINEL Intelligence Dashboard:
- GET /dashboard/summary
- GET /dashboard/trends
- GET /dashboard/sites
- GET /dashboard/activities
- GET /dashboard/hazards
- GET /dashboard/lsr
- GET /dashboard/barriers
- GET /dashboard/recurring-mechanisms
- GET /dashboard/alerts
- GET /dashboard/data-quality
- GET /dashboard/export/{table_name} (CSV export)
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date
import io
import csv

from app.database import get_db
from app.schemas.dashboard_schemas import (
    DashboardSummary,
    TrendPoint,
    SiteSummary,
    ActivitySummary,
    HazardSummary,
    LsrSummary,
    BarrierSummary,
    RecurringMechanismSummary,
    RecentAlertSummary,
    DataQualitySummary,
)
from app.services.dashboard_service import DashboardService
from app.utils.logging import logger

router = APIRouter(prefix="/dashboard", tags=["Intelligence Dashboard"])


@router.get("/summary", response_model=DashboardSummary, summary="Get Executive Dashboard Summary KPIs")
async def get_summary(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    site: Optional[str] = Query(None, description="Site filter"),
    unit: Optional[str] = Query(None, description="Unit filter"),
    functional_location: Optional[str] = Query(None, description="Functional location filter"),
    employment_type: Optional[str] = Query(None, description="Employee or Contractor filter"),
    sif_status: Optional[str] = Query(None, description="SIF decision filter (YES/NO/UNCERTAIN)"),
    priority_level: Optional[str] = Query(None, description="HSE Priority level filter"),
    lsr: Optional[str] = Query(None, description="Life-Saving Rule filter"),
    activity: Optional[str] = Query(None, description="Activity filter"),
    hazard: Optional[str] = Query(None, description="Hazard filter"),
    barrier_condition: Optional[str] = Query(None, description="Barrier condition filter"),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.get_summary(
        db=db,
        start_date=start_date,
        end_date=end_date,
        site=site,
        unit=unit,
        functional_location=functional_location,
        employment_type=employment_type,
        sif_status=sif_status,
        priority_level=priority_level,
        lsr=lsr,
        activity=activity,
        hazard=hazard,
        barrier_condition=barrier_condition,
    )


@router.get("/trends", response_model=List[TrendPoint], summary="Get SIF/FPI Time Series Trends")
async def get_trends(
    window: str = Query("30d", description="Time window (7d, 30d, 90d, 12m)"),
    site: Optional[str] = Query(None, description="Site filter"),
    lsr: Optional[str] = Query(None, description="Life-Saving Rule filter"),
    priority_level: Optional[str] = Query(None, description="Priority level filter"),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.get_trends(
        db=db, window=window, site=site, lsr=lsr, priority_level=priority_level
    )


@router.get("/sites", response_model=List[SiteSummary], summary="Get Site & Functional Location Intelligence")
async def get_sites(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.get_sites(db=db, start_date=start_date, end_date=end_date)


@router.get("/activities", response_model=List[ActivitySummary], summary="Get Activity Precursor Intelligence")
async def get_activities(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.get_activities(db=db, start_date=start_date, end_date=end_date)


@router.get("/hazards", response_model=List[HazardSummary], summary="Get Hazard Precursor Intelligence")
async def get_hazards(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.get_hazards(db=db, start_date=start_date, end_date=end_date)


@router.get("/lsr", response_model=List[LsrSummary], summary="Get 9 Official Life-Saving Rules Intelligence")
async def get_lsr(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.get_lsr(db=db, start_date=start_date, end_date=end_date)


@router.get("/barriers", response_model=List[BarrierSummary], summary="Get Barrier Intelligence & Weakness Ranking")
async def get_barriers(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.get_barriers(db=db, start_date=start_date, end_date=end_date)


@router.get("/recurring-mechanisms", response_model=List[RecurringMechanismSummary], summary="Get Top Recurring Precursor Mechanisms")
async def get_recurring_mechanisms(db: AsyncSession = Depends(get_db)):
    return await DashboardService.get_recurring_mechanisms(db=db)


@router.get("/alerts", response_model=List[RecentAlertSummary], summary="Get Recent Precursor Pattern Escalation Alerts")
async def get_alerts(
    limit: int = Query(10, ge=1, le=50, description="Max alerts to return"),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.get_alerts(db=db, limit=limit)


@router.get("/data-quality", response_model=DataQualitySummary, summary="Get Data Quality & Coverage Summary")
async def get_data_quality(db: AsyncSession = Depends(get_db)):
    return await DashboardService.get_data_quality(db=db)


@router.get("/export/{table_name}", summary="Export Dashboard Table to CSV")
async def export_table_csv(
    table_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Streams CSV export for sites, barriers, or clusters."""
    output = io.StringIO()
    writer = csv.writer(output)

    if table_name == "sites":
        sites = await DashboardService.get_sites(db=db)
        writer.writerow([
            "Site", "Total Reports", "SIF Precursors", "SIF Uncertain", "High Priority",
            "Critical", "Clusters", "Escalating Clusters", "Man-Hours", "Precursor Density",
            "Precursor Concentration %"
        ])
        for s in sites:
            writer.writerow([
                s.site, s.report_count, s.sif_count, s.sif_uncertain_count, s.high_priority_count,
                s.critical_count, s.cluster_count, s.escalating_cluster_count, s.total_man_hours,
                s.precursor_density if s.has_valid_man_hours else "N/A",
                f"{s.precursor_concentration_pct}%"
            ])
    elif table_name == "barriers":
        barriers = await DashboardService.get_barriers(db=db)
        writer.writerow([
            "Barrier", "Total Mentions", "Intact", "Degraded", "Failed", "Absent",
            "Unknown", "SIF Count", "High Priority", "Weakness Score"
        ])
        for b in barriers:
            writer.writerow([
                b.barrier, b.total_mentions, b.intact_count, b.degraded_count, b.failed_count,
                b.absent_count, b.unknown_count, b.sif_count, b.high_priority_count, b.weakness_score
            ])
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported export table '{table_name}'. Supported: 'sites', 'barriers'")

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=oil_sentinel_{table_name}_export.csv"}
    )
