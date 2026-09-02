"""
AI Provider Factory for OIL SENTINEL

Reads settings.AI_PROVIDER and settings.AI_API_KEY to select the
appropriate AI provider. Falls back to MockSafetyExtractionProvider
if no API key is configured, so development and testing remain possible
without any external service.

Usage:
    provider = get_safety_extraction_provider()
    result = await provider.extract_safety_facts(narrative, context)
"""

from app.config import settings
from app.utils.logging import logger
from ai.providers.base import SafetyExtractionProvider
from ai.providers.mock import MockSafetyExtractionProvider


def get_safety_extraction_provider() -> SafetyExtractionProvider:
    """
    Returns the configured SafetyExtractionProvider instance.

    Provider selection logic:
    1. If AI_PROVIDER == "openai" AND AI_API_KEY is set → OpenAISafetyExtractionProvider
    2. If AI_PROVIDER == "openai" BUT AI_API_KEY is missing → warn + fallback to mock
    3. If AI_PROVIDER == "mock" (default) → MockSafetyExtractionProvider
    4. Unknown AI_PROVIDER → warn + fallback to mock

    Returns:
        SafetyExtractionProvider instance (never None)
    """
    provider_name = (settings.AI_PROVIDER or "mock").lower().strip()

    if provider_name == "openai":
        if not settings.AI_API_KEY:
            logger.warning(
                "[AIFactory] AI_PROVIDER=openai requested but AI_API_KEY is not set. "
                "Falling back to MockSafetyExtractionProvider for safety. "
                "Set AI_API_KEY in .env to enable real AI extraction."
            )
            return _make_mock()

        try:
            from ai.providers.openai_provider import OpenAISafetyExtractionProvider
            logger.info(
                f"[AIFactory] Initializing OpenAISafetyExtractionProvider "
                f"(model={settings.AI_MODEL})"
            )
            return OpenAISafetyExtractionProvider(
                api_key=settings.AI_API_KEY,
                model=settings.AI_MODEL or "gpt-4o",
            )
        except ImportError as exc:
            logger.error(
                f"[AIFactory] Failed to import OpenAISafetyExtractionProvider: {exc}. "
                "Falling back to mock."
            )
            return _make_mock()

    if provider_name == "mock":
        logger.info("[AIFactory] Using MockSafetyExtractionProvider (development mode).")
        return _make_mock()

    # Unknown provider — warn and fall back safely
    logger.warning(
        f"[AIFactory] Unknown AI_PROVIDER='{provider_name}'. "
        "Falling back to MockSafetyExtractionProvider."
    )
    return _make_mock()


def _make_mock() -> MockSafetyExtractionProvider:
    return MockSafetyExtractionProvider()
