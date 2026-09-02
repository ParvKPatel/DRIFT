import pytest
from app.services.ingestion import (
    normalize_header,
    parse_date_safe,
    parse_time_safe,
    parse_float_safe,
    CSVIngestionService
)


def test_header_normalization():
    assert normalize_header("Report ID") == "report_id"
    assert normalize_header("Incident ID") == "report_id"
    assert normalize_header("Report Date") == "report_date"
    assert normalize_header("Facility") == "site"
    assert normalize_header("Safety Event Narrative") == "narrative"
    assert normalize_header("Cause") == "incident_cause"


def test_safe_field_parsers():
    d, err = parse_date_safe("2026-08-15")
    assert d is not None and d.year == 2026 and d.month == 8 and d.day == 15
    assert err is None

    d, err = parse_date_safe("15-08-2026")
    assert d is not None and d.day == 15
    assert err is None

    d, err = parse_date_safe("invalid-date")
    assert d is None
    assert err is not None

    t, err = parse_time_safe("14:30:00")
    assert t is not None and t.hour == 14 and t.minute == 30
    assert err is None

    f, err = parse_float_safe("12.5")
    assert f == 12.5
    assert err is None

    f, err = parse_float_safe("invalid-number")
    assert f is None
    assert err is not None
