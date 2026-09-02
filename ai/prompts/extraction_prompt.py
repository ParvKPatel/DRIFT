"""
Phase 3 — Safety Fact Extraction Prompt Templates

These prompts instruct the LLM to:
1. Extract only evidence-supported safety facts
2. Distinguish EXPLICIT vs INFERRED information
3. Return UNKNOWN when evidence is insufficient
4. Never invent missing measurements or facts
5. Separate actual outcome from potential consequence
6. Identify hazardous mechanism (not just the source category label)
7. Return strict structured JSON
8. NOT determine SIF/FPI classification (that belongs to Phase 4+)
"""

SYSTEM_PROMPT = """You are an expert Oil & Gas HSE (Health, Safety, and Environment) analyst.
Your role is to extract structured safety facts from verbatim incident and near-miss narrative reports.

STRICT RULES:
1. Extract ONLY facts that are directly supported by the narrative text.
2. Distinguish between EXPLICIT information (clearly stated) and INFERRED information (reasoned from context).
3. Use evidence_status = "UNKNOWN" when the information cannot be determined from the text.
4. Never invent or hallucinate values, measurements, durations, pressure readings, distances, or isolation status.
5. The "potential_consequence" is what COULD have happened — not what actually happened. A near-miss can have actual_outcome = no injury but potential_consequence = fatal injury.
6. The "hazard" must identify the hazardous MECHANISM or CONDITION (e.g., "pin ejection under kinetic energy") — not simply copy the source category label.
7. Identify the "energy_source" based on the mechanism of harm (mechanical, kinetic, pressure, electrical, thermal, chemical, gravitational, stored_energy, vehicle_motion).
8. For barrier_condition, ONLY use: INTACT, DEGRADED, FAILED, ABSENT, or UNKNOWN.
9. Include supporting evidence quotes for each fact where possible.

CRITICAL RESTRICTION:
Do NOT determine or output:
- SIF/FPI potential (YES/NO/UNCERTAIN)
- Risk priority score
- Life-Saving Rule classification
- Probability of death or injury severity predictions
Those determinations belong to separate screening phases — they are NOT part of your task here.

OUTPUT FORMAT:
Return ONLY valid JSON. Do not include any explanatory prose outside the JSON structure.
The JSON must exactly match the schema provided in the user message."""

USER_PROMPT_TEMPLATE = """Analyze the following safety report and extract structured safety facts.

SOURCE REPORT:
Report ID: {report_id}
Source Incident Category (do NOT simply copy this into hazard field — identify the actual mechanism): {incident_cause}
Short Description: {fixed_short_description}

VERBATIM NARRATIVE:
{narrative}

{corrective_action_section}

Extract the following 9 safety facts from the VERBATIM NARRATIVE above.
For each fact, provide:
- "value": the extracted content as a string (or null if not determinable)
- "evidence": the exact supporting quote from the narrative (or null)
- "evidence_status": "EXPLICIT" | "INFERRED" | "UNKNOWN"
- "confidence": a number from 0.0 to 1.0
- "start_offset": character start index of the evidence in the narrative (or null)
- "end_offset": character end index of the evidence in the narrative (exclusive, or null)

Return exactly this JSON structure (no other keys, no prose outside JSON):

{{
  "activity": {{
    "value": null or "what task was being performed",
    "evidence": null or "verbatim quote",
    "evidence_status": "EXPLICIT" | "INFERRED" | "UNKNOWN",
    "confidence": 0.0 to 1.0,
    "start_offset": null or integer,
    "end_offset": null or integer
  }},
  "equipment": {{
    "value": null or "equipment/tool/machine/object involved",
    "evidence": null or "verbatim quote",
    "evidence_status": "EXPLICIT" | "INFERRED" | "UNKNOWN",
    "confidence": 0.0 to 1.0,
    "start_offset": null or integer,
    "end_offset": null or integer
  }},
  "hazard": {{
    "value": null or "hazardous mechanism/condition — identify the actual failure mode, not just the source category",
    "evidence": null or "verbatim quote",
    "evidence_status": "EXPLICIT" | "INFERRED" | "UNKNOWN",
    "confidence": 0.0 to 1.0,
    "start_offset": null or integer,
    "end_offset": null or integer
  }},
  "energy_source": {{
    "value": null or one of: "MECHANICAL" | "KINETIC" | "GRAVITATIONAL" | "PRESSURE" | "ELECTRICAL" | "THERMAL" | "CHEMICAL" | "HYDROCARBON" | "STORED_ENERGY" | "VEHICLE_MOTION" | "UNKNOWN",
    "evidence": null or "verbatim quote",
    "evidence_status": "EXPLICIT" | "INFERRED" | "UNKNOWN",
    "confidence": 0.0 to 1.0,
    "start_offset": null or integer,
    "end_offset": null or integer
  }},
  "exposure": {{
    "value": null or "who/what was exposed and how",
    "evidence": null or "verbatim quote",
    "evidence_status": "EXPLICIT" | "INFERRED" | "UNKNOWN",
    "confidence": 0.0 to 1.0,
    "start_offset": null or integer,
    "end_offset": null or integer
  }},
  "exposure_location": {{
    "value": null or "where the exposed person was relative to the hazard",
    "evidence": null or "verbatim quote",
    "evidence_status": "EXPLICIT" | "INFERRED" | "UNKNOWN",
    "confidence": 0.0 to 1.0,
    "start_offset": null or integer,
    "end_offset": null or integer
  }},
  "barrier": {{
    "value": null or "safety control that should prevent or mitigate this hazard",
    "evidence": null or "verbatim quote",
    "evidence_status": "EXPLICIT" | "INFERRED" | "UNKNOWN",
    "confidence": 0.0 to 1.0,
    "start_offset": null or integer,
    "end_offset": null or integer
  }},
  "barrier_condition": {{
    "value": null or one of: "INTACT" | "DEGRADED" | "FAILED" | "ABSENT" | "UNKNOWN",
    "evidence": null or "verbatim quote",
    "evidence_status": "EXPLICIT" | "INFERRED" | "UNKNOWN",
    "confidence": 0.0 to 1.0,
    "start_offset": null or integer,
    "end_offset": null or integer
  }},
  "potential_consequence": {{
    "value": null or "what COULD happen if the hazard reached the exposed person — NOT the actual outcome",
    "evidence": null or "verbatim quote",
    "evidence_status": "EXPLICIT" | "INFERRED" | "UNKNOWN",
    "confidence": 0.0 to 1.0,
    "start_offset": null or integer,
    "end_offset": null or integer
  }},
  "is_mock": false,
  "extraction_notes": null or "any notes about extraction quality"
}}

Remember: if information is not in the narrative, set value to null and evidence_status to "UNKNOWN". Do not fabricate values."""


def build_user_prompt(
    report_id: str,
    narrative: str,
    incident_cause: str = "",
    fixed_short_description: str = "",
    corrective_action: str = "",
) -> str:
    """Build the user prompt from report fields."""
    corrective_section = ""
    if corrective_action:
        corrective_section = f"\nCORRECTIVE ACTION (for context only — do not use to invent primary facts):\n{corrective_action}\n"

    return USER_PROMPT_TEMPLATE.format(
        report_id=report_id,
        narrative=narrative,
        incident_cause=incident_cause or "Not specified",
        fixed_short_description=fixed_short_description or "Not specified",
        corrective_action_section=corrective_section,
    )
