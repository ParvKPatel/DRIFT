import csv
import io
import uuid
from datetime import datetime, date, time
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.reports import Report
from app.schemas.enums import ProvenanceType
from app.schemas.ingestion import (
    IngestionResultResponse,
    RowValidationError,
    FieldQualityStats
)
from app.utils.logging import logger

HEADER_MAPPING = {
    "report_id": ["report_id", "report id", "incident id", "id", "report_no"],
    "source_system_id": ["source_system_id", "source system id", "src_id"],
    "report_date": ["report_date", "report date", "date", "incident_date"],
    "report_time": ["report_time", "report time", "time", "incident_time"],
    "site": ["site", "location", "facility", "plant"],
    "unit": ["unit", "plant unit", "section"],
    "shift": ["shift", "work shift"],
    "functional_location": ["functional_location", "functional location", "floc"],
    "functional_location_description": ["functional_location_description", "functional location description", "floc_desc"],
    "item_no": ["item_no", "item no", "item number"],
    "incident_type": ["incident_type", "incident type", "type"],
    "incident_sub_type": ["incident_sub_type", "incident sub type", "sub type", "subtype"],
    "incident_cause": ["incident_cause", "incident cause", "cause"],
    "fixed_short_description": ["fixed_short_description", "fixed short description", "short description", "title"],
    "line_item": ["line_item", "line item"],
    "narrative": ["narrative", "description", "details", "safety event narrative", "event description"],
    "corrective_action": ["corrective_action", "corrective action", "immediate action"],
    "preventive_action": ["preventive_action", "preventive action"],
    "man_hours": ["man_hours", "man hours", "exposure hours"],
    "lost_time": ["lost_time", "lost time", "lost hours"],
    "operational_time_lost": ["operational_time_lost", "operational time lost", "downtime"],
    "financial_implication": ["financial_implication", "financial implication", "cost"],
    "currency": ["currency"],
    "affected_person_type": ["affected_person_type", "affected person type"],
    "employee_or_contractor": ["employee_or_contractor", "employee or contractor", "employment type"],
    "designation": ["designation", "role"],
    "contractor_name": ["contractor_name", "contractor name", "vendor"],
    "actual_outcome": ["actual_outcome", "actual outcome", "outcome"]
}


def normalize_header(header: str) -> str:
    cleaned = header.strip().lower().replace("_", " ").replace("-", " ")
    for canonical_field, aliases in HEADER_MAPPING.items():
        for alias in aliases:
            if cleaned == alias.replace("_", " ").replace("-", " "):
                return canonical_field
    return header.strip()


def parse_date_safe(val: Optional[str]) -> Tuple[Optional[date], Optional[str]]:
    if not val or not val.strip():
        return None, None
    s = val.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.date(), None
        except ValueError:
            continue
    return None, f"Invalid date format '{val}' (expected YYYY-MM-DD)"


def parse_time_safe(val: Optional[str]) -> Tuple[Optional[time], Optional[str]]:
    if not val or not val.strip():
        return None, None
    s = val.strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.time(), None
        except ValueError:
            continue
    return None, f"Invalid time format '{val}' (expected HH:MM:SS)"


