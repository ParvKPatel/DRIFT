"""
OpenAI Safety Extraction Provider for DRIFT

Uses the OpenAI Chat Completions API with JSON response mode to extract
structured safety facts from safety narratives.

Environment variables required:
    AI_API_KEY — OpenAI API key (sk-...)
    AI_MODEL   — Model to use (default: gpt-4o)

The provider will NOT function without a valid API key.
The factory falls back to MockSafetyExtractionProvider if key is absent.
"""

import json
import httpx
from typing import Dict, Any, Optional

from .base import SafetyExtractionProvider
from ai.prompts.extraction_prompt import SYSTEM_PROMPT, build_user_prompt
from app.schemas.safety_extraction import SafetyFactsExtractionResponse, FactField
from app.schemas.enums import EvidenceStatus, EnergySource, BarrierCondition
from app.utils.logging import logger

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
MAX_NARRATIVE_CHARS = 8000  # Truncate very long narratives to avoid token overflow


class OpenAISafetyExtractionProvider(SafetyExtractionProvider):
    """
    OpenAI GPT-based safety fact extraction provider.
    Returns structured SafetyFactsExtractionResponse from GPT JSON mode.
    Never calls SIF/FPI scoring or risk prioritisation — that is Phase 4+.
    """

    PROVIDER_NAME = "openai"
    ANALYSIS_VERSION = "3.0.0"

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.MODEL_NAME = model

    async def extract_safety_facts(
        self,
        narrative: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SafetyFactsExtractionResponse:
        ctx = context or {}
        report_id = ctx.get("report_id", "UNKNOWN")

        # Truncate if necessary to avoid token overflow
        truncated = narrative[:MAX_NARRATIVE_CHARS]
        if len(narrative) > MAX_NARRATIVE_CHARS:
            logger.warning(
                f"[OpenAIProvider] Narrative truncated from {len(narrative)} to "
                f"{MAX_NARRATIVE_CHARS} chars for report {report_id}"
            )

        user_prompt = build_user_prompt(
            report_id=report_id,
            narrative=truncated,
            incident_cause=ctx.get("incident_cause", ""),
            fixed_short_description=ctx.get("fixed_short_description", ""),
            corrective_action=ctx.get("corrective_action", ""),
        )

        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,  # Low temperature for deterministic structured extraction
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(
            f"[OpenAIProvider] Starting extraction for report={report_id} model={self.model}"
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(OPENAI_CHAT_URL, json=payload, headers=headers)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"[OpenAIProvider] HTTP error for report={report_id}: "
                f"{exc.response.status_code} — {exc.response.text[:200]}"
            )
            raise RuntimeError(
                f"OpenAI API HTTP error {exc.response.status_code} for report {report_id}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"[OpenAIProvider] Network error for report={report_id}: {exc}")
            raise RuntimeError(f"OpenAI API network error for report {report_id}") from exc

        data = response.json()

        # Extract content from response
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            logger.error(f"[OpenAIProvider] Unexpected response shape for report={report_id}: {data}")
            raise RuntimeError(f"Unexpected OpenAI response structure for report {report_id}") from exc

        # Parse JSON
        try:
            raw = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error(
                f"[OpenAIProvider] JSON decode error for report={report_id}: "
                f"{exc} — content[:200]={content[:200]}"
            )
            raise RuntimeError(
                f"OpenAI returned invalid JSON for report {report_id}"
            ) from exc

        # Validate & construct the response
        return self._parse_and_validate(raw, report_id)

    def _parse_and_validate(
        self, raw: Dict[str, Any], report_id: str
    ) -> SafetyFactsExtractionResponse:
        """
        Parse raw dict from model into SafetyFactsExtractionResponse.
        Handles missing fields gracefully — defaults to UNKNOWN rather than crashing.
        """
        FACT_FIELDS = [
            "activity", "equipment", "hazard", "energy_source",
            "exposure", "exposure_location", "barrier",
            "barrier_condition", "potential_consequence",
        ]
        ENUM_FIELDS = {
            "energy_source": EnergySource,
            "barrier_condition": BarrierCondition,
        }

        fact_kwargs: Dict[str, FactField] = {}

        for field_name in FACT_FIELDS:
            field_data = raw.get(field_name)
            if not isinstance(field_data, dict):
                logger.warning(
                    f"[OpenAIProvider] Field '{field_name}' missing or invalid "
                    f"for report={report_id}, defaulting to UNKNOWN"
                )
                fact_kwargs[field_name] = FactField(
                    value=None,
                    evidence=None,
                    evidence_status=EvidenceStatus.UNKNOWN,
                    confidence=0.0,
                    start_offset=None,
                    end_offset=None,
                )
                continue

            # Validate and coerce enum fields
            value = field_data.get("value")
            if value is not None and field_name in ENUM_FIELDS:
                enum_cls = ENUM_FIELDS[field_name]
                try:
                    value = enum_cls(str(value).upper())
                except ValueError:
                    logger.warning(
                        f"[OpenAIProvider] Invalid {field_name} enum value '{value}' "
                        f"for report={report_id}, defaulting to UNKNOWN"
                    )
                    value = None

            # Validate evidence_status
            raw_status = field_data.get("evidence_status", "UNKNOWN")
            try:
                status = EvidenceStatus(str(raw_status).upper())
            except ValueError:
                status = EvidenceStatus.UNKNOWN

            # Validate confidence
            raw_conf = field_data.get("confidence", 0.0)
            try:
                confidence = max(0.0, min(1.0, float(raw_conf)))
            except (TypeError, ValueError):
                confidence = 0.0

            # Validate offsets
            start_offset = field_data.get("start_offset")
            end_offset = field_data.get("end_offset")
            if not isinstance(start_offset, int):
                start_offset = None
            if not isinstance(end_offset, int):
                end_offset = None

            # Validate evidence text length
            evidence = field_data.get("evidence")
            if evidence is not None and len(str(evidence)) > 500:
                evidence = str(evidence)[:500]

            # Validate value length
            if value is not None and isinstance(value, str) and len(value) > 500:
                value = value[:500]

            fact_kwargs[field_name] = FactField(
                value=value,
                evidence=evidence,
                evidence_status=status,
                confidence=confidence,
                start_offset=start_offset,
                end_offset=end_offset,
            )

        is_mock = bool(raw.get("is_mock", False))
        extraction_notes = raw.get("extraction_notes")
        if extraction_notes and len(str(extraction_notes)) > 1000:
            extraction_notes = str(extraction_notes)[:1000]

        logger.info(
            f"[OpenAIProvider] Extraction completed for report={report_id}"
        )
        return SafetyFactsExtractionResponse(**fact_kwargs, is_mock=is_mock, extraction_notes=extraction_notes)

    async def generate_suggested_actions(
        self,
        narrative: str,
        hazard: str,
        barrier_condition: str,
        life_saving_rule: str,
        previous_actions: str = "",
    ) -> tuple[list[str], str]:
        prompt = (
            "You are an expert HSE professional advising a safety officer. "
            "Your task is to 'connect the dots' by reviewing the incident details and any previously taken actions, "
            "and then suggest what further steps or long-term controls the human officer should consider implementing.\n\n"
            f"Narrative: {narrative}\n"
            f"Hazard: {hazard}\n"
            f"Barrier Condition: {barrier_condition}\n"
            f"Life-Saving Rule: {life_saving_rule}\n"
            f"Previously Taken Actions: {previous_actions or 'None stated'}\n\n"
            "Guidelines:\n"
            "- Acknowledge the previously taken actions (if any) and suggest how to build upon them or address root causes.\n"
            "- Tone must be advisory: these are SUGGESTIONS for the human officer. The human retains final authority.\n"
            "- Provide 3 to 5 specific, actionable, evidence-based recommendations.\n"
            "- Return a JSON object strictly matching this schema:\n"
            '{\n  "actions": ["action 1", "action 2", "action 3"],\n  "reasoning": "Explanation for how these suggestions connect to the past actions and address the root cause"\n}'
        )

        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "You are a helpful safety assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(OPENAI_CHAT_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                result = json.loads(content)
                actions = result.get("actions", [])
                reasoning = result.get("reasoning", "")
                
                # Enforce limit of 5 actions max
                if isinstance(actions, list):
                    actions = actions[:5]
                else:
                    actions = []
                return actions, reasoning
        except Exception as exc:
            logger.error(f"[OpenAIProvider] Action generation failed: {exc}")
            return [], ""
