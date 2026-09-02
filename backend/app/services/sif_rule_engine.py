"""
Phase 4 — OIL SENTINEL Deterministic SIF/FPI Safety Rule Engine

HYBRID ARCHITECTURE:
Phase 3 AI Extraction → Structured Safety Facts → Deterministic Safety Rules + Signal Scoring → SIF/FPI Result

CRITICAL DESIGN PRINCIPLES:
1. LLM is NOT the final authority — deterministic safety rules can override weak AI signals.
2. NO fake "probability of death" numbers — outputs defensible YES / NO / UNCERTAIN.
3. Prioritizes safety — avoids dangerous false negatives.
4. Source-label leakage prevention — reasons from safety facts and narrative, NOT raw category labels.
5. Evidence-backed — attaches supporting evidence and rule triggers to every decision.
6. Local execution — runs deterministically without external AI API calls.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.schemas.enums import (
    SifDecision,
    EvidenceStatus,
    BarrierCondition,
    EnergySource,
    ScreeningStatus,
)
from app.schemas.sif_screening import (
    ScreeningSignals,
    RuleTrigger,
    SifScreeningResult,
)
from app.utils.logging import logger


# Standardized OIL SENTINEL Reason Codes
REASON_CODES = {
    "SIF-001": "High-energy mechanism with human exposure",
    "SIF-002": "Person within hazardous trajectory",
    "SIF-003": "Barrier absent",
    "SIF-004": "Barrier failed",
    "SIF-005": "Barrier degraded",
    "SIF-006": "Stored energy release",
    "SIF-007": "Falling object exposure",
    "SIF-008": "Caught-in/between exposure",
    "SIF-009": "Fall-from-height exposure",
    "SIF-010": "Electrical exposure with inadequate isolation",
    "SIF-011": "Suspended load exposure",
    "SIF-012": "Pressure release exposure",
    "SIF-013": "Insufficient evidence — safety review required",
    "SIF-NONE": "No credible serious injury/fatality precursor mechanism identified",
}


@dataclass
class SafetyRule:
    """Definition of a deterministic OIL SENTINEL safety screening rule."""
    rule_id: str
    name: str
    description: str
    reason_code: str
    enabled: bool = True

    def evaluate(self, facts: Dict[str, Any]) -> Optional[RuleTrigger]:
        """Evaluates rule against structured safety facts. Returns RuleTrigger if condition met."""
        raise NotImplementedError


class Rule001HighEnergyExposure(SafetyRule):
    """RULE-001: High-energy mechanism + human exposure + failed/absent/degraded barrier."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-001",
            name="High-Energy Mechanism with Human Exposure",
            description="Credible high-energy release with exposed personnel and compromised barrier.",
            reason_code="SIF-001",
        )

    def evaluate(self, facts: Dict[str, Any]) -> Optional[RuleTrigger]:
        energy = facts.get("energy_source")
        hazard = (facts.get("hazard") or "").lower()
        exposure = (facts.get("exposure") or "").lower()
        bc = facts.get("barrier_condition")

        is_high_energy = energy in (
            EnergySource.KINETIC, EnergySource.PRESSURE, EnergySource.ELECTRICAL,
            EnergySource.STORED_ENERGY, EnergySource.GRAVITATIONAL, EnergySource.HYDROCARBON
        ) or any(k in hazard for k in ("high pressure", "kinetic", "high velocity", "ejection", "explosion", "arc flash"))

        has_exposure = bool(exposure and exposure != "none" and not exposure.startswith("no person"))
        barrier_compromised = bc in (BarrierCondition.FAILED, BarrierCondition.ABSENT, BarrierCondition.DEGRADED)

        if is_high_energy and has_exposure and barrier_compromised:
            ev_list = [e for e in (facts.get("hazard_evidence"), facts.get("exposure_evidence"), facts.get("barrier_evidence")) if e]
            return RuleTrigger(
                rule_id=self.rule_id,
                rule_name=self.name,
                reason_code=self.reason_code,
                description=f"High-energy ({energy or 'mechanism'}) present with exposed personnel and {bc or 'compromised'} barrier.",
                signal_strength=1.0,
                evidence_refs=ev_list,
            )
        return None


