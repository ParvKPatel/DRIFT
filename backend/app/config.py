from pydantic_settings import BaseSettings
from pydantic import Field
import os
from typing import Optional


class Settings(BaseSettings):
    APP_ENV: str = Field(default="development")
    APP_NAME: str = Field(default="DRIFT")
    API_V1_PREFIX: str = Field(default="/api/v1")
    LOG_LEVEL: str = Field(default="INFO")

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/oil_sentinel"
    )
    SYNC_DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/oil_sentinel"
    )

    AI_PROVIDER: str = Field(default="mock")
    AI_API_KEY: Optional[str] = Field(default=None)
    AI_MODEL: str = Field(default="gpt-4o")

    EMBEDDING_PROVIDER: str = Field(default="mock", description="mock | local | openai")
    EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-mpnet-base-v2")

    MAX_UPLOAD_SIZE_MB: int = Field(default=50)

    # Phase 5 & 6 Priority Engine Weights (Normalized to 0-100)
    PRIORITY_WEIGHT_SIF: float = Field(default=0.40, description="Weight for SIF evidence score")
    PRIORITY_WEIGHT_BARRIER: float = Field(default=0.25, description="Weight for barrier score")
    PRIORITY_WEIGHT_RECURRENCE: float = Field(default=0.25, description="Weight for recurrence score (Phase 6)")
    PRIORITY_WEIGHT_NOVELTY: float = Field(default=0.0, description="Weight for novelty score (Phase 6)")
    PRIORITY_WEIGHT_ANOMALY: float = Field(default=0.10, description="Weight for escalation score (Phase 6)")

    # Phase 6 Similarity & Clustering Configuration
    SIMILARITY_WEIGHT_SEMANTIC: float = Field(default=0.50)
    SIMILARITY_WEIGHT_MECHANISM: float = Field(default=0.30)
    SIMILARITY_WEIGHT_STRUCTURED: float = Field(default=0.20)
    SIMILARITY_MIN_THRESHOLD: float = Field(default=0.50)
    CLUSTER_EDGE_THRESHOLD: float = Field(default=0.65)
    ESCALATION_RECENCY_HALF_LIFE_DAYS: float = Field(default=30.0)

    # Priority Level Score Thresholds (0-100)
    PRIORITY_THRESHOLD_CRITICAL: float = Field(default=80.0)
    PRIORITY_THRESHOLD_HIGH: float = Field(default=60.0)
    PRIORITY_THRESHOLD_REVIEW: float = Field(default=35.0)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


settings = Settings()
