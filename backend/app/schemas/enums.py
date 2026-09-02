from enum import Enum


class EvidenceStatus(str, Enum):
    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class AnalysisStatus(str, Enum):
    NOT_ANALYZED = "NOT_ANALYZED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ScreeningStatus(str, Enum):
    NOT_SCREENED = "NOT_SCREENED"
    SCREENING = "SCREENING"
    SCREENED = "SCREENED"
    SCREENING_FAILED = "SCREENING_FAILED"


class SifDecision(str, Enum):
    YES = "YES"
    NO = "NO"
    UNCERTAIN = "UNCERTAIN"


class BarrierCondition(str, Enum):
    INTACT = "INTACT"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    ABSENT = "ABSENT"
    UNKNOWN = "UNKNOWN"


class PriorityLevel(str, Enum):
    ROUTINE = "ROUTINE"
    SAFETY_REVIEW = "SAFETY_REVIEW"
    HIGH_PRIORITY_SIF_FPI_PRECURSOR = "HIGH_PRIORITY_SIF_FPI_PRECURSOR"
    CRITICAL = "CRITICAL"
    UNCERTAIN = "UNCERTAIN"


class LifeSavingRule(str, Enum):
    BYPASSING_SAFETY_CONTROLS = "Bypassing Safety Controls"
    CONFINED_SPACE = "Confined Space"
    DRIVING = "Driving"
    ENERGY_ISOLATION = "Energy Isolation"
    HOT_WORK = "Hot Work"
    LINE_OF_FIRE = "Line of Fire"
    SAFE_MECHANICAL_LIFTING = "Safe Mechanical Lifting"
    WORK_AUTHORISATION = "Work Authorisation"
    WORKING_AT_HEIGHT = "Working at Height"
    UNKNOWN = "UNKNOWN"


OFFICIAL_LIFE_SAVING_RULES = [
    LifeSavingRule.BYPASSING_SAFETY_CONTROLS.value,
    LifeSavingRule.CONFINED_SPACE.value,
    LifeSavingRule.DRIVING.value,
    LifeSavingRule.ENERGY_ISOLATION.value,
    LifeSavingRule.HOT_WORK.value,
    LifeSavingRule.LINE_OF_FIRE.value,
    LifeSavingRule.SAFE_MECHANICAL_LIFTING.value,
    LifeSavingRule.WORK_AUTHORISATION.value,
    LifeSavingRule.WORKING_AT_HEIGHT.value,
]


class ComponentStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_YET_AVAILABLE = "NOT_YET_AVAILABLE"
    UNKNOWN = "UNKNOWN"


class EscalationBand(str, Enum):
    LOW = "LOW"                     # 0-29
    WATCH = "WATCH"                 # 30-49
    REVIEW = "REVIEW"               # 50-69
    HIGH = "HIGH"                   # 70-84
    CRITICAL_PATTERN = "CRITICAL_PATTERN"  # 85-100


class SimilarityBand(str, Enum):
    HIGHLY_SIMILAR = "HIGHLY_SIMILAR"        # 0.85 - 1.00
    STRONGLY_RELATED = "STRONGLY_RELATED"    # 0.70 - 0.84
    POTENTIALLY_RELATED = "POTENTIALLY_RELATED" # 0.50 - 0.69
    WEAK = "WEAK"                            # 0.00 - 0.49


class EnergySource(str, Enum):
    MECHANICAL = "MECHANICAL"
    KINETIC = "KINETIC"
    GRAVITATIONAL = "GRAVITATIONAL"
    PRESSURE = "PRESSURE"
    ELECTRICAL = "ELECTRICAL"
    THERMAL = "THERMAL"
    CHEMICAL = "CHEMICAL"
    HYDROCARBON = "HYDROCARBON"
    STORED_ENERGY = "STORED_ENERGY"
    VEHICLE_MOTION = "VEHICLE_MOTION"
    UNKNOWN = "UNKNOWN"


class BarrierType(str, Enum):
    ISOLATION = "isolation"
    GUARDING = "guarding"
    EXCLUSION_ZONE = "exclusion zone"
    SAFE_POSITIONING = "safe positioning"
    LIFTING_CONTROL = "lifting control"
    INSPECTION = "inspection"
    MAINTENANCE = "maintenance"
    PPE = "PPE"
    SOP = "SOP"
    PERMIT_WORK_AUTHORISATION = "permit/work authorisation"
    WARNING_SYSTEM = "warning system"
    SUPERVISION = "supervision"
    HOUSEKEEPING = "housekeeping"
    EQUIPMENT_SELECTION = "equipment selection"


class AlertType(str, Enum):
    SIF_REVIEW = "SIF_REVIEW"
    PATTERN_ESCALATION = "PATTERN_ESCALATION"
    BARRIER_WEAKNESS = "BARRIER_WEAKNESS"
    NOVEL_CASE = "NOVEL_CASE"
    REPORTING_ANOMALY = "REPORTING_ANOMALY"


class ProvenanceType(str, Enum):
    SYNTHETIC = "SYNTHETIC"
    REFERENCE = "REFERENCE"
    OIL_EXPORT = "OIL_EXPORT"
    OTHER = "OTHER"


class ReviewStatus(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    IN_REVIEW = "IN_REVIEW"
    REVIEWED = "REVIEWED"
    NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION"


class ReviewDecision(str, Enum):
    CONFIRM_AI = "CONFIRM_AI"
    OVERRIDE = "OVERRIDE"
    REJECT = "REJECT"
    NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION"


class RejectionReason(str, Enum):
    FALSE_POSITIVE = "FALSE_POSITIVE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    DUPLICATE_OBSERVATION = "DUPLICATE_OBSERVATION"
    INCORRECT_INTERPRETATION = "INCORRECT_INTERPRETATION"
    NOT_A_SIF_PRECURSOR = "NOT_A_SIF_PRECURSOR"
    OTHER = "OTHER"

