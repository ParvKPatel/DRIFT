from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional

from app.database import get_db
from app.models.reports import Report
from app.schemas.reports import (
    ReportRead,
    ReportListResponse,
    ReportStatsResponse
)
from app.schemas.ingestion import IngestionResultResponse
from app.schemas.safety_extraction import (
    AnalysisRequest,
    BatchAnalysisRequest,
    AnalysisResultResponse,
    BatchAnalysisResultResponse,
)
from sqlalchemy.orm import selectinload
from app.models.safety_analysis import SafetyAnalysis
from app.schemas.sif_screening import (
    SifScreeningRequest,
    BatchSifScreeningRequest,
    SifScreeningResult,
    BatchSifScreeningResponse,
)
from app.schemas.lsr_mapping import (
    LsrMappingRequest,
    BatchLsrMappingRequest,
    LsrMappingResult,
    BatchLsrMappingResponse,
)
from app.schemas.priority_engine import (
    PriorityRequest,
    BatchPriorityRequest,
    PriorityResult,
    BatchPriorityResponse,
    FullIntelligenceResult,
)
from app.services.ingestion import CSVIngestionService
from app.services.seed import seed_synthetic_reports
from app.services.extraction_service import SafetyExtractionService
from app.services.sif_screening_service import SifScreeningService
from app.services.lsr_mapping_service import LsrMappingService
from app.services.priority_service import PriorityService
from app.services.intelligence_service import IntelligenceService
from app.services.similarity_service import SimilarityService
from app.schemas.similarity_schemas import SimilarReportResponse
from app.utils.logging import logger

router = APIRouter(prefix="/reports", tags=["Safety Reports"])



@router.get("", response_model=ReportListResponse, summary="List Safety Reports")
async def list_reports(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    site: Optional[str] = Query(None, description="Filter by operational site"),
    incident_type: Optional[str] = Query(None, description="Filter by incident type"),
    incident_cause: Optional[str] = Query(None, description="Filter by incident cause"),
    search: Optional[str] = Query(None, description="Search in narrative or short description"),
    db: AsyncSession = Depends(get_db)
):
    """Returns paginated safety reports with filtering and search capabilities."""
    query = select(Report)
    count_query = select(func.count(Report.id))

    filters = []
    if site:
        filters.append(Report.site.ilike(f"%{site}%"))
    if incident_type:
        filters.append(Report.incident_type.ilike(f"%{incident_type}%"))
    if incident_cause:
        filters.append(Report.incident_cause.ilike(f"%{incident_cause}%"))
    if search:
        search_filter = or_(
            Report.narrative.ilike(f"%{search}%"),
            Report.fixed_short_description.ilike(f"%{search}%"),
            Report.report_id.ilike(f"%{search}%")
        )
        filters.append(search_filter)

    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one() or 0

    offset = (page - 1) * size
    query = query.options(selectinload(Report.safety_analysis)).order_by(Report.created_at.desc(), Report.id.desc()).offset(offset).limit(size)
    
    result = await db.execute(query)
    reports = result.scalars().all()

    items = []
    for r in reports:
        dto = ReportRead.model_validate(r)
        if r.safety_analysis:
            sa = r.safety_analysis
            dto.sif_fpi_potential = sa.sif_fpi_potential
            dto.screening_status = sa.screening_status
            dto.primary_life_saving_rule = sa.primary_life_saving_rule or sa.life_saving_rule
            dto.priority_score = sa.priority_score
            dto.priority_level = sa.priority_level
        items.append(dto)

    pages = (total + size - 1) // size if total > 0 else 1

    return ReportListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/stats", response_model=ReportStatsResponse, summary="Get Report Statistics & Data Quality")
