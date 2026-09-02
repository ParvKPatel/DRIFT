"""
Phase 5 — OIL SENTINEL Life-Saving Rule (LSR) Engine

Evaluates Phase 3 Safety Facts and verbatim report narrative to map
incidents to the 9 official OIL SENTINEL Life-Saving Rules:

1. Bypassing Safety Controls
2. Confined Space
3. Driving
4. Energy Isolation
5. Hot Work
6. Line of Fire
7. Safe Mechanical Lifting
8. Work Authorisation
9. Working at Height

CRITICAL DESIGN RULES:
- Strictly respects evidence discipline: EXPLICIT / INFERRED / UNKNOWN.
- Supports primary_life_saving_rule + optional secondary_life_saving_rules.
- Does NOT overwrite original source incident_cause (source preservation).
- Evaluates safety facts and narrative — does NOT rely solely on raw category labels.
- Runs 100% locally without external API dependencies.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

from app.schemas.enums import LifeSavingRule, EvidenceStatus, EnergySource, BarrierCondition
from app.schemas.lsr_mapping import LsrMappingResult
from app.utils.logging import logger


@dataclass
class LsrCandidate:
    rule: LifeSavingRule
    confidence: float
    evidence: Optional[str]
    evidence_status: EvidenceStatus
    reason: str


class LsrEngine:
    """Deterministic & evidence-backed Life-Saving Rule Mapping Engine."""

    MAPPING_VERSION = "lsr-engine-v1"

    def map_rules(
        self,
        report_id: str,
        facts: Dict[str, Any],
        narrative: str,
    ) -> LsrMappingResult:
        """
        Maps report to primary and optional secondary Life-Saving Rules.
        """
        narrative_lower = narrative.lower()

        candidates: List[LsrCandidate] = []

        # ── 1. BYPASSING SAFETY CONTROLS ─────────────────────────────────────
        cand_bypass = self._eval_bypassing_safety_controls(facts, narrative_lower)
        if cand_bypass:
            candidates.append(cand_bypass)

        # ── 2. CONFINED SPACE ────────────────────────────────────────────────
        cand_confined = self._eval_confined_space(facts, narrative_lower)
        if cand_confined:
            candidates.append(cand_confined)

        # ── 3. DRIVING ───────────────────────────────────────────────────────
        cand_driving = self._eval_driving(facts, narrative_lower)
        if cand_driving:
            candidates.append(cand_driving)

        # ── 4. ENERGY ISOLATION ──────────────────────────────────────────────
        cand_iso = self._eval_energy_isolation(facts, narrative_lower)
        if cand_iso:
            candidates.append(cand_iso)

        # ── 5. HOT WORK ──────────────────────────────────────────────────────
        cand_hot = self._eval_hot_work(facts, narrative_lower)
        if cand_hot:
            candidates.append(cand_hot)

        # ── 6. LINE OF FIRE ──────────────────────────────────────────────────
        cand_lof = self._eval_line_of_fire(facts, narrative_lower)
        if cand_lof:
            candidates.append(cand_lof)

        # ── 7. SAFE MECHANICAL LIFTING ───────────────────────────────────────
        cand_lift = self._eval_safe_mechanical_lifting(facts, narrative_lower)
        if cand_lift:
            candidates.append(cand_lift)

        # ── 8. WORK AUTHORISATION ────────────────────────────────────────────
        cand_auth = self._eval_work_authorisation(facts, narrative_lower)
        if cand_auth:
            candidates.append(cand_auth)

        # ── 9. WORKING AT HEIGHT ─────────────────────────────────────────────
        cand_height = self._eval_working_at_height(facts, narrative_lower)
        if cand_height:
            candidates.append(cand_height)

        # Sort candidates by confidence desc
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        if not candidates:
            return LsrMappingResult(
                report_id=report_id,
                primary_life_saving_rule=LifeSavingRule.UNKNOWN,
                secondary_life_saving_rules=[],
                lsr_confidence=0.0,
                lsr_evidence=None,
                lsr_evidence_status=EvidenceStatus.UNKNOWN,
                lsr_reason="No Life-Saving Rule relationship identified in available report evidence.",
                lsr_mapping_version=self.MAPPING_VERSION,
                mapped_at=datetime.now(timezone.utc),
            )

        primary = candidates[0]
        secondaries: List[LifeSavingRule] = []
        for c in candidates[1:]:
            if c.rule != primary.rule and c.confidence >= 0.65:
                secondaries.append(c.rule)

        return LsrMappingResult(
            report_id=report_id,
            primary_life_saving_rule=primary.rule,
            secondary_life_saving_rules=secondaries,
            lsr_confidence=primary.confidence,
            lsr_evidence=primary.evidence,
            lsr_evidence_status=primary.evidence_status,
            lsr_reason=primary.reason,
            lsr_mapping_version=self.MAPPING_VERSION,
            mapped_at=datetime.now(timezone.utc),
        )

    # ── Rule Evaluators ─────────────────────────────────────────────────────

    def _eval_bypassing_safety_controls(self, facts: Dict[str, Any], text: str) -> Optional[LsrCandidate]:
        barrier = (facts.get("barrier") or "").lower()
        bc = facts.get("barrier_condition")

        if any(k in text or k in barrier for k in ("bypass", "interlock defeat", "guard removed", "override safety", "tamper", "bypassed")):
            status = EvidenceStatus.EXPLICIT if "bypass" in text else EvidenceStatus.INFERRED
            ev = self._find_evidence(text, ["bypass", "guard", "interlock", "override"])
            return LsrCandidate(
                rule=LifeSavingRule.BYPASSING_SAFETY_CONTROLS,
                confidence=0.90,
                evidence=ev,
                evidence_status=status,
                reason="Safety control or interlock was bypassed, defeated, or removed without authorization.",
            )
        return None

    def _eval_confined_space(self, facts: Dict[str, Any], text: str) -> Optional[LsrCandidate]:
        activity = (facts.get("activity") or "").lower()
        loc = (facts.get("exposure_location") or "").lower()

        if any(k in text or k in activity or k in loc for k in ("confined space", "vessel entry", "storage tank entry", "sewer pit", "manhole", "inside tank", "enclosed space entry")):
            status = EvidenceStatus.EXPLICIT if "confined space" in text or "vessel entry" in text else EvidenceStatus.INFERRED
            ev = self._find_evidence(text, ["confined space", "vessel", "tank", "pit", "manhole", "entry"])
            return LsrCandidate(
                rule=LifeSavingRule.CONFINED_SPACE,
                confidence=0.92,
                evidence=ev,
                evidence_status=status,
                reason="Entry or work performed inside a confined or enclosed space.",
            )
        return None

    def _eval_driving(self, facts: Dict[str, Any], text: str) -> Optional[LsrCandidate]:
        equipment = (facts.get("equipment") or "").lower()
        energy = facts.get("energy_source")

        if energy == EnergySource.VEHICLE_MOTION or any(k in text or k in equipment for k in ("vehicle", "driving", "driver", "truck", "pickup", "forklift", "transportation", "seatbelt")):
            status = EvidenceStatus.EXPLICIT if any(k in text for k in ("driving", "vehicle", "truck", "driver")) else EvidenceStatus.INFERRED
            ev = self._find_evidence(text, ["vehicle", "driving", "truck", "driver", "forklift"])
            return LsrCandidate(
                rule=LifeSavingRule.DRIVING,
                confidence=0.88,
                evidence=ev,
                evidence_status=status,
                reason="Hazard associated with vehicle operation, driving, or mobile equipment movement.",
            )
        return None

    def _eval_energy_isolation(self, facts: Dict[str, Any], text: str) -> Optional[LsrCandidate]:
        energy = facts.get("energy_source")
        hazard = (facts.get("hazard") or "").lower()
        barrier = (facts.get("barrier") or "").lower()

        if any(k in text or k in hazard or k in barrier for k in ("loto", "isolation", "lockout", "tagout", "de-energize", "zero energy", "opening pressurized", "breaking containment", "energized line")):
            has_explicit = any(k in text or k in barrier for k in ("loto", "isolation", "lockout", "tagout", "de-energize", "zero energy"))
            status = EvidenceStatus.EXPLICIT if has_explicit else EvidenceStatus.INFERRED
            conf = 0.96 if has_explicit else 0.88
            ev = self._find_evidence(text, ["loto", "isolation", "lockout", "pressure", "energized", "de-energize"])
            return LsrCandidate(
                rule=LifeSavingRule.ENERGY_ISOLATION,
                confidence=conf,
                evidence=ev,
                evidence_status=status,
                reason="Hazard associated with hazardous energy isolation or Lockout/Tagout (LOTO) controls.",
            )
        return None

    def _eval_hot_work(self, facts: Dict[str, Any], text: str) -> Optional[LsrCandidate]:
        activity = (facts.get("activity") or "").lower()

        if any(k in text or k in activity for k in ("welding", "cutting", "grinding", "hot work", "torch", "spark", "ignition source")):
            status = EvidenceStatus.EXPLICIT if any(k in text for k in ("welding", "hot work", "grinding", "cutting")) else EvidenceStatus.INFERRED
            ev = self._find_evidence(text, ["welding", "hot work", "grinding", "cutting", "torch"])
            return LsrCandidate(
                rule=LifeSavingRule.HOT_WORK,
                confidence=0.94,
                evidence=ev,
                evidence_status=status,
                reason="Activity involving open flames, sparks, welding, grinding, or ignition sources.",
            )
        return None

    def _eval_line_of_fire(self, facts: Dict[str, Any], text: str) -> Optional[LsrCandidate]:
        exposure = (facts.get("exposure") or "").lower()
        loc = (facts.get("exposure_location") or "").lower()
        hazard = (facts.get("hazard") or "").lower()
        energy = facts.get("energy_source")

        has_explicit_lof = any(k in text or k in exposure or k in loc or k in hazard for k in (
            "trajectory", "line of fire", "struck by", "opposite side", "falling object",
            "dropped object", "ejected", "pin came out", "hammer slipped", "whiplash", "pinch point"
        ))

        is_line_of_fire = (
            has_explicit_lof or
            energy in (EnergySource.KINETIC, EnergySource.PRESSURE, EnergySource.GRAVITATIONAL)
        )

        has_exposed_person = any(k in exposure or k in loc or k in text for k in ("rigger", "rigman", "worker", "technician", "operator", "person", "employee", "nearby"))

        if is_line_of_fire and has_exposed_person:
            status = EvidenceStatus.EXPLICIT if has_explicit_lof else EvidenceStatus.INFERRED
            conf = 0.95 if has_explicit_lof else 0.82
            ev = self._find_evidence(text, ["trajectory", "line of fire", "nearby", "opposite side", "rigman", "rigger", "worker", "struck"])
            return LsrCandidate(
                rule=LifeSavingRule.LINE_OF_FIRE,
                confidence=conf,
                evidence=ev,
                evidence_status=status,
                reason="Personnel positioned in line of fire of ejected component, falling object, or hazardous trajectory.",
            )
        return None

    def _eval_safe_mechanical_lifting(self, facts: Dict[str, Any], text: str) -> Optional[LsrCandidate]:
        activity = (facts.get("activity") or "").lower()
        equipment = (facts.get("equipment") or "").lower()

        if any(k in text or k in activity or k in equipment for k in ("crane", "rigging", "sling", "hoist", "suspended load", "lifting", "shackle", "derrick", "winch")):
            status = EvidenceStatus.EXPLICIT if any(k in text for k in ("crane", "lifting", "rigging", "shackle", "sling")) else EvidenceStatus.INFERRED
            ev = self._find_evidence(text, ["crane", "lifting", "rigging", "shackle", "sling", "suspended load"])
            return LsrCandidate(
                rule=LifeSavingRule.SAFE_MECHANICAL_LIFTING,
                confidence=0.92,
                evidence=ev,
                evidence_status=status,
                reason="Hazard associated with mechanical lifting, crane operation, or rigging assembly.",
            )
        return None

    def _eval_work_authorisation(self, facts: Dict[str, Any], text: str) -> Optional[LsrCandidate]:
        barrier = (facts.get("barrier") or "").lower()

        if any(k in text or k in barrier for k in ("permit to work", "ptw", "work permit", "work authorisation", "unauthorized work", "job safety analysis", "jsa", "permit")):
            status = EvidenceStatus.EXPLICIT if any(k in text for k in ("permit", "ptw", "authorisation")) else EvidenceStatus.INFERRED
            ev = self._find_evidence(text, ["permit", "ptw", "authorisation", "jsa"])
            return LsrCandidate(
                rule=LifeSavingRule.WORK_AUTHORISATION,
                confidence=0.88,
                evidence=ev,
                evidence_status=status,
                reason="Activity requiring formal Permit to Work (PTW) or work authorization control.",
            )
        return None

    def _eval_working_at_height(self, facts: Dict[str, Any], text: str) -> Optional[LsrCandidate]:
        hazard = (facts.get("hazard") or "").lower()
        activity = (facts.get("activity") or "").lower()
        equipment = (facts.get("equipment") or "").lower()

        if any(k in text or k in hazard or k in activity or k in equipment for k in ("scaffold", "working at height", "fall from height", "harness", "elevated platform", "roof opening", "ladder", "edge protection")):
            status = EvidenceStatus.EXPLICIT if any(k in text for k in ("scaffold", "height", "fall from height", "harness")) else EvidenceStatus.INFERRED
            ev = self._find_evidence(text, ["scaffold", "height", "fall", "harness", "elevated"])
            return LsrCandidate(
                rule=LifeSavingRule.WORKING_AT_HEIGHT,
                confidence=0.92,
                evidence=ev,
                evidence_status=status,
                reason="Work performed at height, elevated platforms, or scaffolding.",
            )
        return None

    # ── Evidence Helper ─────────────────────────────────────────────────────

    @staticmethod
    def _find_evidence(text: str, keywords: List[str]) -> Optional[str]:
        """Finds matching sentence or phrase snippet containing keywords."""
        sentences = [s.strip() for s in text.replace("\n", ". ").split(".") if s.strip()]
        for sentence in sentences:
            if any(k in sentence for k in keywords):
                return sentence[:150]
        return None