class Rule002FallingObject(SafetyRule):
    """RULE-002: Falling object / dropped object + human exposure beneath/near trajectory."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-002",
            name="Falling Object Exposure",
            description="Dropped/falling object hazard with personnel beneath or near impact path.",
            reason_code="SIF-007",
        )

    def evaluate(self, facts: Dict[str, Any]) -> Optional[RuleTrigger]:
        hazard = (facts.get("hazard") or "").lower()
        equipment = (facts.get("equipment") or "").lower()
        exposure = (facts.get("exposure") or "").lower()
        loc = (facts.get("exposure_location") or "").lower()
        energy = facts.get("energy_source")

        is_falling = (
            energy == EnergySource.GRAVITATIONAL or
            any(k in hazard for k in ("fall", "drop", "fell", "ejected", "struck by falling", "dropped object")) or
            "dropped" in equipment
        )
        has_exposure = any(k in exposure or k in loc for k in ("beneath", "below", "underneath", "trajectory", "nearby", "rigger", "rigman", "worker", "person"))

        if is_falling and has_exposure:
            ev_list = [e for e in (facts.get("hazard_evidence"), facts.get("exposure_evidence")) if e]
            return RuleTrigger(
                rule_id=self.rule_id,
                rule_name=self.name,
                reason_code=self.reason_code,
                description="Falling/dropped object hazard with personnel exposed in impact/drop zone.",
                signal_strength=0.95,
                evidence_refs=ev_list,
            )
        return None


class Rule003UnexpectedEjection(SafetyRule):
    """RULE-003: Unexpected movement/ejection + person in trajectory."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-003",
            name="Unexpected Movement / Ejection in Trajectory Path",
            description="Component or tool unexpectedly ejected or moved at speed toward personnel.",
            reason_code="SIF-002",
        )

    def evaluate(self, facts: Dict[str, Any]) -> Optional[RuleTrigger]:
        hazard = (facts.get("hazard") or "").lower()
        exposure = (facts.get("exposure") or "").lower()
        loc = (facts.get("exposure_location") or "").lower()
        energy = facts.get("energy_source")

        is_ejection = (
            energy == EnergySource.KINETIC or
            any(k in hazard for k in ("eject", "came out at speed", "projectile", "slippage", "whiplash", "unexpected movement", "fly away"))
        )
        in_trajectory = any(k in exposure or k in loc for k in ("trajectory", "opposite side", "path", "in line", "nearby", "rigman", "worker"))

        if is_ejection and in_trajectory:
            ev_list = [e for e in (facts.get("hazard_evidence"), facts.get("exposure_evidence"), facts.get("exposure_location_evidence")) if e]
            return RuleTrigger(
                rule_id=self.rule_id,
                rule_name=self.name,
                reason_code=self.reason_code,
                description="Unexpected ejection/movement of component with personnel in trajectory path.",
                signal_strength=0.95,
                evidence_refs=ev_list,
            )
        return None