def parse_float_safe(val: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
    if not val or not val.strip():
        return None, None
    try:
        return float(val.strip()), None
    except ValueError:
        return None, f"Invalid numeric value '{val}'"


class CSVIngestionService:
    @staticmethod
    async def process_csv_upload(
        db: AsyncSession,
        file_content: bytes,
        filename: str,
        provenance: ProvenanceType = ProvenanceType.OIL_EXPORT
    ) -> Tuple[IngestionResultResponse, List[str]]:
        ingestion_id = f"ING-{uuid.uuid4().hex[:8].upper()}"
        
        try:
            text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = file_content.decode("latin-1", errors="replace")

        reader = csv.reader(io.StringIO(text))
        try:
            raw_headers = next(reader)
        except StopIteration:
            return IngestionResultResponse(
                ingestion_id=ingestion_id,
                filename=filename,
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                duplicate_rows=0,
                imported_rows=0,
                errors=[RowValidationError(row_number=0, error_type="ERROR", message="CSV file is completely empty")],
                message="Failed: Empty CSV file"
            ), []

        header_map = {idx: normalize_header(h) for idx, h in enumerate(raw_headers)}

        errors: List[RowValidationError] = []
        warnings: List[RowValidationError] = []
        reports_to_insert: List[Report] = []
        
        total_rows = 0
        duplicate_rows = 0
        invalid_rows = 0

        # Fetch existing report_ids to prevent duplicate insertion
        result = await db.execute(select(Report.report_id))
        existing_report_ids = set(result.scalars().all())

        field_counts: Dict[str, int] = {k: 0 for k in HEADER_MAPPING.keys()}

        for row_idx, row in enumerate(reader, start=2):
            if not row or not any(cell.strip() for cell in row):
                continue  # Skip empty lines cleanly
            
            total_rows += 1
            row_data: Dict[str, Any] = {}
            
            for idx, cell in enumerate(row):
                if idx in header_map:
                    field_name = header_map[idx]
                    val = cell.strip() if cell else None
                    if val == "":
                        val = None
                    row_data[field_name] = val

            # Check required narrative
            narrative = row_data.get("narrative")
            if not narrative:
                invalid_rows += 1
                errors.append(RowValidationError(
                    row_number=row_idx,
                    report_id=row_data.get("report_id"),
                    column_name="narrative",
                    error_type="ERROR",
                    message="Missing required field 'narrative'"
                ))
                continue

            report_id = row_data.get("report_id")
            if not report_id:
                invalid_rows += 1
                errors.append(RowValidationError(
                    row_number=row_idx,
                    column_name="report_id",
                    error_type="ERROR",
                    message="Missing required identifier 'report_id'"
                ))
                continue

            # Duplicate detection (SAFE SKIP)
            if report_id in existing_report_ids:
                duplicate_rows += 1
                warnings.append(RowValidationError(
                    row_number=row_idx,
                    report_id=report_id,
                    error_type="WARNING",
                    message=f"Duplicate report_id '{report_id}' skipped (SAFE SKIP)"
                ))
                continue

            # Parse typed fields
            report_date, date_err = parse_date_safe(row_data.get("report_date"))
            if date_err:
                warnings.append(RowValidationError(row_number=row_idx, report_id=report_id, column_name="report_date", error_type="WARNING", message=date_err))

            report_time, time_err = parse_time_safe(row_data.get("report_time"))
            if time_err:
                warnings.append(RowValidationError(row_number=row_idx, report_id=report_id, column_name="report_time", error_type="WARNING", message=time_err))

            man_hours, mh_err = parse_float_safe(row_data.get("man_hours"))
            if mh_err:
                warnings.append(RowValidationError(row_number=row_idx, report_id=report_id, column_name="man_hours", error_type="WARNING", message=mh_err))

            lost_time, lt_err = parse_float_safe(row_data.get("lost_time"))
            if lt_err:
                warnings.append(RowValidationError(row_number=row_idx, report_id=report_id, column_name="lost_time", error_type="WARNING", message=lt_err))

            operational_time_lost, opt_err = parse_float_safe(row_data.get("operational_time_lost"))
            if opt_err:
                warnings.append(RowValidationError(row_number=row_idx, report_id=report_id, column_name="operational_time_lost", error_type="WARNING", message=opt_err))

            financial_implication, fin_err = parse_float_safe(row_data.get("financial_implication"))
            if fin_err:
                warnings.append(RowValidationError(row_number=row_idx, report_id=report_id, column_name="financial_implication", error_type="WARNING", message=fin_err))

            # Track field presence
            for field in HEADER_MAPPING.keys():
                if row_data.get(field) is not None:
                    field_counts[field] = field_counts.get(field, 0) + 1

            report_obj = Report(
                report_id=report_id,
                source_system_id=row_data.get("source_system_id"),
                report_date=report_date,
                report_time=report_time,
                site=row_data.get("site"),
                unit=row_data.get("unit"),
                shift=row_data.get("shift"),
                functional_location=row_data.get("functional_location"),
                functional_location_description=row_data.get("functional_location_description"),
                item_no=row_data.get("item_no"),
                incident_type=row_data.get("incident_type"),
                incident_sub_type=row_data.get("incident_sub_type"),
                incident_cause=row_data.get("incident_cause"),
                fixed_short_description=row_data.get("fixed_short_description"),
                line_item=row_data.get("line_item"),
                narrative=narrative,
                corrective_action=row_data.get("corrective_action"),
                preventive_action=row_data.get("preventive_action"),
                man_hours=man_hours,
                lost_time=lost_time,
                operational_time_lost=operational_time_lost,
                financial_implication=financial_implication,
                currency=row_data.get("currency") or "INR",
                affected_person_type=row_data.get("affected_person_type"),
                employee_or_contractor=row_data.get("employee_or_contractor"),
                designation=row_data.get("designation"),
                contractor_name=row_data.get("contractor_name"),
                actual_outcome=row_data.get("actual_outcome"),
                source_file=filename,
                source_row_number=row_idx,
                provenance=provenance
            )
            
            reports_to_insert.append(report_obj)
            existing_report_ids.add(report_id)

        # Execute DB Batch Insert
        if reports_to_insert:
            db.add_all(reports_to_insert)
            await db.commit()

        imported_count = len(reports_to_insert)
        valid_count = imported_count

        # Build quality stats
        quality_stats: Dict[str, FieldQualityStats] = {}
        for field, present_count in field_counts.items():
            pct = round((present_count / total_rows * 100.0), 1) if total_rows > 0 else 0.0
            quality_stats[field] = FieldQualityStats(
                total_count=total_rows,
                present_count=present_count,
                missing_count=total_rows - present_count,
                completeness_percentage=pct
            )

        logger.info(f"Ingestion {ingestion_id} completed: {imported_count} imported, {duplicate_rows} duplicates, {invalid_rows} rejected")

        return IngestionResultResponse(
            ingestion_id=ingestion_id,
            filename=filename,
            total_rows=total_rows,
            valid_rows=valid_count,
            invalid_rows=invalid_rows,
            duplicate_rows=duplicate_rows,
            imported_rows=imported_count,
            errors=errors,
            warnings=warnings,
            field_completeness=quality_stats,
            message=f"Successfully imported {imported_count} of {total_rows} safety reports."
        ), [str(r.report_id) for r in reports_to_insert]
