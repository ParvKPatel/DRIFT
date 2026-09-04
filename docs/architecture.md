# DRIFT — Architectural Specification

## System Purpose & Vision

DRIFT is an evidence-backed HSE decision-support system designed to detect Serious Injury & Fatality (SIF) precursors in safety report text narratives.

Unlike traditional text classifiers that evaluate reports in isolation, the central product idea of DRIFT is **PRECURSOR ACCUMULATION**. A single safety report may appear minor in isolation; however, multiple reports involving the same energy mechanism, asset, activity, or barrier failure across time reveal emerging precursor patterns that precede catastrophic incidents.

---

## Core System Architecture

```mermaid
flowchart TD
    subgraph Data Ingestion & Storage
        CSV[CSV / Field Safety Reports] -->|POST /api/v1/reports/upload| Ingest[Validation & Ingestion Service]
        Ingest -->|Insert Raw Fields| RawDB[(PostgreSQL: 'reports' Table)]
    end

    subgraph AI Safety Intelligence Engine
        RawDB -->|Extract Unprocessed Narratives| Extract[Safety Extraction Provider]
        Extract -->|Extracted Safety Facts| Screening[SIF/FPI Screening Engine]
        Screening -->|Map Life-Saving Rules| LSR[LSR Mapping Engine]
        LSR -->|Insert AI Facts| AIDB[(PostgreSQL: 'safety_analysis' Table)]
    end

    subgraph Precursor Intelligence & Vector Storage
        AIDB -->|Generate Vectors| Embed[Embedding Provider]
        Embed -->|Store Vectors| VecDB[(pgvector Embeddings)]
        VecDB -->|Semantic Similarity Search| Cluster[Precursor Accumulation Engine]
        Cluster -->|Detect Escalation| Escalation[Escalation & Barrier Intelligence]
    end

    subgraph Presentation & Decision Support
        Escalation -->|Serve Prioritised Queues| API[FastAPI REST Services]
        API -->|JSON REST Responses| Dashboard[Next.js Industrial Control Room Dashboard]
        Dashboard -->|Triage & Action| User[HSE Safety Analysts & Engineers]
    end
```

---

## Source Data vs. AI Representation Isolation

To guarantee data integrity and satisfy **Principle 2 (Preserve Source Data)**, the architecture enforces strict separation between raw field data and AI analytical data:

```mermaid
erDiagram
    reports ||--o| safety_analysis : "analyzed_by (1:1)"
    
    reports {
        string report_id PK
        string site
        string unit
        string incident_type
        string incident_cause
        string narrative
        string corrective_action
        date report_date
    }

    safety_analysis {
        int id PK
        string report_id FK
        string hazard
        enum energy_source
        string exposure
        string barrier
        enum barrier_condition
        enum sif_fpi_potential
        enum evidence_status
        string life_saving_rule
        float priority_score
        enum priority_level
    }
```

---

## Core Product Principles

1. **Evidence First**: AI safety facts are strictly annotated with evidence levels (`EXPLICIT`, `INFERRED`, `UNKNOWN`). Facts lacking narrative evidence default to `UNKNOWN`.
2. **Preserve Source Data**: Source fields (`reports`) are immutable and never overwritten by AI interpretation (`safety_analysis`).
3. **Decision Support Only**: DRIFT prioritizes reports for human safety officers; it does not replace HSE personnel or claim predictive perfection.
4. **Uncertainty is Valid**: The system explicitly supports `YES`, `NO`, and `UNCERTAIN` outputs.
5. **Human-in-the-Loop**: Ambiguous and high-risk precursor findings populate a dedicated HSE Human Review Queue.
