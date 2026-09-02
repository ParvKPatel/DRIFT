from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RowValidationError(BaseModel):
    row_number: int
    report_id: Optional[str] = None
    column_name: Optional[str] = None
    error_type: str  # "ERROR" or "WARNING"
    message: str


class FieldQualityStats(BaseModel):
    total_count: int = 0
    present_count: int = 0
    missing_count: int = 0
    completeness_percentage: float = 0.0


class IngestionResultResponse(BaseModel):
    ingestion_id: str
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    imported_rows: int
    errors: List[RowValidationError] = []
    warnings: List[RowValidationError] = []
    field_completeness: Dict[str, FieldQualityStats] = {}
    message: str
