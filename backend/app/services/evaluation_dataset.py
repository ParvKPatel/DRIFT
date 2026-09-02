"""
Phase 9 — Synthetic / Demo Evaluation Dataset

A curated set of 25 reference cases covering:
- SIF Precursors (YES)
- Non-SIF Observations (NO)
- Insufficient Evidence (UNCERTAIN)
- All 9 official Life-Saving Rules
- Degraded / Absent / Intact barriers
- Counterfactual paired cases (exposure vs isolated)

NOTE: Explicitly tagged as SYNTHETIC / DEMO EVALUATION DATA.
"""

from typing import List, Dict, Any
from app.schemas.enums import SifDecision, LifeSavingRule, BarrierCondition, EnergySource

SYNTHETIC_EVALUATION_DATASET: List[Dict[str, Any]] = [
    # ── 1. Line of Fire (SIF: YES) ──
    {
        "case_id": "EVAL-001",
        "narrative": "During pin removal, the rigman hammered the retaining pin and it ejected with high velocity passing inches from his head.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.LINE_OF_FIRE.value,
        "expected_barrier_condition": BarrierCondition.FAILED,
        "category": "High-Energy Ejection",
    },
    # ── 2. Working at Height (SIF: YES) ──
    {
        "case_id": "EVAL-002",
        "narrative": "Scaffolder working at 12m height had unhooked his safety harness to reach an outer ledger when grating slipped beneath him.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.WORKING_AT_HEIGHT.value,
        "expected_barrier_condition": BarrierCondition.ABSENT,
        "category": "Fall from Height",
    },
    # ── 3. Energy Isolation (SIF: YES) ──
    {
        "case_id": "EVAL-003",
        "narrative": "Technician cracked flange on high-pressure hydrocarbon gas manifold without positive physical lock-out tag-out isolation verified.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.ENERGY_ISOLATION.value,
        "expected_barrier_condition": BarrierCondition.FAILED,
        "category": "Pressurized Hydrocarbon Release",
    },
    # ── 4. Confined Space (SIF: YES) ──
    {
        "case_id": "EVAL-004",
        "narrative": "Contractor entered crude oil storage separator vessel before forced ventilation was complete and without continuous multi-gas monitor running.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.CONFINED_SPACE.value,
        "expected_barrier_condition": BarrierCondition.FAILED,
        "category": "Toxic Gas / Oxygen Deficient Atmosphere",
    },
    # ── 5. Safe Mechanical Lifting (SIF: YES) ──
    {
        "case_id": "EVAL-005",
        "narrative": "Crane auxiliary hook wire parted during 8-tonne compressor skid lift; heavy load dropped 3 meters into pipe rack near rigging crew.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.SAFE_MECHANICAL_LIFTING.value,
        "expected_barrier_condition": BarrierCondition.FAILED,
        "category": "Suspended Load Drop",
    },
    # ── 6. Hot Work (SIF: YES) ──
    {
        "case_id": "EVAL-006",
        "narrative": "Welder initiated torch cutting on deck support bracket directly above open drain sump containing residual condensate without fire blanket barrier.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.HOT_WORK.value,
        "expected_barrier_condition": BarrierCondition.ABSENT,
        "category": "Flammable Vapor Flash Fire",
    },
    # ── 7. Driving (SIF: YES) ──
    {
        "case_id": "EVAL-007",
        "narrative": "Heavy transport truck carrying drill pipes had complete brake failure descending steep access road and overturned near pipeline corridor.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.DRIVING.value,
        "expected_barrier_condition": BarrierCondition.FAILED,
        "category": "Heavy Vehicle Rollover",
    },
    # ── 8. Bypassing Safety Controls (SIF: YES) ──
    {
        "case_id": "EVAL-008",
        "narrative": "Operator placed mechanical override defeat on high-level emergency shutdown ESD valve on fuel gas scrubber to avoid unit trip.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.BYPASSING_SAFETY_CONTROLS.value,
        "expected_barrier_condition": BarrierCondition.FAILED,
        "category": "Defeated Critical Safety Barrier",
    },
    # ── 9. Work Authorisation (SIF: YES) ──
    {
        "case_id": "EVAL-009",
        "narrative": "Maintenance crew commenced hot bolting live main steam header without approved Permit to Work and without valid risk assessment on file.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.WORK_AUTHORISATION.value,
        "expected_barrier_condition": BarrierCondition.ABSENT,
        "category": "Unauthorized High-Risk Work",
    },
    # ── 10. Routine Housekeeping (SIF: NO) ──
    {
        "case_id": "EVAL-010",
        "narrative": "Minor empty plastic water bottle left beside tool storage cabinet on workshop floor; picked up and disposed into dry waste bin.",
        "expected_sif": SifDecision.NO,
        "expected_lsr": "UNKNOWN",
        "expected_barrier_condition": BarrierCondition.INTACT,
        "category": "Low-Risk Housekeeping",
    },
    # ── 11. Routine PPE Compliance (SIF: NO) ──
    {
        "case_id": "EVAL-011",
        "narrative": "Worker observed entering administrative office lobby without safety glasses; corrected immediately and glasses put on.",
        "expected_sif": SifDecision.NO,
        "expected_lsr": "UNKNOWN",
        "expected_barrier_condition": BarrierCondition.INTACT,
        "category": "Minor Behavioral Observation",
    },
    # ── 12. Office Ergonomics (SIF: NO) ──
    {
        "case_id": "EVAL-012",
        "narrative": "Clerk noted office desk chair armrest loose; tightened using hex key screwdriver.",
        "expected_sif": SifDecision.NO,
        "expected_lsr": "UNKNOWN",
        "expected_barrier_condition": BarrierCondition.INTACT,
        "category": "Ergonomics / Office",
    },
    # ── 13. Eyewash Station Maintenance (SIF: NO) ──
    {
        "case_id": "EVAL-013",
        "narrative": "Routine weekly inspection found eyewash unit water pressure slightly low; line flushed and filter replaced.",
        "expected_sif": SifDecision.NO,
        "expected_lsr": "UNKNOWN",
        "expected_barrier_condition": BarrierCondition.DEGRADED,
        "category": "Facility Maintenance",
    },
    # ── 14. Small Hand Tool Rust (SIF: NO) ──
    {
        "case_id": "EVAL-014",
        "narrative": "Hand wrench found with surface rust in tool room; wiped down with protective oil coat.",
        "expected_sif": SifDecision.NO,
        "expected_lsr": "UNKNOWN",
        "expected_barrier_condition": BarrierCondition.INTACT,
        "category": "Routine Tool Maintenance",
    },
    # ── 15. Ambiguous / Insufficient Narrative (SIF: UNCERTAIN) ──
    {
        "case_id": "EVAL-015",
        "narrative": "Observed sound near separator module during shift change.",
        "expected_sif": SifDecision.UNCERTAIN,
        "expected_lsr": "UNKNOWN",
        "expected_barrier_condition": BarrierCondition.UNKNOWN,
        "category": "Ambiguous Sound",
    },
    # ── 16. Incomplete Electrical Inspection (SIF: UNCERTAIN) ──
    {
        "case_id": "EVAL-016",
        "narrative": "Panel door was slightly ajar in battery room; unknown whether live terminals were exposed behind cover plate.",
        "expected_sif": SifDecision.UNCERTAIN,
        "expected_lsr": LifeSavingRule.ENERGY_ISOLATION.value,
        "expected_barrier_condition": BarrierCondition.DEGRADED,
        "category": "Incomplete Exposure Evidence",
    },
    # ── 17. Unclear Chemical Odor (SIF: UNCERTAIN) ──
    {
        "case_id": "EVAL-017",
        "narrative": "Faint sweet odor noticed near chemical injection skid; wind speed zero and personnel vacated area to investigate.",
        "expected_sif": SifDecision.UNCERTAIN,
        "expected_lsr": "UNKNOWN",
        "expected_barrier_condition": BarrierCondition.UNKNOWN,
        "category": "Unconfirmed Exposure",
    },
    # ── 18. Line of Fire (Heavy Component) (SIF: YES) ──
    {
        "case_id": "EVAL-018",
        "narrative": "Drill collar shifted on catwalk rolling toward roustabout who jumped clear over handrail.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.LINE_OF_FIRE.value,
        "expected_barrier_condition": BarrierCondition.FAILED,
        "category": "Rolling Tubular Exposure",
    },
    # ── 19. Electrical Flash Arc (SIF: YES) ──
    {
        "case_id": "EVAL-019",
        "narrative": "Electrician opened 415V MCC breaker door without arc flash shield; flash arc singed technician glove.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.ENERGY_ISOLATION.value,
        "expected_barrier_condition": BarrierCondition.FAILED,
        "category": "Arc Flash Exposure",
    },
    # ── 20. Struck-by Crane Swing (SIF: YES) ──
    {
        "case_id": "EVAL-020",
        "narrative": "Counterweight of mobile crane swung through blind spot striking rigger standing inside barricade perimeter.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.SAFE_MECHANICAL_LIFTING.value,
        "expected_barrier_condition": BarrierCondition.FAILED,
        "category": "Crane Swing Path",
    },
    # ── 21. Minor Vehicle Parking (SIF: NO) ──
    {
        "case_id": "EVAL-021",
        "narrative": "Utility pickup truck parked 1 foot outside designated yellow parking bay line at base workshop.",
        "expected_sif": SifDecision.NO,
        "expected_lsr": LifeSavingRule.DRIVING.value,
        "expected_barrier_condition": BarrierCondition.INTACT,
        "category": "Non-Moving Parking Issue",
    },
    # ── 22. Valve Handwheel Loose (SIF: NO) ──
    {
        "case_id": "EVAL-022",
        "narrative": "Water utility wash line valve handwheel felt loose when turning off garden hose; secured nut with wrench.",
        "expected_sif": SifDecision.NO,
        "expected_lsr": "UNKNOWN",
        "expected_barrier_condition": BarrierCondition.INTACT,
        "category": "Low-Pressure Utility Maintenance",
    },
    # ── 23. Counterfactual Pair A: EXPOSED (SIF: YES) ──
    {
        "case_id": "EVAL-023",
        "narrative": "High-pressure test manifold pressure relief valve lifted at 250 bar discharging directly toward test technician standing 2 feet away.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.LINE_OF_FIRE.value,
        "expected_barrier_condition": BarrierCondition.FAILED,
        "category": "Counterfactual: Worker in Discharge Path",
    },
    # ── 24. Counterfactual Pair B: ISOLATED/NO EXPOSURE (SIF: NO / LOW) ──
    {
        "case_id": "EVAL-024",
        "narrative": "High-pressure test manifold pressure relief valve lifted at 250 bar discharging safely into unoccupied blast bunker while all personnel monitored remotely from control van.",
        "expected_sif": SifDecision.NO,
        "expected_lsr": LifeSavingRule.LINE_OF_FIRE.value,
        "expected_barrier_condition": BarrierCondition.INTACT,
        "category": "Counterfactual: Blast Bunker Barrier Intact",
    },
    # ── 25. High Fall Risk from Ladder (SIF: YES) ──
    {
        "case_id": "EVAL-025",
        "narrative": "Painter overreached from untethered extension ladder positioned on oily steel grating at 6 meters elevation.",
        "expected_sif": SifDecision.YES,
        "expected_lsr": LifeSavingRule.WORKING_AT_HEIGHT.value,
        "expected_barrier_condition": BarrierCondition.FAILED,
        "category": "Elevated Ladder Unstable",
    },
]
