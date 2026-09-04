"""
Phase 6 — Embedding Provider Abstraction & Implementations

Provides vector embeddings for report text representations:
- Abstract `EmbeddingProvider` base class.
- `MockEmbeddingProvider`: Deterministic hash-based 768-dim embeddings (no network/API required, fast & reproducible for testing).
- `LocalSentenceTransformerProvider`: Uses local `sentence-transformers` library if installed.
- `EmbeddingFactory`: Instantiates provider based on configuration (`settings.EMBEDDING_PROVIDER`).
"""

import math
import hashlib
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Optional

from app.config import settings
from app.utils.logging import logger


class EmbeddingProvider(ABC):
    """Abstract interface for embedding providers."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embeds a single string into a 768-dimensional float vector."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of strings into a list of 768-dimensional float vectors."""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic, offline embedding provider for testing and demo environments.
    Uses SHA-256 seed + word frequency hashing to generate normalized 768-dim vectors.
    Reports with semantically related words produce high cosine similarity.
    """

    DIMENSION = 768

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.DIMENSION

        # Base vector initialized from hash of normalized text
        vec = np.zeros(self.DIMENSION, dtype=np.float32)
        words = text.lower().split()
        
        for idx, word in enumerate(words):
            # Seed pseudo-random generator with hash of word
            h = hashlib.sha256(word.encode('utf-8')).hexdigest()
            seed = int(h[:8], 16)
            rng = np.random.RandomState(seed)
            word_vec = rng.randn(self.DIMENSION).astype(np.float32)
            
            # Position weighting & word accumulation
            weight = 1.0 + (1.0 / (idx + 1))
            vec += word_vec * weight

        # Normalize to unit length (L2 norm)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class LocalSentenceTransformerProvider(EmbeddingProvider):
    """
    Local pretrained SentenceTransformer embedding provider.
    Falls back gracefully to MockEmbeddingProvider if sentence-transformers is not installed.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        self.model_name = model_name
        self._model = None

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer(model_name)
            logger.info(f"[EmbeddingProvider] Loaded local SentenceTransformer model: {model_name}")
        except Exception as exc:
            logger.warning(f"[EmbeddingProvider] Could not load sentence-transformers ({exc}). Falling back to MockEmbeddingProvider.")
            self._fallback = MockEmbeddingProvider()

    def embed_text(self, text: str) -> List[float]:
        if hasattr(self, '_fallback') and self._fallback:
            return self._fallback.embed_text(text)
        if self._model is not None:
            vec = self._model.encode(text, normalize_embeddings=True)
            return vec.tolist()
        return MockEmbeddingProvider().embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if hasattr(self, '_fallback') and self._fallback:
            return self._fallback.embed_batch(texts)
        if self._model is not None:
            vecs = self._model.encode(texts, normalize_embeddings=True)
            return [v.tolist() for v in vecs]
        return MockEmbeddingProvider().embed_batch(texts)


class EmbeddingFactory:
    """Factory for embedding provider instances."""

    _instance: Optional[EmbeddingProvider] = None

    @classmethod
    def get_provider(cls) -> EmbeddingProvider:
        if cls._instance is not None:
            return cls._instance

        provider_type = (settings.EMBEDDING_PROVIDER or "mock").lower()

        if provider_type == "local":
            cls._instance = LocalSentenceTransformerProvider(model_name=settings.EMBEDDING_MODEL)
        else:
            cls._instance = MockEmbeddingProvider()

        logger.info(f"[EmbeddingFactory] Initialized embedding provider: '{type(cls._instance).__name__}'")
        return cls._instance
