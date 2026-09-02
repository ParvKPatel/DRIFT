# PROJECT_SPEC.md — OIL SENTINEL

> **Authoritative Technical Specification & Product Requirements Document**

## 1. Executive Product Overview

**Project Title**: AI/NLP Engine to Detect Serious Injury & Fatality (SIF) Precursors in Unsafe-Act, Unsafe-Condition, Near-Miss and Incident Reports

**System Name**: **OIL SENTINEL**

### 1.1 Objective
OIL SENTINEL is a specialized decision-support engine engineered to process unstructured industrial safety reports and identify precursor patterns indicating high potential for Serious Injury or Fatality (SIF).

### 1.2 The Core Differentiator: Precursor Accumulation
A single safety report viewed in isolation may appear minor (e.g. "shackle pin came loose"). However, when multiple reports across time share the same energy source, activity, equipment, or degraded barrier mechanism, they reveal an **emerging precursor accumulation pattern**. OIL SENTINEL connects reports across time instead of analyzing each report in isolation.

---

## 2. Core User & Target Workflow

**Target User**: HSE Personnel, Safety Analysts, Incident Investigators, and Rig/Plant Managers.

### 2.1 System Workflow
```
Field Reports (CSV / Safety Log)
       ↓
Upload & Schema Validation
       ↓
Raw Report Persistence ('reports')
       ↓
AI Safety Fact Extraction (Activity, Equipment, Hazard, Energy, Exposure, Barrier)
       ↓
Evidence Annotation (EXPLICIT / INFERRED / UNKNOWN)
       ↓
SIF/FPI Screening (YES / NO / UNCERTAIN)
       ↓
Life-Saving Rule Mapping (LSR-01 through LSR-09)
       ↓
Dense Vector Embedding Generation
       ↓
Semantic Similarity & Precursor Clustering
       ↓
Precursor Escalation Detection
       ↓
HSE Priority Queue Ranking
       ↓
Human-in-the-Loop Review
```

---

## 3. Mandatory Safety Principles

1. **Evidence First**: System never invents safety facts. Every AI safety fact is annotated as `EXPLICIT`, `INFERRED`, or `UNKNOWN`.
2. **Preserve Source Data**: Raw source fields belong strictly to `reports` and are never overwritten by AI findings in `safety_analysis`.
3. **Decision Support Only**: OIL SENTINEL prioritizes reports for human safety officers; it does not claim to "predict fatalities" or replace HSE personnel ("OIL SENTINEL is a decision-support screening system, not an autonomous safety authority").
4. **Uncertainty is Valid**: Explicitly supports `YES`, `NO`, and `UNCERTAIN` classification without fake "probability of death" numbers.
5. **Deterministic Safety Override**: Critical safety rules override weak AI extraction signals to avoid dangerous false negatives.
6. **Source Label Leakage Prevention**: Screening reasons from extracted safety facts & narrative, NOT from raw category labels.
7. **Human-in-the-Loop**: High-risk and uncertain cases populate the Human Review Queue.

---

## 3.1 Phase 4: SIF/FPI Screening Architecture

```
Phase 3 Safety Facts (Activity, Equipment, Hazard, Energy, Exposure, Barrier, Consequence)
        ↓
Deterministic Safety Rule Engine (8 OIL SENTINEL Safety Rules)
  + RULE-001: High-Energy Mechanism with Human Exposure (SIF-001)
  + RULE-002: Falling Object Exposure (SIF-007)
  + RULE-003: Unexpected Ejection / Movement in Trajectory (SIF-002)
  + RULE-004: Suspended Load Exposure (SIF-011)
  + RULE-005: Electrical Energy Exposure (SIF-010)
  + RULE-006: Pressurized / Stored Energy Release (SIF-006 / SIF-012)
  + RULE-007: Fall From Height Exposure (SIF-009)
  + RULE-008: Caught-In / Between Equipment Exposure (SIF-008)
        ↓
Transparent Intermediate Screening Signals (0.0 to 1.0)
  • mechanism_signal, exposure_signal, barrier_signal, consequence_signal, evidence_signal
        ↓
SIF/FPI Screening Result: YES | NO | UNCERTAIN
```

---

## 3.2 Phase 5: Life-Saving Rule Mapping & HSE Priority Engine Architecture

```
SIF/FPI Screening Result + Safety Facts
        ↓
Life-Saving Rule Mapping Engine (9 Official Project Rules)
  1. Bypassing Safety Controls   2. Confined Space   3. Driving
  4. Energy Isolation            5. Hot Work         6. Line of Fire
  7. Safe Mechanical Lifting     8. Work Authorisation 9. Working at Height
        ↓
Primary LSR + Secondary LSRs (Evidence-backed, confidence, rationale)
        ↓
HSE Priority Engine (0–100 Score + Priority Level + Safety Overrides)
  • Priority Score = w_sif * sif_score + w_barrier * barrier_score + (Phase 6 components tracked as NOT_YET_AVAILABLE)
  • Levels: CRITICAL | HIGH_PRIORITY_SIF_FPI_PRECURSOR | SAFETY_REVIEW | ROUTINE | UNCERTAIN
        ↓
HSE Review Priority Queue (/priority)
```

---

## 4. MVP Scope & Out-of-Scope Roadmap

### In Scope (MVP Target):
- Monorepo foundation (FastAPI + Next.js + PostgreSQL/pgvector).
- Dual schema data model (`reports` vs `safety_analysis`).
- Pluggable AI provider abstraction (`SafetyExtractionProvider`, `EmbeddingProvider`, `SIFReasoningProvider`).
- Config-driven vocabularies (Energy, Barrier, Life-Saving Rules, Escalation Bands).
- Industrial control room application shell with zero fake analytical statistics.
- Unit and schema test suite.

### Out of Scope (Future Phases):
- Microservices, Kafka, Graph Databases, Kubernetes.
- Automatic risk mitigation execution without human approval.
- Direct training on OIL proprietary live operational data.

---

## 5. Technology Stack Summary

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide icons, Recharts.
- **Backend**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic.
- **Database**: PostgreSQL 16 with `pgvector` extension.
- **Testing**: Pytest, AsyncClient, TypeScript type checking, ESLint.
- **DevOps**: Docker, Docker Compose, Makefile.
