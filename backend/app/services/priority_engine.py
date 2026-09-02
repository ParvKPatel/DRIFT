"""
Phase 5 — OIL SENTINEL HSE Priority Engine

Calculates a transparent 0–100 HSE Prioritisation Score and Priority Level
to rank safety reports for human HSE review attention.

IMPORTANT CONSTRAINTS:
1. The priority_score is a 0–100 RANKING SCORE only for HSE attention.
2. It does NOT represent probability of death, fatality risk, or guaranteed safety.
3. Component availability tracking: Phase 6 components (recurrence, novelty, reporting anomaly)
   are explicitly tracked as NOT_YET_AVAILABLE rather than fabricating false scores.
4. Critical Safety Overrides: Critical Phase 4 safety rules override weak priority scores
   to prevent dangerous reports from being downgraded to ROUTINE.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from app.config import settings
from app.schemas.enums import (
    PriorityLevel,
    ComponentStatus,
    SifDecision,
    BarrierCondition,
)
from app.schemas.priority_engine import (
    PriorityResult,
    PriorityComponent,
)
from app.utils.logging import logger


PRIORITY_REASON_CODES = {
    "PRIORITY-001": "Strong SIF/FPI precursor evidence",
    "PRIORITY-002": "Human exposure in line of fire documented",
    "PRIORITY-003": "Barrier degraded",
    "PRIORITY-004": "Barrier failed",
    "PRIORITY-005": "Barrier absent",
    "PRIORITY-006": "Critical deterministic safety rule triggered",
    "PRIORITY-007": "Insufficient evidence for full safety triage",
    "PRIORITY-008": "Uncertain SIF screening require safety inspector review",
    "PRIORITY-009": "High-consequence hazardous energy mechanism",
    "PRIORITY-010": "Life-Saving Rule mapped with strong evidence",
}


class HsePriorityEngine:
    """Calculates 0-100 HSE Prioritisation Score and Priority Level."""

    PRIORITY_VERSION = "priority-engine-v1"

    def calculate_priority(
        self,
        report_id: str,
        safety_analysis_facts: Dict[str, Any],
    ) -> PriorityResult:
        """
        Executes full HSE priority scoring:
        1. Calculate available component scores (sif_evidence_score, barrier_score).
        2. Mark unavailable Phase 6 components as NOT_YET_AVAILABLE.
        3. Compute weighted 0–100 priority_score.
        4. Apply safety overrides & uncertainty propagation.
        5. Assign PriorityLevel (CRITICAL, HIGH_PRIORITY_SIF_FPI_PRECURSOR, SAFETY_REVIEW, ROUTINE, UNCERTAIN).
        6. Build 'Why Prioritized' evidence explanation.
        """
        facts = safety_analysis_facts

        sif_decision = facts.get("sif_fpi_potential") or SifDecision.UNCERTAIN
        sif_conf = facts.get("sif_confidence") or 0.50
        bc = facts.get("barrier_condition") or BarrierCondition.UNKNOWN
        rule_ids = facts.get("rule_ids_triggered") or []

        # ── 1. Component 1: SIF Evidence Score (0.0 to 1.0) ──────────────────
        sif_score = self._calc_sif_evidence_score(facts, sif_decision, sif_conf, rule_ids)

        # ── 2. Component 2: Barrier Score (0.0 to 1.0) ───────────────────────
        bar_score = self._calc_barrier_score(bc)

        # ── 3. Phase 6 Components: Recurrence & Escalation ───────────────────
        rec_score_val = facts.get("recurrence_score")
        esc_score_val = facts.get("escalation_score")

        rec_status = ComponentStatus.AVAILABLE if rec_score_val is not None else ComponentStatus.NOT_YET_AVAILABLE
        esc_status = ComponentStatus.AVAILABLE if esc_score_val is not None else ComponentStatus.NOT_YET_AVAILABLE

        # ── 4. Component Breakdown & Availability ─────────────────────────────
        components: List[PriorityComponent] = [
            PriorityComponent(
                name="sif_evidence_score",
                score=round(sif_score, 2),
                weight=settings.PRIORITY_WEIGHT_SIF,
                status=ComponentStatus.AVAILABLE,
                description="Derived from Phase 4 SIF screening, mechanism strength, and rule triggers",
            ),
            PriorityComponent(
                name="barrier_score",
                score=round(bar_score, 2),
                weight=settings.PRIORITY_WEIGHT_BARRIER,
                status=ComponentStatus.AVAILABLE,
                description="Derived from Phase 3 barrier condition (FAILED/ABSENT=1.0, DEGRADED=0.75, UNKNOWN=0.5, INTACT=0.1)",
            ),
            PriorityComponent(
                name="recurrence_score",
                score=round(rec_score_val, 2) if rec_score_val is not None else None,
                weight=settings.PRIORITY_WEIGHT_RECURRENCE,
                status=rec_status,
                description="Precursor recurrence across historical reports (Phase 6 Relationship Intelligence)",
            ),
            PriorityComponent(
                name="novelty_score",
                score=None,
                weight=settings.PRIORITY_WEIGHT_NOVELTY,
                status=ComponentStatus.NOT_YET_AVAILABLE,
                description="Semantic novelty detection score (Phase 6)",
            ),
            PriorityComponent(
                name="escalation_score",
                score=round(esc_score_val / 100.0, 2) if esc_score_val is not None else None,
                weight=settings.PRIORITY_WEIGHT_ANOMALY,
                status=esc_status,
                description="Cluster escalation & precursor accumulation score (Phase 6 Pattern Engine)",
            ),
        ]

        # ── 5. Weighted Priority Score Calculation (0 to 100) ───────────────
        w_sif = settings.PRIORITY_WEIGHT_SIF
        w_bar = settings.PRIORITY_WEIGHT_BARRIER
        w_rec = settings.PRIORITY_WEIGHT_RECURRENCE if rec_score_val is not None else 0.0
        w_esc = settings.PRIORITY_WEIGHT_ANOMALY if esc_score_val is not None else 0.0

        weight_sum = w_sif + w_bar + w_rec + w_esc

        weighted_val = (sif_score * w_sif) + (bar_score * w_bar)
        if rec_score_val is not None:
            weighted_val += rec_score_val * w_rec
        if esc_score_val is not None:
            weighted_val += (esc_score_val / 100.0) * w_esc

        if weight_sum > 0:
            raw_score = weighted_val / weight_sum
        else:
            raw_score = (sif_score + bar_score) / 2.0

        priority_score = round(raw_score * 100.0, 1)

        # ── 5. Safety Overrides & Level Assignment ───────────────────────────
        override = False
        override_reason: Optional[str] = None
        reason_codes: List[str] = []
        why_prioritized: List[str] = []

        # Check for critical safety rule override
        if rule_ids and any(r in rule_ids for r in ("RULE-001", "RULE-002", "RULE-003", "RULE-004", "RULE-007")):
            override = True
            override_reason = f"Critical Phase 4 safety rule(s) triggered: {', '.join(rule_ids)}"
            reason_codes.append("PRIORITY-006")
            why_prioritized.append(f"CRITICAL OVERRIDE: {override_reason}")

        if sif_decision == SifDecision.YES:
            reason_codes.append("PRIORITY-001")
            why_prioritized.append("Strong SIF/FPI precursor evidence identified")

        if facts.get("exposure"):
            reason_codes.append("PRIORITY-002")
            why_prioritized.append(f"Personnel exposure: {facts['exposure']}")

        if bc in (BarrierCondition.FAILED, BarrierCondition.ABSENT):
            reason_codes.append("PRIORITY-004" if bc == BarrierCondition.FAILED else "PRIORITY-005")
            why_prioritized.append(f"Barrier state: {bc.value}")
        elif bc == BarrierCondition.DEGRADED:
            reason_codes.append("PRIORITY-003")
            why_prioritized.append("Barrier degraded")

        if facts.get("primary_life_saving_rule") and facts["primary_life_saving_rule"] != "UNKNOWN":
            reason_codes.append("PRIORITY-010")
            why_prioritized.append(f"Mapped to Life-Saving Rule: {facts['primary_life_saving_rule']}")

        if rec_score_val is not None and rec_score_val >= 0.5:
            why_prioritized.append(f"Precursor Recurrence detected across related reports ({round(rec_score_val * 100)}%)")

        if esc_score_val is not None and esc_score_val >= 50.0:
            why_prioritized.append(f"Precursor Cluster Escalation active (Score: {esc_score_val})")

        # Determine Priority Level
        if override or priority_score >= settings.PRIORITY_THRESHOLD_CRITICAL:
            level = PriorityLevel.CRITICAL
        elif sif_decision == SifDecision.YES or priority_score >= settings.PRIORITY_THRESHOLD_HIGH:
            level = PriorityLevel.HIGH_PRIORITY_SIF_FPI_PRECURSOR
        elif sif_decision == SifDecision.UNCERTAIN:
            level = PriorityLevel.UNCERTAIN
            reason_codes.append("PRIORITY-008")
            why_prioritized.append("UNCERTAIN SIF screening requires safety inspector triage")
        elif priority_score >= settings.PRIORITY_THRESHOLD_REVIEW:
            level = PriorityLevel.SAFETY_REVIEW
        else:
            level = PriorityLevel.ROUTINE

        unavailable_components = []
        if rec_score_val is None:
            unavailable_components.append("Recurrence Score")
        if esc_score_val is None:
            unavailable_components.append("Escalation Score")
        unavailable_components.append("Semantic Novelty Score")

        return PriorityResult(
            report_id=report_id,
            priority_score=priority_score,
            priority_level=level,
            priority_reason_codes=list(dict.fromkeys(reason_codes)),
            priority_override=override,
            override_reason=override_reason,
            components=components,
            why_prioritized=why_prioritized,
            unavailable_components=unavailable_components,
            priority_version=self.PRIORITY_VERSION,
            calculated_at=datetime.now(timezone.utc),
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _calc_sif_evidence_score(
        self,
        facts: Dict[str, Any],
        sif_decision: SifDecision,
        sif_conf: float,
        rule_ids: List[str],
    ) -> float:
        if sif_decision == SifDecision.YES:
            base = 0.85
            if rule_ids:
                base += 0.10
            return min(1.0, base + (sif_conf * 0.05))
        elif sif_decision == SifDecision.UNCERTAIN:
            return 0.55
        else:
            # SifDecision.NO
            if facts.get("hazard_confidence", 0.0) > 0.8:
                return 0.10
            return 0.20

    def _calc_barrier_score(self, bc: BarrierCondition) -> float:
        if bc in (BarrierCondition.FAILED, BarrierCondition.ABSENT):
            return 1.0
        elif bc == BarrierCondition.DEGRADED:
            return 0.75
        elif bc == BarrierCondition.UNKNOWN:
            return 0.50
        elif bc == BarrierCondition.INTACT:
            return 0.10
        return 0.30