class Rule004SuspendedLoad(SafetyRule):
    """RULE-004: Suspended load + person beneath or within load path."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-004",
            name="Suspended Load Exposure",
            description="Personnel positioned beneath or within fall path of suspended load.",
            reason_code="SIF-011",
        )

    def evaluate(self, facts: Dict[str, Any]) -> Optional[RuleTrigger]:
        activity = (facts.get("activity") or "").lower()
        hazard = (facts.get("hazard") or "").lower()
        equipment = (facts.get("equipment") or "").lower()
        exposure = (facts.get("exposure") or "").lower()
        loc = (facts.get("exposure_location") or "").lower()

        is_lifting = any(k in activity or k in hazard or k in equipment for k in ("lift", "crane", "rigging", "sling", "hoist", "suspended load"))
        beneath_load = any(k in exposure or k in loc for k in ("beneath", "under load", "below", "load path", "drop zone"))

        if is_lifting and beneath_load:
            ev_list = [e for e in (facts.get("hazard_evidence"), facts.get("exposure_evidence")) if e]
            return RuleTrigger(
                rule_id=self.rule_id,
                rule_name=self.name,
                reason_code=self.reason_code,
                description="Personnel in dangerous proximity to suspended load or rigging drop line.",
                signal_strength=0.95,
                evidence_refs=ev_list,
            )
        return None


class Rule005ElectricalExposure(SafetyRule):
    """RULE-005: Electrical energy + human exposure + inadequate isolation/barrier."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-005",
            name="Electrical Energy Exposure",
            description="Live electrical contact hazard without positive isolation.",
            reason_code="SIF-010",
        )

    def evaluate(self, facts: Dict[str, Any]) -> Optional[RuleTrigger]:
        energy = facts.get("energy_source")
        hazard = (facts.get("hazard") or "").lower()
        exposure = (facts.get("exposure") or "").lower()
        bc = facts.get("barrier_condition")

        is_electrical = (
            energy == EnergySource.ELECTRICAL or
            any(k in hazard for k in ("electric", "voltage", "arc flash", "live wire", "electrocution"))
        )
        has_exposure = bool(exposure and exposure != "none")
        isolation_inadequate = bc in (BarrierCondition.FAILED, BarrierCondition.ABSENT, BarrierCondition.DEGRADED, BarrierCondition.UNKNOWN)

        if is_electrical and has_exposure and isolation_inadequate:
            ev_list = [e for e in (facts.get("hazard_evidence"), facts.get("exposure_evidence")) if e]
            return RuleTrigger(
                rule_id=self.rule_id,
                rule_name=self.name,
                reason_code=self.reason_code,
                description="Electrical hazard with exposed personnel and inadequate isolation/protection.",
                signal_strength=0.90,
                evidence_refs=ev_list,
            )
        return None


class Rule006PressureRelease(SafetyRule):
    """RULE-006: Pressure / stored energy release + human exposure."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-006",
            name="Pressurized / Stored Energy Release",
            description="Uncontrolled pressure release or hydraulic/pneumatic burst with exposed personnel.",
            reason_code="SIF-012",
        )

    def evaluate(self, facts: Dict[str, Any]) -> Optional[RuleTrigger]:
        energy = facts.get("energy_source")
        hazard = (facts.get("hazard") or "").lower()
        exposure = (facts.get("exposure") or "").lower()

        is_pressure = (
            energy in (EnergySource.PRESSURE, EnergySource.STORED_ENERGY) or
            any(k in hazard for k in ("pressure release", "hydraulic burst", "pneumatic", "hose whip", "overpressure", "pinhole leak under 200 bar", "bar pressure"))
        )
        has_exposure = bool(exposure and exposure != "none" and not exposure.startswith("no person"))

        if is_pressure and has_exposure:
            ev_list = [e for e in (facts.get("hazard_evidence"), facts.get("exposure_evidence")) if e]
            return RuleTrigger(
                rule_id=self.rule_id,
                rule_name=self.name,
                reason_code=self.reason_code,
                description="Uncontrolled pressure/stored energy release with personnel in line of fire.",
                signal_strength=0.90,
                evidence_refs=ev_list,
            )
        return None


class Rule007FallFromHeight(SafetyRule):
    """RULE-007: Fall from height + exposed person + inadequate fall protection."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-007",
            name="Fall From Height Exposure",
            description="Work at elevated position without fall arrest or intact guardrails.",
            reason_code="SIF-009",
        )

    def evaluate(self, facts: Dict[str, Any]) -> Optional[RuleTrigger]:
        hazard = (facts.get("hazard") or "").lower()
        activity = (facts.get("activity") or "").lower()
        exposure = (facts.get("exposure") or "").lower()
        bc = facts.get("barrier_condition")

        is_fall_height = any(k in hazard or k in activity for k in ("fall from height", "elevated", "working at height", "scaffold fall", "roof opening", "unprotected edge"))
        has_exposure = bool(exposure and exposure != "none")
        protection_inadequate = bc in (BarrierCondition.FAILED, BarrierCondition.ABSENT, BarrierCondition.DEGRADED, BarrierCondition.UNKNOWN)

        if is_fall_height and has_exposure and protection_inadequate:
            ev_list = [e for e in (facts.get("hazard_evidence"), facts.get("exposure_evidence")) if e]
            return RuleTrigger(
                rule_id=self.rule_id,
                rule_name=self.name,
                reason_code=self.reason_code,
                description="Personnel exposed to fall from height with compromised fall protection barrier.",
                signal_strength=0.95,
                evidence_refs=ev_list,
            )
        return None


