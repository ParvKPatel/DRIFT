"""
Phase 6 — Temporal Analysis & Pattern Escalation Engine

Calculates 0-100 Escalation Score and generates Pattern Escalation Alerts based on:
1. Recurrence score (0.0 to 1.0)
2. Recency score (exponential decay over 7d/14d/30d rolling windows)
3. Shared asset & barrier repetition strength
4. Mechanism similarity strength

CRITICAL MANDATES:
- Score is a 0-100 prototype ranking metric for HSE pattern attention.
- Does NOT claim accident prediction or fatality probability.
- Does NOT alter original source incident severity or incident_cause.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, date

from app.config import settings
from app.schemas.enums import EscalationBand, PriorityLevel, AlertType
from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.utils.logging import logger


class EscalationEngine:
    """Calculates temporal pattern escalation scores and builds alert explanations."""

    @classmethod
    def calculate_cluster_escalation(
        cls,
        member_reports: List[Tuple[Report, Optional[SafetyAnalysis], float]],
        now: Optional[datetime] = None,
    ) -> Tuple[float, EscalationBand, List[str], Dict[str, Any]]:
        """
        Calculates 0-100 Escalation Score for a group/cluster of related reports.

        Returns: (escalation_score, escalation_band, why_escalating_reasons, metrics_dict)
        """
        if not member_reports:
            return 0.0, EscalationBand.LOW, ["Insufficient report history."], {}

        if now is None:
            now = datetime.now(timezone.utc)

        count = len(member_reports)

        # Dates & recency
        dates: List[date] = [m[0].report_date for m in member_reports if m[0].report_date]
        if not dates:
            # Fallback to created_at
            dates = [m[0].created_at.date() for m in member_reports if m[0].created_at]

        most_recent_date = max(dates) if dates else now.date()
        oldest_date = min(dates) if dates else now.date()
        time_span_days = max(1, (most_recent_date - oldest_date).days)
        days_since_latest = max(0, (now.date() - most_recent_date).days)

        # Average similarity to cluster
        sim_scores = [m[2] for m in member_reports]
        avg_sim = sum(sim_scores) / float(len(sim_scores)) if sim_scores else 0.5

        # ── 1. Recurrence Score (0.0 to 1.0) ──────────────────────────────────
        # More reports in shorter time span = higher recurrence
        alpha = 0.4
        rec_factor = (count - 1) * (30.0 / time_span_days)
        recurrence_score = min(1.0, 1.0 - math.exp(-alpha * rec_factor * avg_sim))
        if count == 1:
            recurrence_score = 0.10

        # ── 2. Recency Score (Exponential Decay) ──────────────────────────────
        half_life = settings.ESCALATION_RECENCY_HALF_LIFE_DAYS
        decay_lambda = math.log(2) / half_life
        recency_score = math.exp(-decay_lambda * days_since_latest)

        # ── 3. Shared Asset / Location & Barrier Boost (1.0 to 1.4) ───────────
        locations = [m[0].functional_location or m[0].site for m in member_reports if m[0].functional_location or m[0].site]
        barriers = [m[1].barrier for m in member_reports if m[1] and m[1].barrier and m[1].barrier != "UNKNOWN"]

        shared_loc_boost = 1.0
        if locations and len(set(locations)) == 1 and count >= 2:
            shared_loc_boost = 1.25

        shared_bar_boost = 1.0
        if barriers and len(set(barriers)) == 1 and count >= 2:
            shared_bar_boost = 1.15

        asset_barrier_mult = min(1.4, shared_loc_boost * shared_bar_boost)

        # ── 4. Escalation Score Formula (0 to 100) ────────────────────────────
        raw_escalation = 100.0 * (
            (recurrence_score * 0.45) +
            (recency_score * 0.30) +
            (avg_sim * 0.25)
        ) * asset_barrier_mult

        escalation_score = round(max(0.0, min(100.0, raw_escalation)), 1)

        # Determine Escalation Band
        band = cls.map_escalation_band(escalation_score)

        # ── 5. Evidence-Backed "Why Escalating?" Explanation ──────────────────
        why_escalating: List[str] = []
        why_escalating.append(f"✓ {count} related precursor reports identified in cluster")
        if count >= 3:
            why_escalating.append(f"✓ High precursor recurrence density ({count} events over {time_span_days} days)")
        if days_since_latest <= 14:
            why_escalating.append(f"✓ Recent activity ({days_since_latest} days since latest event)")

        if shared_loc_boost > 1.0:
            loc_val = locations[0]
            why_escalating.append(f"✓ Repeated precursor mechanism at same functional location: {loc_val}")

        if shared_bar_boost > 1.0:
            bar_val = barriers[0]
            why_escalating.append(f"✓ Repeated barrier involvement: {bar_val}")

        if avg_sim >= 0.75:
            why_escalating.append(f"✓ Strong semantic mechanism similarity ({round(avg_sim * 100)}%)")

        metrics = {
            "recurrence_score": round(recurrence_score, 2),
            "recency_score": round(recency_score, 2),
            "avg_similarity": round(avg_sim, 2),
            "time_span_days": time_span_days,
            "days_since_latest": days_since_latest,
            "asset_barrier_mult": round(asset_barrier_mult, 2),
        }

        return escalation_score, band, why_escalating, metrics

    @staticmethod
    def map_escalation_band(score: float) -> EscalationBand:
        """Maps 0-100 score to EscalationBand enum."""
        if score >= 85.0:
            return EscalationBand.CRITICAL_PATTERN
        elif score >= 70.0:
            return EscalationBand.HIGH
        elif score >= 50.0:
            return EscalationBand.REVIEW
        elif score >= 30.0:
            return EscalationBand.WATCH
        else:
            return EscalationBand.LOW
