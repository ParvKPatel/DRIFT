# DRIFT — Serious Injury & Fatality (SIF) Precursor Engine

> **Phase 9 Status**: Completed — Testing, Evaluation & Robustness, Reproducible Evaluation Runner CLI, Confusion Matrix, Critical Misses & Abstention Metrics, Data Leakage Audit, and Database-Driven Evaluation Dashboard.

DRIFT is a specialized decision-support engine engineered to process unstructured industrial safety reports and identify precursor patterns indicating high potential for Serious Injury or Fatality (SIF).

---

## Key Features (Phases 1–9)

- **Model Benchmarking & Safety Evaluation (`/evaluation`)**: Transparent, reproducible evaluation suite calculating Precision, Recall, F1, F2 (safety-biased), PR-AUC, 2x2 Confusion Matrix, and Critical Misses against a 25-case Reference Standard.
- **Strict Anti-Fabrication**: Clearly labels reference evaluations as `SYNTHETIC / DEMO EVALUATION DATA`. Real calculations without hardcoded or inflated claims.
- **Data Leakage & Invariance Audits**: Rigorous test suites ensuring target-label-leaking fields (`fixed_short_description`, review decisions) are excluded from model inputs, and testing synonym/phrasing robustness (`struck-by` vs `ejected at speed`).
- **Abstention / Uncertainty Capability**: Evaluates and preserves model uncertainty (`UNCERTAIN`) when narrative evidence is insufficient rather than forcing unjustified certainty.
- **HSE Review & Human-in-the-Loop Command Center (`/review`)**: Decision-support queue where safety officers verify, override, reject, or request more information on AI findings.
- **Dual-State Transparency**: Original AI assessments and human-reviewed conclusions remain stored and displayed side-by-side (`original_ai_sif_potential` vs `final_sif_potential`), ensuring full traceability and zero data overwrites.
- **Auditable History & Decision Rationale**: Every review action records WHO, WHAT, WHEN, and WHY (rationale comment, rejection code, or missing information field tags).
- **HSE Intelligence Command Center (`/`)**: Real database-driven dashboard transforming safety facts, SIF screening, Life-Saving Rules, priority rankings, and precursor clusters into actionable executive information.
- **Precursor Density vs. Concentration**: Strictly calculates normalized density ($\text{SIF precursors} / \text{man\_hours}$) only when a valid exposure denominator exists; clearly labels fallback precursor concentration share otherwise.
- **Site & Barrier Intelligence Matrices (`/sites`, `/barriers`)**: Comprehensive cross-site precursor density rankings and barrier degradation matrices (INTACT, DEGRADED, FAILED, ABSENT, UNKNOWN) with weakness score rankings and CSV exports.
- **Precursor Clusters & Temporal Escalation (`/clusters`)**: Vector embedding similarity clustering with 30-day exponential decay and shared asset/barrier boost.
- **Dual Data Model Architecture**: Strict architectural separation between **Raw Source Report Data** ([`reports`](file:///Users/parvpatel/SIH%20MVP/backend/app/models/reports.py)) and **AI Safety Representation** ([`safety_analysis`](file:///Users/parvpatel/SIH%20MVP/backend/app/models/safety_analysis.py)). Raw source fields are never overwritten.
- **pgvector-Enabled Database**: PostgreSQL 16 schema with `pgvector` vector extension, foreign keys, composite indexes, and enum constraints.
- **Robust CSV Ingestion Engine**: Accepts CSV datasets (`POST /api/v1/reports/upload`), validates mandatory fields, handles malformed formats safely, detects duplicates (`SAFE SKIP`), and produces field completeness logs.
- **Synthetic Demo Seeding**: Instant synthetic dataset population (`POST /api/v1/reports/seed`) featuring realistic industrial near-miss scenarios (pin ejection, hammer slipping, wire trip hazards, hydraulic leaks, eyewash breakdown).
- **Industrial Control Room UI**: Clean enterprise UI pages for CSV dataset upload ([`/upload`](http://localhost:3000/upload)), report register ([`/reports`](http://localhost:3000/reports)), and detailed report inspector ([`/reports/[id]`](http://localhost:3000/reports/DEMO-001)).
- **Comprehensive Test Suite**: Automated pytest suite enforcing database model integrity, CSV validation rules, source data preservation, and `NULL` vs `UNKNOWN` separation.

---

## Quick Start & Verification

### 1. Start PostgreSQL with pgvector (Docker Compose)

```bash
make db-up
```

### 2. Run Alembic Database Migrations

```bash
cd backend
alembic upgrade head
```

### 3. Seed Synthetic Demo Data

```bash
curl -X POST http://localhost:8000/api/v1/reports/seed
```

### 4. Run Backend Server

```bash
make dev-backend
```

### 5. Run Frontend Application

```bash
make dev-frontend
```

Access the UI at: `http://localhost:3000`

---

## Automated Test Verification

Run the full pytest suite:

```bash
make test-backend
```

Run frontend lint & type checks:

```bash
make lint-frontend
```

---

## Core Data Rules

1. **Source Preservation**: Raw source fields belong strictly to `reports` and are never modified by AI processes.
2. **Missing vs Uncertainty**: Missing source data is persisted strictly as `NULL`. Analytical uncertainty is represented by explicit `UNKNOWN` / `UNCERTAIN` enums.
3. **No External AI Requirement**: Phase 2 operates 100% locally without requiring external AI API keys.
