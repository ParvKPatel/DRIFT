# API Specification

All backend endpoints are prefixed with `/api/v1`.

## Health & Metadata Endpoints

### `GET /api/v1/health`
- **Summary**: Liveness health check
- **Response**:
```json
{
  "status": "ok"
}
```

### `GET /api/v1/health/database`
- **Summary**: Database connectivity verification
- **Response**:
```json
{
  "status": "ok",
  "database": "connected"
}
```

### `GET /api/v1/meta`
- **Summary**: Application metadata & environment parameters
- **Response**:
```json
{
  "application_name": "OIL SENTINEL",
  "version": "0.1.0-phase1",
  "environment": "development",
  "api_prefix": "/api/v1",
  "ai_provider": "mock",
  "embedding_provider": "mock"
}
```

---

## Safety Report Endpoints

### `GET /api/v1/reports`
- **Summary**: List safety reports stored in database
- **Response**: Array of `ReportRead` JSON objects.

### `POST /api/v1/reports/upload`
- **Summary**: Upload CSV safety report dataset
- **Payload**: `multipart/form-data` with `file`
- **Response**:
```json
{
  "status": "success",
  "message": "Dataset 'safety_reports.csv' received successfully.",
  "filename": "safety_reports.csv",
  "rows_processed": 0,
  "mode": "phase1_upload_stub"
}
```

---

## Standard Error Response Format

All API errors conform to the standard error envelope format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid report payload",
    "details": {}
  }
}
```
