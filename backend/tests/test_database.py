import pytest
from app.config import settings
from app.database import Base
from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis


def test_database_model_metadata():
    assert "reports" in Base.metadata.tables
    assert "safety_analysis" in Base.metadata.tables
    
    reports_table = Base.metadata.tables["reports"]
    assert "report_id" in reports_table.columns
    assert "narrative" in reports_table.columns
    
    safety_table = Base.metadata.tables["safety_analysis"]
    assert "sif_fpi_potential" in safety_table.columns
    assert "evidence_status" in safety_table.columns


def test_database_url_configuration():
    assert settings.DATABASE_URL is not None
    assert "drift" in settings.DATABASE_URL
