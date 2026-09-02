"""
Phase 6 — Hybrid Report-to-Report Similarity Engine

Calculates report-to-report similarity combining:
1. Semantic narrative/vector similarity (cosine distance of embedding vectors)
2. Safety mechanism similarity (hazard, energy, exposure, consequence)
3. Structured metadata overlap (activity, equipment, barrier, location, LSR)

Formula:
similarity = w_semantic * semantic_sim + w_mechanism * mechanism_sim + w_structured * structured_sim

Configurable prototype weights & display bands.
"""

import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import date

from app.config import settings
from app.schemas.enums import SimilarityBand
from app.schemas.similarity_schemas import SharedMechanismDetails, SimilarReportItem
from app.models.reports import Report
from app.models.safety_analysis import SafetyAnalysis
from app.utils.logging import logger


class SimilarityEngine:
    """Calculates report similarity and shared mechanism explanations."""

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculates cosine similarity between two float vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        dot = np.dot(a, b)
        sim = float(dot / (norm_a * norm_b))
        return max(0.0, min(1.0, sim))

    @classmethod
    def calculate_hybrid_similarity(
        cls,
        r1: Report,
        sa1: Optional[SafetyAnalysis],
        v1: List[float],
        r2: Report,
        sa2: Optional[SafetyAnalysis],
        v2: List[float],
    ) -> Tuple[float, SharedMechanismDetails]:
        """
        Calculates hybrid similarity score and shared mechanism details between report 1 and report 2.
        """
        # 1. Semantic vector similarity
        semantic_sim = cls.cosine_similarity(v1, v2)

        # 2. Mechanism similarity (Hazard + Energy + Exposure + Consequence)
        mech_sim, shared_mech = cls._calc_mechanism_similarity(sa1, sa2)

        # 3. Structured metadata overlap
        struct_sim, shared_struct = cls._calc_structured_similarity(r1, sa1, r2, sa2)

        # Combined weighted similarity
        w_sem = settings.SIMILARITY_WEIGHT_SEMANTIC
        w_mech = settings.SIMILARITY_WEIGHT_MECHANISM
        w_str = settings.SIMILARITY_WEIGHT_STRUCTURED
        w_sum = w_sem + w_mech + w_str

        if w_sum > 0:
            total_sim = ((semantic_sim * w_sem) + (mech_sim * w_mech) + (struct_sim * w_str)) / w_sum
        else:
            total_sim = (semantic_sim + mech_sim + struct_sim) / 3.0

        total_sim = round(float(total_sim), 3)

        # Days between report dates
        days_between = None
        if r1.report_date and r2.report_date:
            days_between = abs((r1.report_date - r2.report_date).days)

        details = SharedMechanismDetails(
            shared_activity=shared_struct.get("activity"),
            shared_hazard=shared_mech.get("hazard"),
            shared_equipment=shared_struct.get("equipment"),
            shared_exposure=shared_mech.get("exposure"),
            shared_barrier=shared_struct.get("barrier"),
            shared_lsr=shared_struct.get("lsr"),
            shared_asset=shared_struct.get("asset"),
            shared_functional_location=shared_struct.get("location"),
            days_between=days_between,
            semantic_similarity=round(semantic_sim, 3),
            mechanism_similarity=round(mech_sim, 3),
            structured_similarity=round(struct_sim, 3),
        )

        return total_sim, details

    @staticmethod
    def map_similarity_band(score: float) -> SimilarityBand:
        """Maps float score (0.0 to 1.0) to prototype SimilarityBand."""
        if score >= 0.85:
            return SimilarityBand.HIGHLY_SIMILAR
        elif score >= 0.70:
            return SimilarityBand.STRONGLY_RELATED
        elif score >= 0.50:
            return SimilarityBand.POTENTIALLY_RELATED
        else:
            return SimilarityBand.WEAK

    # ── Internal Overlap Helpers ──────────────────────────────────────────────

    @classmethod
    def _calc_mechanism_similarity(
        cls,
        sa1: Optional[SafetyAnalysis],
        sa2: Optional[SafetyAnalysis],
    ) -> Tuple[float, Dict[str, Optional[str]]]:
        if not sa1 or not sa2:
            return 0.0, {}

        matches = 0
        total = 4
        shared = {}

        # Hazard
        h1 = (sa1.hazard or "").lower().strip()
        h2 = (sa2.hazard or "").lower().strip()
        if h1 and h2 and h1 != "unknown" and h2 != "unknown":
            if h1 == h2 or h1 in h2 or h2 in h1 or cls._token_overlap(h1, h2) >= 0.5:
                matches += 1.0
                shared["hazard"] = sa1.hazard

        # Energy Source
        if sa1.energy_source and sa2.energy_source and sa1.energy_source == sa2.energy_source and sa1.energy_source.value != "UNKNOWN":
            matches += 1.0

        # Exposure
        e1 = (sa1.exposure or "").lower().strip()
        e2 = (sa2.exposure or "").lower().strip()
        if e1 and e2 and e1 != "unknown" and e2 != "unknown":
            if e1 == e2 or e1 in e2 or e2 in e1 or cls._token_overlap(e1, e2) >= 0.4:
                matches += 1.0
                shared["exposure"] = sa1.exposure

        # Consequence
        c1 = (sa1.potential_consequence or "").lower().strip()
        c2 = (sa2.potential_consequence or "").lower().strip()
        if c1 and c2 and c1 != "unknown" and c2 != "unknown":
            if c1 == c2 or c1 in c2 or c2 in c1 or cls._token_overlap(c1, c2) >= 0.4:
                matches += 1.0

        score = matches / float(total)
        return score, shared

    @classmethod
    def _calc_structured_similarity(
        cls,
        r1: Report,
        sa1: Optional[SafetyAnalysis],
        r2: Report,
        sa2: Optional[SafetyAnalysis],
    ) -> Tuple[float, Dict[str, Optional[str]]]:
        matches = 0.0
        total = 5.0
        shared = {}

        # Functional Location / Site
        loc1 = (r1.functional_location or r1.site or "").lower().strip()
        loc2 = (r2.functional_location or r2.site or "").lower().strip()
        if loc1 and loc2 and loc1 == loc2:
            matches += 1.0
            shared["location"] = r1.functional_location or r1.site

        if sa1 and sa2:
            # Activity
            act1 = (sa1.activity or "").lower().strip()
            act2 = (sa2.activity or "").lower().strip()
            if act1 and act2 and act1 != "unknown" and act2 != "unknown":
                if act1 == act2 or act1 in act2 or act2 in act1 or cls._token_overlap(act1, act2) >= 0.5:
                    matches += 1.0
                    shared["activity"] = sa1.activity

            # Equipment
            eq1 = (sa1.equipment or "").lower().strip()
            eq2 = (sa2.equipment or "").lower().strip()
            if eq1 and eq2 and eq1 != "unknown" and eq2 != "unknown":
                if eq1 == eq2 or eq1 in eq2 or eq2 in eq1 or cls._token_overlap(eq1, eq2) >= 0.5:
                    matches += 1.0
                    shared["equipment"] = sa1.equipment

            # Barrier
            b1 = (sa1.barrier or "").lower().strip()
            b2 = (sa2.barrier or "").lower().strip()
            if b1 and b2 and b1 != "unknown" and b2 != "unknown":
                if b1 == b2 or b1 in b2 or b2 in b1 or cls._token_overlap(b1, b2) >= 0.4:
                    matches += 1.0
                    shared["barrier"] = sa1.barrier

            # Life-Saving Rule
            lsr1 = sa1.primary_life_saving_rule or sa1.life_saving_rule
            lsr2 = sa2.primary_life_saving_rule or sa2.life_saving_rule
            if lsr1 and lsr2 and lsr1 != "UNKNOWN" and lsr2 != "UNKNOWN" and lsr1 == lsr2:
                matches += 1.0
                shared["lsr"] = lsr1

        score = matches / total
        return score, shared

    @staticmethod
    def _token_overlap(s1: str, s2: str) -> float:
        w1 = set(s1.split())
        w2 = set(s2.split())
        if not w1 or not w2:
            return 0.0
        inter = w1.intersection(w2)
        union = w1.union(w2)
        return len(inter) / float(len(union))