async def get_report_stats(db: AsyncSession = Depends(get_db)):
    """Returns dataset completeness and breakdown statistics."""
    total_res = await db.execute(select(func.count(Report.id)))
    total_reports = total_res.scalar_one() or 0

    syn_res = await db.execute(select(func.count(Report.id)).where(Report.provenance == "SYNTHETIC"))
    synthetic_count = syn_res.scalar_one() or 0

    oil_res = await db.execute(select(func.count(Report.id)).where(Report.provenance == "OIL_EXPORT"))
    oil_export_count = oil_res.scalar_one() or 0

    site_res = await db.execute(select(func.count(func.distinct(Report.site))))
    sites_count = site_res.scalar_one() or 0

    date_res = await db.execute(select(func.max(Report.report_date)))
    latest_report_date = date_res.scalar_one()

    # Calculate completeness for key fields
    fields_to_check = [
        ("report_date", Report.report_date),
        ("site", Report.site),
        ("unit", Report.unit),
        ("functional_location", Report.functional_location),
        ("incident_type", Report.incident_type),
        ("incident_cause", Report.incident_cause),
        ("fixed_short_description", Report.fixed_short_description),
        ("narrative", Report.narrative),
        ("man_hours", Report.man_hours)
    ]

    completeness: dict = {}
    for name, col in fields_to_check:
        cnt_res = await db.execute(select(func.count(Report.id)).where(col.isnot(None)))
        present = cnt_res.scalar_one() or 0
        pct = round((present / total_reports * 100.0), 1) if total_reports > 0 else 0.0
        completeness[name] = pct

    return ReportStatsResponse(
        total_reports=total_reports,
        synthetic_count=synthetic_count,
        oil_export_count=oil_export_count,
        sites_count=sites_count,
        latest_report_date=latest_report_date,
        field_completeness=completeness
    )


@router.post("/seed", summary="Seed Synthetic Demo Safety Dataset")
async def seed_demo_data(db: AsyncSession = Depends(get_db)):
    """Populates synthetic reference safety reports into database."""
    count = await seed_synthetic_reports(db)
    return {
        "status": "success",
        "message": f"Seeded {count} synthetic reference reports.",
        "seeded_count": count
    }


@router.post("/upload", response_model=IngestionResultResponse, summary="Upload CSV Safety Dataset")
async def upload_reports_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests CSV safety report dataset into reports table.
    Preserves exact source data, detects duplicates, validates required fields.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV dataset files are supported"
        )
    
    logger.info(f"Report dataset upload requested: {file.filename}")
    content = await file.read()
    
    result = await CSVIngestionService.process_csv_upload(
        db=db,
        file_content=content,
        filename=file.filename
    )
    return result


@router.get("/{report_id}", response_model=ReportRead, summary="Get Report Detail by ID")
async def get_report_detail(report_id: str, db: AsyncSession = Depends(get_db)):
    """Returns single safety report by canonical report_id."""
    stmt = select(Report).where(Report.report_id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety report '{report_id}' not found"
        )

    return ReportRead.model_validate(report)