class Rule008CaughtInBetween(SafetyRule):
    """RULE-008: Caught-in/between mechanism + person exposed to moving equipment."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-008",
            name="Caught-In / Between Equipment Exposure",
            description="Personnel exposed to pinch points, rotating shafts, or nip points.",
            reason_code="SIF-008",
        )

    def evaluate(self, facts: Dict[str, Any]) -> Optional[RuleTrigger]:
        hazard = (facts.get("hazard") or "").lower()
        exposure = (facts.get("exposure") or "").lower()
        energy = facts.get("energy_source")

        is_caught = (
            energy in (EnergySource.MECHANICAL, EnergySource.KINETIC) and
            any(k in hazard for k in ("caught in", "caught between", "pinch point", "entanglement", "crushing", "rotating shaft", "nip point"))
        )
        has_exposure = bool(exposure and exposure != "none")

        if is_caught and has_exposure:
            ev_list = [e for e in (facts.get("hazard_evidence"), facts.get("exposure_evidence")) if e]
            return RuleTrigger(
                rule_id=self.rule_id,
                rule_name=self.name,
                reason_code=self.reason_code,
                description="Personnel exposed to crushing, pinch-point, or caught-in/between machinery hazard.",
                signal_strength=0.90,
                evidence_refs=ev_list,
            )
        return None


class SafetyRuleEngine:
    """
    OIL SENTINEL Deterministic Safety Rule Engine.

    Evaluates 8 deterministic safety rules against Phase 3 safety facts.
    Calculates 5 transparent screening signals.
    Produces SifScreeningResult (YES / NO / UNCERTAIN).
    """

    SCREENING_VERSION = "sif-engine-v1"

    def __init__(self):
        self.rules: List[SafetyRule] = [
            Rule001HighEnergyExposure(),
            Rule002FallingObject(),
            Rule003UnexpectedEjection(),
            Rule004SuspendedLoad(),
            Rule005ElectricalExposure(),
            Rule006PressureRelease(),
            Rule007FallFromHeight(),
            Rule008CaughtInBetween(),
        ]

    def screen(
        self,
        report_id: str,
        safety_facts: Dict[str, Any],
        narrative: str,
    ) -> SifScreeningResult:
        """
        Executes full screening workflow:
        1. Evaluate all 8 deterministic rules
        2. Calculate 5 transparent screening signals
        3. Determine SIF decision (YES / NO / UNCERTAIN)
        4. Apply rule overrides
        5. Build evidence-backed explanation
        """
        # 1. Evaluate deterministic rules
        triggered_rules: List[RuleTrigger] = []
        for r in self.rules:
            if r.enabled:
                trig = r.evaluate(safety_facts)
                if trig:
                    triggered_rules.append(trig)

        # 2. Calculate transparent signals (0.0 to 1.0)
        signals = self._calculate_signals(safety_facts, narrative, triggered_rules)

        # 3. Decision Logic & Rule Override
        decision, confidence, reason_code, explanation, factors, review_req, review_reason = self._make_decision(
            report_id=report_id,
            facts=safety_facts,
            narrative=narrative,
            signals=signals,
            triggered_rules=triggered_rules,
        )

        rule_ids = [tr.rule_id for tr in triggered_rules]
        reason_codes = list(dict.fromkeys([tr.reason_code for tr in triggered_rules] + ([reason_code] if reason_code else [])))

        return SifScreeningResult(
            report_id=report_id,
            sif_fpi_potential=decision,
            sif_confidence=confidence,
            screening_status=ScreeningStatus.SCREENED,
            screening_reason=explanation,
            reason_codes=reason_codes,
            rule_ids_triggered=rule_ids,
            contributing_factors=factors,
            signals=signals,
            rules_triggered=triggered_rules,
            screening_version=self.SCREENING_VERSION,
            screened_at=datetime.now(timezone.utc),
            review_required=review_req,
            review_reason=review_reason,
        )

    # ── Signal calculation ──────────────────────────────────────────────────

    def _calculate_signals(
        self,
        facts: Dict[str, Any],
        narrative: str,
        triggered_rules: List[RuleTrigger],
    ) -> ScreeningSignals:
        energy = facts.get("energy_source")
        hazard = (facts.get("hazard") or "").lower()
        exposure = (facts.get("exposure") or "").lower()
        loc = (facts.get("exposure_location") or "").lower()
        bc = facts.get("barrier_condition")
        pc = (facts.get("potential_consequence") or "").lower()

        # Mechanism signal (0.0 - 1.0)
        if triggered_rules:
            mech_sig = max([tr.signal_strength for tr in triggered_rules])
        elif energy in (EnergySource.KINETIC, EnergySource.PRESSURE, EnergySource.ELECTRICAL, EnergySource.STORED_ENERGY, EnergySource.GRAVITATIONAL):
            mech_sig = 0.80
        elif energy in (EnergySource.MECHANICAL, EnergySource.CHEMICAL, EnergySource.HYDROCARBON, EnergySource.THERMAL):
            mech_sig = 0.65
        elif hazard and hazard != "none":
            mech_sig = 0.40
        else:
            mech_sig = 0.10

        # Exposure signal (0.0 - 1.0)
        if any(k in exposure or k in loc for k in ("trajectory", "beneath", "underneath", "passing nearby", "opposite side", "path", "rigger", "rigman")):
            exp_sig = 0.90
        elif exposure and exposure != "none" and not exposure.startswith("no person"):
            exp_sig = 0.70
        elif "worker" in narrative.lower() or "person" in narrative.lower() or "operator" in narrative.lower():
            exp_sig = 0.45
        elif facts.get("exposure_evidence_status") == EvidenceStatus.UNKNOWN:
            exp_sig = 0.20
        else:
            exp_sig = 0.05

        # Barrier signal (0.0 - 1.0)
        if bc == BarrierCondition.FAILED or bc == BarrierCondition.ABSENT:
            bar_sig = 0.95
        elif bc == BarrierCondition.DEGRADED:
            bar_sig = 0.75
        elif bc == BarrierCondition.UNKNOWN:
            bar_sig = 0.50
        elif bc == BarrierCondition.INTACT:
            bar_sig = 0.10
        else:
            bar_sig = 0.30

        # Consequence signal (0.0 - 1.0)
        if any(k in pc for k in ("fatal", "death", "severe", "serious", "struck-by", "injection", "burn", "electrocution", "fracture", "amputation")):
            con_sig = 0.90
        elif pc and pc != "none":
            con_sig = 0.60
        elif mech_sig >= 0.70:
            con_sig = 0.50
        else:
            con_sig = 0.20

        # Evidence signal (0.0 - 1.0) based on confidence averages across 9 facts
        conf_values = [
            facts.get(f"{field}_confidence")
            for field in ("activity", "equipment", "hazard", "energy_source", "exposure", "exposure_location", "barrier", "barrier_condition", "potential_consequence")
            if facts.get(f"{field}_confidence") is not None
        ]
        if conf_values:
            ev_sig = float(sum(conf_values) / len(conf_values))
        else:
            ev_sig = 0.50

        return ScreeningSignals(
            mechanism_signal=round(mech_sig, 2),
            exposure_signal=round(exp_sig, 2),
            barrier_signal=round(bar_sig, 2),
            consequence_signal=round(con_sig, 2),
            evidence_signal=round(ev_sig, 2),
        )

    # ── Decision & Override Logic ───────────────────────────────────────────

    def _make_decision(
        self,
        report_id: str,
        facts: Dict[str, Any],
        narrative: str,
        signals: ScreeningSignals,
        triggered_rules: List[RuleTrigger],
    ) -> Tuple[SifDecision, float, str, str, List[str], bool, Optional[str]]:

        factors: List[str] = []
        review_required = False
        review_reason: Optional[str] = None

        # ── 1. RULE OVERRIDE: Any triggered deterministic safety rule → SIF YES ──
        if triggered_rules:
            factors.append(f"Triggered {len(triggered_rules)} deterministic safety rule(s)")
            if facts.get("exposure"):
                factors.append(f"Human exposure: {facts['exposure']}")
            if facts.get("hazard"):
                factors.append(f"Hazardous mechanism: {facts['hazard']}")
            if facts.get("barrier_condition"):
                factors.append(f"Barrier condition: {facts['barrier_condition']}")

            # If evidence confidence is extremely low (< 0.25), flag UNCERTAIN instead of YES to avoid hallucination
            if signals.evidence_signal < 0.25:
                explanation = (
                    f"Deterministic safety rules triggered ({', '.join(r.rule_id for r in triggered_rules)}), "
                    "but narrative evidence confidence is too low to verify exposure."
                )
                return (
                    SifDecision.UNCERTAIN,
                    0.50,
                    "SIF-013",
                    explanation,
                    factors,
                    True,
                    "Low evidence confidence for triggered safety rule",
                )

            rule_names = ", ".join(f"{r.rule_id} ({r.rule_name})" for r in triggered_rules)
            explanation = (
                f"SIF/FPI Precursor Detected. Triggered deterministic safety rule(s): {rule_names}. "
                f"Narrative evidence supports credible high-energy hazard with personnel exposure."
            )
            confidence = min(0.98, max(0.80, signals.evidence_signal + 0.15))
            return (
                SifDecision.YES,
                round(confidence, 2),
                triggered_rules[0].reason_code,
                explanation,
                factors,
                False,
                None,
            )

        # ── 2. UNCERTAIN HANDLING: Missing facts, low evidence, vague narrative ──
        has_hazardous_mech = signals.mechanism_signal >= 0.60
        is_exposure_unknown = facts.get("exposure_evidence_status") == EvidenceStatus.UNKNOWN or signals.exposure_signal == 0.20
        is_barrier_unknown = facts.get("barrier_condition") == BarrierCondition.UNKNOWN
        is_low_evidence = signals.evidence_signal < 0.40

        # Poor / vague narrative check
        is_vague = len(narrative.split()) < 8 or all(
            facts.get(f) is None for f in ("hazard", "exposure", "equipment")
        )

        if is_vague:
            explanation = (
                "Insufficient safety detail in report narrative. "
                "Unable to establish hazardous mechanism or human exposure scenario."
            )
            return (
                SifDecision.UNCERTAIN,
                0.40,
                "SIF-013",
                explanation,
                ["Vague or low-quality narrative", "Missing hazardous mechanism & exposure details"],
                True,
                "Narrative lacks sufficient detail for SIF screening",
            )

        if has_hazardous_mech and (is_exposure_unknown or is_barrier_unknown or is_low_evidence):
            uncertain_reasons = []
            if is_exposure_unknown:
                uncertain_reasons.append("Human exposure cannot be established from narrative")
            if is_barrier_unknown:
                uncertain_reasons.append("Barrier condition is UNKNOWN")
            if is_low_evidence:
                uncertain_reasons.append("Overall extraction confidence is low")

            explanation = (
                f"Potentially hazardous mechanism identified ({facts.get('hazard') or facts.get('energy_source')}), "
                f"but key safety facts are uncertain: {'; '.join(uncertain_reasons)}."
            )
            return (
                SifDecision.UNCERTAIN,
                0.55,
                "SIF-013",
                explanation,
                uncertain_reasons,
                True,
                "Hazardous mechanism present but exposure or barrier condition is uncertain",
            )

        # ── 3. NO SIF PRECURSOR: No credible serious mechanism or no exposure ─────
        if signals.mechanism_signal < 0.50 or signals.exposure_signal < 0.25:
            explanation = (
                "No credible serious injury or fatality precursor mechanism identified in available report evidence. "
                "Energy level and exposure conditions do not indicate SIF/FPI potential."
            )
            factors.append("No high-energy mechanism or hazardous trajectory identified")
            if facts.get("barrier_condition") == BarrierCondition.INTACT:
                factors.append("Barrier intact")

            return (
                SifDecision.NO,
                round(max(0.75, signals.evidence_signal), 2),
                "SIF-NONE",
                explanation,
                factors,
                False,
                None,
            )

        # ── 4. DEFAULT FALLBACK ──────────────────────────────────────────────
        explanation = "Screening evaluation completed without triggering high-priority SIF rules."
        return (
            SifDecision.NO,
            0.70,
            "SIF-NONE",
            explanation,
            ["No critical safety rule triggered"],
            False,
            None,
        )
