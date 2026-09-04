"""
Mock AI Providers for Local Testing and Offline Development

IMPORTANT:
- MockSafetyExtractionProvider is a DETERMINISTIC DEMO provider only.
- Results are keyword-heuristic based, NOT real AI predictions.
- All results carry is_mock=True and provider_name="mock".
- Use only for development/testing/demo when no real AI key is configured.
"""

from typing import Dict, Any, List, Optional
from .base import SafetyExtractionProvider, EmbeddingProvider, SIFReasoningProvider
from app.schemas.safety_extraction import SafetyFactsExtractionResponse, FactField
from app.schemas.enums import EvidenceStatus, EnergySource, BarrierCondition


class MockSafetyExtractionProvider(SafetyExtractionProvider):
    """
    Deterministic mock provider for Safety Extraction.

    Produces structured FactField output with keyword-heuristic matching.
    Every result has is_mock=True so it is never confused with real AI output.
    """

    PROVIDER_NAME = "mock"
    MODEL_NAME = "mock-heuristic-v3"
    ANALYSIS_VERSION = "3.0.0"

    async def extract_safety_facts(
        self,
        narrative: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SafetyFactsExtractionResponse:
        text = narrative.lower()
        ctx = context or {}

        # ── ACTIVITY ─────────────────────────────────────────────────────────
        activity_value, activity_ev, activity_status, activity_conf = self._extract_activity(text, narrative)

        # ── EQUIPMENT ────────────────────────────────────────────────────────
        equipment_value, equipment_ev, equipment_status, equipment_conf = self._extract_equipment(text, narrative)

        # ── HAZARD ───────────────────────────────────────────────────────────
        hazard_value, hazard_ev, hazard_status, hazard_conf = self._extract_hazard(text, narrative)

        # ── ENERGY SOURCE ────────────────────────────────────────────────────
        energy_value, energy_ev, energy_status, energy_conf = self._extract_energy(text, narrative)

        # ── EXPOSURE ─────────────────────────────────────────────────────────
        exposure_value, exposure_ev, exposure_status, exposure_conf = self._extract_exposure(text, narrative)

        # ── EXPOSURE LOCATION ────────────────────────────────────────────────
        loc_value, loc_ev, loc_status, loc_conf = self._extract_exposure_location(text, narrative)

        # ── BARRIER ──────────────────────────────────────────────────────────
        barrier_value, barrier_ev, barrier_status, barrier_conf = self._extract_barrier(text, narrative)

        # ── BARRIER CONDITION ────────────────────────────────────────────────
        bc_value, bc_ev, bc_status, bc_conf = self._extract_barrier_condition(text, narrative)

        # ── POTENTIAL CONSEQUENCE ────────────────────────────────────────────
        pc_value, pc_ev, pc_status, pc_conf = self._extract_consequence(text, narrative)

        # ── HUMAN OVERRIDE LOGIC (For Demo Purposes) ─────────────────────────
        human_decision = str(ctx.get("human_decision", "")).upper()
        human_feedback = str(ctx.get("human_feedback", "")).lower()

        if "OVERRIDE" in human_decision:
            if "not critical" in human_feedback or "low" in human_feedback or "safe" in human_feedback:
                hazard_value = "Routine/Low-Risk Task (Human Overridden)"
                pc_value = "Minor first aid or no injury"
                bc_value = BarrierCondition.INTACT
                energy_value = None
                exposure_value = "none"
                loc_value = "none"
            elif "critical" in human_feedback or "high" in human_feedback or "fatal" in human_feedback:
                hazard_value = "Critical Life-Threatening Hazard (Human Overridden)"
                pc_value = "Fatality or severe permanent disability"
                bc_value = BarrierCondition.FAILED
                exposure_value = "Personnel directly in line of fire"
                loc_value = "Direct trajectory"

        def _make_fact(value, evidence, status, conf):
            start, end = self._find_offsets(narrative, evidence)
            return FactField(
                value=value,
                evidence=evidence,
                evidence_status=status,
                confidence=conf,
                start_offset=start,
                end_offset=end,
            )

        return SafetyFactsExtractionResponse(
            activity=_make_fact(activity_value, activity_ev, activity_status, activity_conf),
            equipment=_make_fact(equipment_value, equipment_ev, equipment_status, equipment_conf),
            hazard=_make_fact(hazard_value, hazard_ev, hazard_status, hazard_conf),
            energy_source=_make_fact(energy_value, energy_ev, energy_status, energy_conf),
            exposure=_make_fact(exposure_value, exposure_ev, exposure_status, exposure_conf),
            exposure_location=_make_fact(loc_value, loc_ev, loc_status, loc_conf),
            barrier=_make_fact(barrier_value, barrier_ev, barrier_status, barrier_conf),
            barrier_condition=_make_fact(bc_value, bc_ev, bc_status, bc_conf),
            potential_consequence=_make_fact(pc_value, pc_ev, pc_status, pc_conf),
            is_mock=True,
            extraction_notes="[DEMO] Mock heuristic extraction — not a real AI prediction. Configure AI_PROVIDER=openai for production use.",
        )

    # ── keyword extraction helpers ─────────────────────────────────────────

    def _extract_activity(self, text, narrative):
        if any(k in text for k in ("removing pin", "remove pin")):
            return ("Pin removal from structural assembly", "removing pin from", EvidenceStatus.EXPLICIT, 0.90)
        if "lifting" in text or "sling" in text or "rigging" in text:
            return ("Lifting / rigging operation", "lifting" if "lifting" in text else "rigging", EvidenceStatus.EXPLICIT, 0.85)
        if "welding" in text:
            return ("Welding operation", "welding", EvidenceStatus.EXPLICIT, 0.88)
        if "drilling" in text:
            return ("Drilling operation", "drilling", EvidenceStatus.EXPLICIT, 0.87)
        if "testing" in text and "line" in text:
            return ("Line pressure testing", "line testing", EvidenceStatus.EXPLICIT, 0.85)
        if "inspection" in text:
            return ("Safety inspection", "inspection", EvidenceStatus.INFERRED, 0.60)
        if "maintenance" in text:
            return ("Maintenance activity", "maintenance", EvidenceStatus.EXPLICIT, 0.75)
        if "housekeeping" in text:
            return ("Housekeeping / area cleaning", "housekeeping", EvidenceStatus.EXPLICIT, 0.80)
        return ("General Operations (Mock)", None, EvidenceStatus.INFERRED, 0.40)

    def _extract_equipment(self, text, narrative):
        if "pin" in text and ("structure" in text or "shackle" in text):
            return ("Structural pin / shackle assembly", None, EvidenceStatus.INFERRED, 0.75)
        if "hammer" in text:
            return ("Hammer", "hammer", EvidenceStatus.EXPLICIT, 0.90)
        if "hydraulic" in text and "hose" in text:
            return ("Hydraulic hose", "hydraulic hose", EvidenceStatus.EXPLICIT, 0.92)
        if "wire" in text or "cable" in text:
            return ("Wire / cable", "wire" if "wire" in text else "cable", EvidenceStatus.EXPLICIT, 0.85)
        if "scaffold" in text:
            return ("Scaffolding", "scaffold", EvidenceStatus.EXPLICIT, 0.88)
        if "eyewash" in text:
            return ("Eyewash station", "eyewash", EvidenceStatus.EXPLICIT, 0.92)
        if "crane" in text:
            return ("Crane", "crane", EvidenceStatus.EXPLICIT, 0.90)
        return ("Standard Tools / Equipment (Mock)", None, EvidenceStatus.INFERRED, 0.40)

    def _extract_hazard(self, text, narrative):
        if "pin" in text and ("speed" in text or "came out" in text or "ejected" in text):
            return ("Pin ejection — projectile hazard from stored kinetic/mechanical energy release",
                    "came out at speed" if "came out at speed" in text else "speed", EvidenceStatus.EXPLICIT, 0.92)
        if "struck" in text or "struck by" in text:
            return ("Struck-by — unexpected movement of object", "struck", EvidenceStatus.EXPLICIT, 0.85)
        if "fall" in text and "height" in text:
            return ("Fall from height", "fall from height", EvidenceStatus.EXPLICIT, 0.90)
        if "hydraulic" in text and ("leak" in text or "burst" in text or "hose" in text):
            return ("High-pressure hydraulic fluid release / loss of containment", "hydraulic", EvidenceStatus.EXPLICIT, 0.88)
        if "wire" in text and ("lay" in text or "trip" in text or "across" in text):
            return ("Tripping hazard — improperly positioned cable/wire", "wire", EvidenceStatus.EXPLICIT, 0.82)
        if "hammer" in text and "slip" in text:
            return ("Struck-by hazard from slipping striking tool", "hammer" if "hammer" in text else None, EvidenceStatus.EXPLICIT, 0.87)
        if "electrical" in text or "electric" in text:
            return ("Electrical contact hazard", "electrical" if "electrical" in text else "electric", EvidenceStatus.EXPLICIT, 0.88)
        if "eyewash" in text and ("blocked" in text or "not working" in text or "inoperative" in text or "missing" in text):
            return ("Compromised emergency eyewash provision — barrier failure", "eyewash", EvidenceStatus.INFERRED, 0.72)
        return ("Unrecognized Hazard (Mock)", None, EvidenceStatus.INFERRED, 0.40)

    def _extract_energy(self, text, narrative):
        if "speed" in text or "ejected" in text or "came out" in text or "kinetic" in text:
            return (EnergySource.KINETIC, "came out at speed" if "came out at speed" in text else "speed", EvidenceStatus.EXPLICIT, 0.85)
        if "hammered" in text or "struck" in text or "hit" in text:
            return (EnergySource.MECHANICAL, "hammer" if "hammer" in text else None, EvidenceStatus.INFERRED, 0.75)
        if "hydraulic" in text:
            return (EnergySource.PRESSURE, "hydraulic", EvidenceStatus.EXPLICIT, 0.88)
        if "height" in text or "fall" in text or "drop" in text:
            return (EnergySource.GRAVITATIONAL, "height" if "height" in text else "fall", EvidenceStatus.EXPLICIT, 0.85)
        if "electrical" in text or "electric" in text or "voltage" in text:
            return (EnergySource.ELECTRICAL, "electrical" if "electrical" in text else "electric", EvidenceStatus.EXPLICIT, 0.90)
        if "chemical" in text or "acid" in text or "caustic" in text:
            return (EnergySource.CHEMICAL, "chemical" if "chemical" in text else None, EvidenceStatus.INFERRED, 0.70)
        if "hot" in text or "heat" in text or "steam" in text or "burn" in text:
            return (EnergySource.THERMAL, "hot" if "hot" in text else "heat", EvidenceStatus.INFERRED, 0.68)
        return (EnergySource.UNKNOWN, None, EvidenceStatus.UNKNOWN, 0.0)

    def _extract_exposure(self, text, narrative):
        if "rigman" in text or "rigger" in text:
            return ("Rigman in trajectory of ejected object",
                    "rigman" if "rigman" in text else "rigger", EvidenceStatus.EXPLICIT, 0.90)
        if "worker" in text or "employee" in text:
            return ("Worker exposed to hazardous energy",
                    "worker" if "worker" in text else "employee", EvidenceStatus.EXPLICIT, 0.80)
        if "person" in text and ("near" in text or "nearby" in text or "beneath" in text):
            return ("Person near / beneath hazard source",
                    "person nearby" if "person nearby" in text else "nearby", EvidenceStatus.EXPLICIT, 0.78)
        if "operator" in text:
            return ("Operator exposed to equipment hazard", "operator", EvidenceStatus.EXPLICIT, 0.82)
        return ("Personnel in vicinity (Mock)", None, EvidenceStatus.INFERRED, 0.40)

    def _extract_exposure_location(self, text, narrative):
        if "opposite side" in text:
            return ("Opposite side of pin trajectory", "opposite side", EvidenceStatus.EXPLICIT, 0.88)
        if "nearby" in text or "passing nearby" in text:
            return ("Near the trajectory path of ejected component",
                    "passing nearby" if "passing nearby" in text else "nearby", EvidenceStatus.EXPLICIT, 0.85)
        if "beneath" in text or "below" in text:
            return ("Beneath suspended load or dropped object hazard zone",
                    "beneath" if "beneath" in text else "below", EvidenceStatus.EXPLICIT, 0.88)
        if "near" in text:
            return ("Near the hazard source", "near", EvidenceStatus.INFERRED, 0.60)
        return ("General work area (Mock)", None, EvidenceStatus.INFERRED, 0.40)

    def _extract_barrier(self, text, narrative):
        if "exclusion" in text or "barricade" in text or "barrier" in text:
            return ("Exclusion zone / barricade", "exclusion" if "exclusion" in text else "barricade", EvidenceStatus.EXPLICIT, 0.88)
        if "guard" in text:
            return ("Physical guarding", "guard", EvidenceStatus.EXPLICIT, 0.85)
        if "permit" in text:
            return ("Work permit / work authorisation", "permit", EvidenceStatus.EXPLICIT, 0.88)
        if "ppe" in text or "helmet" in text or "goggles" in text:
            return ("Personal Protective Equipment (PPE)", "ppe" if "ppe" in text else "helmet", EvidenceStatus.EXPLICIT, 0.82)
        if "inspection" in text:
            return ("Pre-task inspection", "inspection", EvidenceStatus.INFERRED, 0.60)
        # default inferred
        return ("Safe positioning / line-of-fire avoidance", None, EvidenceStatus.INFERRED, 0.45)

    def _extract_barrier_condition(self, text, narrative):
        if any(k in text for k in ("came out", "ejected", "slipped", "fell", "failed", "burst", "leaked")):
            return (BarrierCondition.FAILED, None, EvidenceStatus.INFERRED, 0.78)
        if any(k in text for k in ("blocked", "not working", "inoperative", "broken", "damaged", "missing")):
            return (BarrierCondition.ABSENT, None, EvidenceStatus.INFERRED, 0.72)
        if any(k in text for k in ("degraded", "worn", "reduced", "partial")):
            return (BarrierCondition.DEGRADED, None, EvidenceStatus.INFERRED, 0.70)
        if any(k in text for k in ("guard in place", "excluded", "permit in place")):
            return (BarrierCondition.INTACT, None, EvidenceStatus.INFERRED, 0.60)
        return (BarrierCondition.UNKNOWN, None, EvidenceStatus.UNKNOWN, 0.0)

    def _extract_consequence(self, text, narrative):
        if "speed" in text or "ejected" in text or "trajectory" in text:
            return ("Struck-by injury from high-velocity projectile — potentially fatal or serious bodily injury",
                    None, EvidenceStatus.INFERRED, 0.82)
        if "fall" in text and "height" in text:
            return ("Serious or fatal injury from fall from height", "fall from height", EvidenceStatus.INFERRED, 0.85)
        if "hydraulic" in text and ("hose" in text or "leak" in text):
            return ("High-pressure fluid injection injury or chemical burns", None, EvidenceStatus.INFERRED, 0.80)
        if "electric" in text:
            return ("Electrocution or electrical burn injury", None, EvidenceStatus.INFERRED, 0.85)
        if "wire" in text and "trip" in text:
            return ("Trip and fall injury — potential serious injury", None, EvidenceStatus.INFERRED, 0.65)
        if "hammer" in text and "slip" in text:
            return ("Struck-by injury from slipping striking tool", None, EvidenceStatus.INFERRED, 0.72)
        return ("Possible minor injury/incident (Mock)", None, EvidenceStatus.INFERRED, 0.40)

    @staticmethod
    def _find_offsets(narrative: str, evidence: Optional[str]):
        """Safely find start/end character offsets of evidence in narrative."""
        if not evidence or not narrative:
            return None, None
        idx = narrative.lower().find(evidence.lower())
        if idx == -1:
            return None, None
        return idx, idx + len(evidence)

    async def generate_suggested_actions(
        self,
        narrative: str,
        hazard: str,
        barrier_condition: str,
        life_saving_rule: str,
        previous_actions: str = "",
    ) -> tuple[List[str], str]:
        import asyncio
        text = narrative.lower()
        actions = []
        
        # Personalized based on text
        if "fire" in text or "hot work" in text or "burn" in text:
            actions.append(f"Inspect all fire extinguishers and hot work permits in the {hazard or 'affected'} zone.")
            actions.append("Ensure a dedicated fire watch is maintained for 30 minutes after operations.")
        elif "fall" in text or "height" in text or "scaffold" in text:
            actions.append("Conduct an immediate audit of all fall arrest systems and harness lanyards.")
            actions.append("Re-certify scaffolding tags and ensure toe boards are secure.")
        elif "lift" in text or "crane" in text or "dropped" in text:
            actions.append("Re-establish the lifting exclusion zone with physical barricades.")
            actions.append("Inspect all rigging equipment (slings, shackles) for wear and tear.")
        elif "pressure" in text or "leak" in text or "hose" in text:
            actions.append("Depressurize lines and conduct a visual sweep for fluid leaks.")
            actions.append("Verify LOTO (Lock-Out Tag-Out) is applied to all active valves.")
        else:
            actions.append(f"Verify the {str(barrier_condition).lower() if barrier_condition else 'safety'} controls for {hazard or 'this task'}.")
            actions.append(f"Review the {life_saving_rule or 'relevant'} documentation.")
            actions.append("Inspect the affected work area.")
            
        # Connect to previous actions if any exist
        if previous_actions:
            actions.append(f"Follow up on previous action: '{previous_actions}'.")
            
        # Add a generic closing action
        actions.append("Conduct a toolbox talk covering these specific risks before resuming work.")
        
        reasoning = f"Based on the detected hazard ({hazard}), barrier condition ({barrier_condition}), and the narrative context, these specific actions align with {life_saving_rule or 'standard safety protocols'}."
        await asyncio.sleep(0.5)
        return actions, reasoning


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock provider returning 1536-dimensional dummy vector embeddings."""

    async def generate_embedding(self, text: str) -> List[float]:
        length = len(text)
        return [(i % 100) / 100.0 * (1 if (i + length) % 2 == 0 else -1) for i in range(1536)]

    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [await self.generate_embedding(t) for t in texts]


class MockSIFReasoningProvider(SIFReasoningProvider):
    """
    Mock provider for SIF screening evaluation.
    NOTE: SIF classification belongs to Phase 4+. This provider is a stub.
    """

    async def evaluate_sif_potential(self, safety_facts: Dict[str, Any]) -> Dict[str, Any]:
        # Simple heuristic to spread out SIF potential deterministically
        fact_str = str(safety_facts)
        score = sum(ord(c) for c in fact_str) % 3
        
        if score == 0:
            status = "YES"
        elif score == 1:
            status = "NO"
        else:
            status = "UNCERTAIN"
            
        return {
            "sif_fpi_potential": status,
            "sif_confidence": 0.85,
            "evidence_status": "EXPLICIT",
            "note": "Deterministically assigned mock value to balance data spread.",
        }