# ── Phase 3: AI Analysis Endpoints ─────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=BatchAnalysisResultResponse,
    summary="Batch AI Safety Fact Extraction",
    tags=["AI Analysis"],
)
async def batch_analyze_reports(
    request: BatchAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger AI safety fact extraction for multiple reports.

    - If report_ids is provided: analyze those specific reports.
    - If report_ids is None: analyze all NOT_ANALYZED reports.
    - batch_size controls maximum concurrent AI calls (default 5, max 20).
    - force_reanalyze=true re-runs even for COMPLETED analyses.

    NOTE: This endpoint does NOT compute SIF/FPI scores (Phase 4+).
    """
    logger.info(
        f"Batch analysis request: report_ids={request.report_ids} "
        f"batch_size={request.batch_size} force={request.force_reanalyze}"
    )
    return await SafetyExtractionService.analyze_batch(
        db=db,
        report_ids=request.report_ids,
        force_reanalyze=request.force_reanalyze,
        batch_size=request.batch_size,
    )


@router.post(
    "/{report_id}/analyze",
    response_model=AnalysisResultResponse,
    summary="Run AI Safety Fact Extraction for One Report",
    tags=["AI Analysis"],
)
async def analyze_report(
    report_id: str,
    request: Optional[AnalysisRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger AI safety fact extraction for a single report.

    Extracts: Activity, Equipment, Hazard, Energy Source, Exposure,
    Exposure Location, Barrier, Barrier Condition, Potential Consequence.

    Evidence spans are stored and linked to the original verbatim narrative.
    Analysis status is tracked (NOT_ANALYZED → PROCESSING → COMPLETED/FAILED).

    Pass ?force_reanalyze=true to re-run a previously completed analysis.
    NOTE: Does NOT compute SIF/FPI potential (that is Phase 4+).
    """
    if request is None:
        request = AnalysisRequest()

    logger.info(
        f"Analysis requested for report={report_id} force={request.force_reanalyze}"
    )

    try:
        return await SafetyExtractionService.analyze_report(
            report_id=report_id,
            db=db,
            force_reanalyze=request.force_reanalyze,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(f"Analysis endpoint error for report={report_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Safety fact extraction failed for report '{report_id}'. Check logs for details.",
        )


@router.get(
    "/{report_id}/analysis",
    response_model=AnalysisResultResponse,
    summary="Get Existing AI Safety Analysis for a Report",
    tags=["AI Analysis"],
)
async def get_report_analysis(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the most recent AI safety analysis for a report without re-running extraction.

    Returns 404 if no analysis exists yet for this report.
    Use POST /{report_id}/analyze to trigger extraction.
    """
    result = await SafetyExtractionService.get_analysis_result(report_id=report_id, db=db)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No AI analysis found for report '{report_id}'. "
                   "Run POST /reports/{report_id}/analyze to generate one.",
        )
    return result


# ── Phase 4: SIF / FPI Intelligence Screening Endpoints ───────────────────

@router.post(
    "/screen-sif",
    response_model=BatchSifScreeningResponse,
    summary="Batch SIF/FPI Precursor Screening",
    tags=["SIF Screening"],
)
async def batch_screen_sif(
    request: BatchSifScreeningRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers SIF/FPI precursor screening for multiple safety reports using the
    deterministic OIL SENTINEL Safety Rule Engine.

    - If report_ids is provided: screens those specific reports.
    - If report_ids is None: screens all COMPLETED reports that are unscreened.
    - Runs 100% locally without external AI API dependency.
    """
    logger.info(f"Batch SIF screening requested: report_ids={request.report_ids}")
    return await SifScreeningService.screen_batch(
        db=db,
        report_ids=request.report_ids,
        force_rescreen=request.force_rescreen,
        batch_size=request.batch_size,
    )


@router.post(
    "/{report_id}/screen-sif",
    response_model=SifScreeningResult,
    summary="Run SIF/FPI Precursor Screening for One Report",
    tags=["SIF Screening"],
)
async def screen_report_sif(
    report_id: str,
    request: Optional[SifScreeningRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Runs deterministic SIF/FPI precursor screening for a single report.

    Evaluates 8 deterministic safety rules (RULE-001 to RULE-008),
    computes 5 transparent screening signals, applies critical rule overrides,
    and returns YES / NO / UNCERTAIN decision with supporting evidence.
    """
    if request is None:
        request = SifScreeningRequest()

    logger.info(f"SIF screening requested for report='{report_id}' force={request.force_rescreen}")

    try:
        return await SifScreeningService.screen_report(
            report_id=report_id,
            db=db,
            force_rescreen=request.force_rescreen,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(f"SIF screening endpoint error for report='{report_id}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SIF screening failed for report '{report_id}'. Check backend logs.",
        )


@router.get(
    "/{report_id}/sif-analysis",
    response_model=SifScreeningResult,
    summary="Get Existing SIF/FPI Screening Result for a Report",
    tags=["SIF Screening"],
)
async def get_report_sif_analysis(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns existing SIF screening result for a report without re-running.

    Returns 404 if report has not been screened yet.
    Use POST /reports/{report_id}/screen-sif to trigger screening.
    """
    result = await SifScreeningService.get_screening_result(report_id=report_id, db=db)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No SIF screening result found for report '{report_id}'. "
                   f"Run POST /reports/{report_id}/screen-sif to generate one.",
        )
    return result


# ── Phase 5: Life-Saving Rule (LSR) Mapping Endpoints ───────────────────────

@router.post(
    "/map-lsr",
    response_model=BatchLsrMappingResponse,
    summary="Batch Life-Saving Rule Mapping",
    tags=["Life-Saving Rules"],
)
async def batch_map_lsr(
    request: BatchLsrMappingRequest,
    db: AsyncSession = Depends(get_db),
):
    """Triggers LSR mapping for multiple safety reports."""
    logger.info(f"Batch LSR mapping requested: report_ids={request.report_ids}")
    return await LsrMappingService.map_batch(
        db=db,
        report_ids=request.report_ids,
        force_remap=request.force_remap,
        batch_size=request.batch_size,
    )


@router.post(
    "/{report_id}/map-lsr",
    response_model=LsrMappingResult,
    summary="Map Life-Saving Rule for One Report",
    tags=["Life-Saving Rules"],
)
async def map_report_lsr(
    report_id: str,
    request: Optional[LsrMappingRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Maps report to the 9 official project Life-Saving Rules with confidence,
    supporting evidence, and rationale. Preserves original incident_cause.
    """
    if request is None:
        request = LsrMappingRequest()

    try:
        return await LsrMappingService.map_report_lsr(
            report_id=report_id,
            db=db,
            force_remap=request.force_remap,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"LSR mapping failed for report='{report_id}': {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/{report_id}/lsr",
    response_model=LsrMappingResult,
    summary="Get Existing LSR Mapping for a Report",
    tags=["Life-Saving Rules"],
)
async def get_report_lsr(report_id: str, db: AsyncSession = Depends(get_db)):
    """Returns existing LSR mapping result for a report."""
    result = await LsrMappingService.get_lsr_result(report_id=report_id, db=db)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No LSR mapping found for report '{report_id}'. Run POST /reports/{report_id}/map-lsr.",
        )
    return result


# ── Phase 5: HSE Priority Engine Endpoints ─────────────────────────────────

@router.post(
    "/calculate-priority",
    response_model=BatchPriorityResponse,
    summary="Batch HSE Priority Calculation",
    tags=["HSE Priority"],
)
async def batch_calculate_priority(
    request: BatchPriorityRequest,
    db: AsyncSession = Depends(get_db),
):
    """Calculates 0-100 HSE priority ranking for multiple safety reports."""
    logger.info(f"Batch priority calculation requested: report_ids={request.report_ids}")
    return await PriorityService.calculate_batch(
        db=db,
        report_ids=request.report_ids,
        force_recalculate=request.force_recalculate,
        batch_size=request.batch_size,
    )


@router.post(
    "/{report_id}/calculate-priority",
    response_model=PriorityResult,
    summary="Calculate HSE Priority for One Report",
    tags=["HSE Priority"],
)
async def calculate_report_priority(
    report_id: str,
    request: Optional[PriorityRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculates 0-100 HSE Priority ranking score and level (CRITICAL, HIGH-PRIORITY,
    SAFETY REVIEW, ROUTINE, UNCERTAIN) with component breakdown and safety overrides.
    """
    if request is None:
        request = PriorityRequest()

    try:
        return await PriorityService.calculate_priority(
            report_id=report_id,
            db=db,
            force_recalculate=request.force_recalculate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Priority calculation failed for report='{report_id}': {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/{report_id}/priority",
    response_model=PriorityResult,
    summary="Get Existing HSE Priority Result for a Report",
    tags=["HSE Priority"],
)
async def get_report_priority(report_id: str, db: AsyncSession = Depends(get_db)):
    """Returns existing HSE priority calculation for a report."""
    result = await PriorityService.get_priority_result(report_id=report_id, db=db)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No priority result found for report '{report_id}'. Run POST /reports/{report_id}/calculate-priority.",
        )
    return result


# ── Phase 5: Combined Full Intelligence Pipeline Endpoints ─────────────────

@router.post(
    "/{report_id}/intelligence",
    response_model=FullIntelligenceResult,
    summary="Run Full Intelligence Pipeline for One Report",
    tags=["Report Intelligence"],
)
async def run_report_intelligence(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Runs full intelligence pipeline (Phase 3 Fact Extraction -> Phase 4 SIF Screening
    -> Phase 5 LSR Mapping -> Phase 5 HSE Priority) in a single request.
    """
    try:
        return await IntelligenceService.process_full_intelligence(
            report_id=report_id,
            db=db,
            force_reanalyze=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Full intelligence pipeline failed for report='{report_id}': {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ── Phase 6: Similar Report Retrieval Endpoint ──────────────────────────────

@router.get(
    "/{report_id}/similar",
    response_model=SimilarReportResponse,
    summary="Retrieve Top Similar Reports with Shared Mechanism Explanation",
    tags=["Similarity & Relationships"],
)
async def get_similar_reports(
    report_id: str,
    top_k: int = Query(5, ge=1, le=20, description="Top K similar reports to return"),
    min_threshold: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum similarity threshold (0.0 to 1.0)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves top K semantically and structurally similar reports for a target report.

    Combines semantic narrative similarity, safety mechanism similarity (hazard, energy,
    exposure, consequence), and structured metadata overlap (activity, equipment, barrier, LSR, location).

    Returns shared mechanism breakdown, date distance, and similarity bands.
    """
    try:
        return await SimilarityService.get_similar_reports(
            report_id=report_id,
            db=db,
            top_k=top_k,
            min_threshold=min_threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Similar reports retrieval failed for report='{report_id}': {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))




