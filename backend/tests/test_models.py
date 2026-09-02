import pytest
from app.database import Base
from app.models import (
    Report,
    SafetyAnalysis,
    Evidence,
    ReportEmbedding,
    SimilarReport,
    Cluster,
    ClusterMember,
    Alert,
    Review,
)


def test_all_domain_models_registered_in_metadata():
    tables = Base.metadata.tables
    expected_tables = [
        "reports",
        "safety_analysis",
        "evidence",
        "report_embeddings",
        "similar_reports",
        "clusters",
        "cluster_members",
        "alerts",
        "reviews",
    ]
    for table in expected_tables:
        assert table in tables, f"Table '{table}' not registered in SQLAlchemy Base metadata."


def test_reports_table_columns_and_constraints():
    reports_table = Base.metadata.tables["reports"]
    assert "report_id" in reports_table.columns
    assert "source_system_id" in reports_table.columns
    assert "narrative" in reports_table.columns
    assert "incident_cause" in reports_table.columns
    assert "provenance" in reports_table.columns
    assert "source_file" in reports_table.columns


def test_safety_analysis_table_columns():
    safety_table = Base.metadata.tables["safety_analysis"]
    assert "report_id" in safety_table.columns
    assert "hazard" in safety_table.columns
    assert "energy_source" in safety_table.columns
    assert "barrier_condition" in safety_table.columns
    assert "sif_fpi_potential" in safety_table.columns
    assert "evidence_status" in safety_table.columns
    assert "analysis_version" in safety_table.columns


def test_evidence_table_columns():
    evidence_table = Base.metadata.tables["evidence"]
    assert "report_id" in evidence_table.columns
    assert "field_name" in evidence_table.columns
    assert "evidence_text" in evidence_table.columns
    assert "evidence_status" in evidence_table.columns
