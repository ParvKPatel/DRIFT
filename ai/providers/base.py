"""
AI Provider Base Interfaces for OIL SENTINEL

Ensures pluggable AI providers (OpenAI, hosted LLM, local model, or Mock).
Never hardcode provider logic into backend routes or core business services.

Phase 3: SafetyExtractionProvider returns SafetyFactsExtractionResponse.
Phase 4+: SIFReasoningProvider and EmbeddingProvider are used.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class SafetyExtractionProvider(ABC):
    """Interface for extracting structured safety facts from report text narratives."""

    PROVIDER_NAME: str = "base"
    MODEL_NAME: str = "unknown"
    ANALYSIS_VERSION: str = "3.0.0"

    @abstractmethod
    async def extract_safety_facts(
        self,
        narrative: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Extracts structured safety facts from narrative text.

        Args:
            narrative: The verbatim safety report narrative text.
            context: Optional dict with additional report metadata
                     (report_id, incident_cause, fixed_short_description, etc.)

        Returns:
            SafetyFactsExtractionResponse instance.

        Providers MUST NOT:
        - Determine SIF/FPI potential (that is Phase 4+)
        - Calculate risk priority scores
        - Overwrite source fields
        - Write to the database
        """
        pass


class EmbeddingProvider(ABC):
    """Interface for generating text vector embeddings for semantic similarity."""

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generates a dense vector embedding for the input text."""
        pass

    @abstractmethod
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates dense vector embeddings for a list of input texts."""
        pass


class SIFReasoningProvider(ABC):
    """Interface for evaluating Serious Injury & Fatality (SIF/FPI) potential (Phase 4+)."""

    @abstractmethod
    async def evaluate_sif_potential(self, safety_facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates SIF potential and confidence based on safety facts.
        Must return evidence status (EXPLICIT, INFERRED, UNKNOWN) and SIF decision (YES, NO, UNCERTAIN).
        NOTE: This interface is intentionally not populated in Phase 3.
        """
        pass
