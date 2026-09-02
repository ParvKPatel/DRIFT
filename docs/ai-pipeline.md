# AI Safety Intelligence Pipeline

OIL SENTINEL combines NLP extraction, deterministic safety rules, vector embeddings, and temporal clustering into a hybrid intelligence pipeline.

## Processing Pipeline Flow

```
Raw Safety Narrative
        ↓
[1. Extraction Provider] (Extract Activity, Equipment, Hazard, Energy, Exposure, Barrier)
        ↓
[2. Evidence Validation] (Annotate EXPLICIT / INFERRED / UNKNOWN)
        ↓
[3. SIF Screening Engine] (Evaluate SIF/FPI Potential: YES / NO / UNCERTAIN)
        ↓
[4. LSR Mapping Engine] (Match against Life-Saving Rules vocabulary)
        ↓
[5. Embedding Engine] (Generate 1536d vector representation)
        ↓
[6. Clustering Engine] (Semantic Similarity & Temporal Precursor Accumulation)
        ↓
[7. Priority Engine] (Compute Composite Priority Score & Level)
```

## AI Provider Abstraction Interface

To prevent vendor lock-in and enable offline execution during hackathon presentations, all AI operations interact through abstract base classes defined in `ai/providers/base.py`:

- `SafetyExtractionProvider`: Interface for structured safety fact extraction.
- `EmbeddingProvider`: Interface for dense vector generation.
- `SIFReasoningProvider`: Interface for SIF screening reasoning.

Implementations are selected dynamically via `AI_PROVIDER` and `EMBEDDING_PROVIDER` environment configuration settings:
- `mock` (Default local testing without API keys)
- `openai` (Hosted API integration)
- `local` (Local open-weights model)
