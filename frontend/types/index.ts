export type EvidenceStatus = 'EXPLICIT' | 'INFERRED' | 'UNKNOWN';
export type SifDecision = 'YES' | 'NO' | 'UNCERTAIN';
export type BarrierCondition = 'INTACT' | 'DEGRADED' | 'FAILED' | 'ABSENT' | 'UNKNOWN';
export type PriorityLevel = 'ROUTINE' | 'SAFETY_REVIEW' | 'HIGH_PRIORITY_SIF_FPI_PRECURSOR' | 'CRITICAL' | 'UNCERTAIN';
export type AnalysisStatus = 'NOT_ANALYZED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'NEEDS_REVIEW';
export type ScreeningStatus = 'NOT_SCREENED' | 'SCREENING' | 'SCREENED' | 'SCREENING_FAILED';

export interface RuleTrigger {
  rule_id: string;
  rule_name: string;
  reason_code: string;
  description: string;
  signal_strength: number;
  evidence_refs: string[];
}

export interface ScreeningSignals {
  mechanism_signal: number;
  exposure_signal: number;
  barrier_signal: number;
  consequence_signal: number;
  evidence_signal: number;
}

/** Phase 4: SIF / FPI Screening Decision Result */
export interface SifScreeningResult {
  report_id: string;
  sif_fpi_potential: SifDecision;
  sif_confidence: number;
  screening_status: ScreeningStatus;
  screening_reason: string;
  reason_codes: string[];
  rule_ids_triggered: string[];
  contributing_factors: string[];
  signals: ScreeningSignals;
  rules_triggered: RuleTrigger[];
  screening_version: string;
  screened_at?: string;
  review_required: boolean;
  review_reason?: string;
}

export type LifeSavingRule =
  | 'Bypassing Safety Controls'
  | 'Confined Space'
  | 'Driving'
  | 'Energy Isolation'
  | 'Hot Work'
  | 'Line of Fire'
  | 'Safe Mechanical Lifting'
  | 'Work Authorisation'
  | 'Working at Height'
  | 'UNKNOWN';

export type ComponentStatus = 'AVAILABLE' | 'NOT_YET_AVAILABLE' | 'UNKNOWN';

export interface LsrMappingResult {
  report_id: string;
  primary_life_saving_rule: LifeSavingRule;
  secondary_life_saving_rules: LifeSavingRule[];
  lsr_confidence: number;
  lsr_evidence?: string;
  lsr_evidence_status: EvidenceStatus;
  lsr_reason: string;
  lsr_mapping_version: string;
  mapped_at?: string;
}

export interface PriorityComponent {
  name: string;
  score?: number;
  weight: number;
  status: ComponentStatus;
  description: string;
}

export interface PriorityResult {
  report_id: string;
  priority_score: number;
  priority_level: PriorityLevel;
  priority_reason_codes: string[];
  priority_override: boolean;
  override_reason?: string;
  components: PriorityComponent[];
  why_prioritized: string[];
  unavailable_components: string[];
  priority_version: string;
  calculated_at?: string;
}

export type EscalationBand = 'LOW' | 'WATCH' | 'REVIEW' | 'HIGH' | 'CRITICAL_PATTERN';
export type SimilarityBand = 'HIGHLY_SIMILAR' | 'STRONGLY_RELATED' | 'POTENTIALLY_RELATED' | 'WEAK';

export interface SharedMechanismDetails {
  shared_activity?: string;
  shared_hazard?: string;
  shared_equipment?: string;
  shared_exposure?: string;
  shared_barrier?: string;
  shared_lsr?: string;
  shared_asset?: string;
  shared_functional_location?: string;
  days_between?: number;
  semantic_similarity: number;
  mechanism_similarity: number;
  structured_similarity: number;
}

export interface SimilarReportItem {
  report_id: string;
  report_date?: string;
  site?: string;
  functional_location?: string;
  narrative_snippet: string;
  fixed_short_description?: string;
  sif_fpi_potential?: SifDecision;
  primary_life_saving_rule?: string;
  priority_level?: PriorityLevel;
  similarity_score: number;
  similarity_band: SimilarityBand;
  shared_details: SharedMechanismDetails;
}

export interface SimilarReportResponse {
  target_report_id: string;
  total_found: number;
  similar_reports: SimilarReportItem[];
}

export interface TimelineEvent {
  report_id: string;
  report_date?: string;
  days_from_first: number;
  title: string;
  narrative_snippet: string;
  hazard?: string;
  barrier_condition?: string;
  exposure?: string;
  sif_fpi_potential?: SifDecision;
}

export interface ClusterMemberResponse {
  report_id: string;
  report_date?: string;
  site?: string;
  functional_location?: string;
  short_description?: string;
  sif_fpi_potential?: SifDecision;
  primary_life_saving_rule?: string;
  priority_level?: PriorityLevel;
  similarity_to_cluster: number;
}

export interface ClusterResponse {
  id: number;
  cluster_name: string;
  common_mechanism?: string;
  common_asset?: string;
  common_hazard?: string;
  common_activity?: string;
  common_equipment?: string;
  common_barrier?: string;
  common_lsr?: string;
  recurrence_count: number;
  escalation_score: number;
  escalation_band: EscalationBand;
  first_seen?: string;
  last_seen?: string;
  created_at: string;
  updated_at: string;
}

export interface FullIntelligenceResult {
  report_id: string;
  extraction?: SafetyAnalysisResult;
  sif_screening?: SifScreeningResult;
  lsr_mapping?: LsrMappingResult;
  priority?: PriorityResult;
}

export interface ClusterDetailResponse extends ClusterResponse {
  members: ClusterMemberResponse[];
  timeline: TimelineEvent[];
  why_escalating: string[];
  systemic_pattern?: string;
}

export interface EvidenceItem {
  id: number;
  report_id: string;
  analysis_id?: number;
  field_name: string;
  evidence_text: string;
  start_offset?: number;
  end_offset?: number;
  evidence_status: EvidenceStatus;
  confidence: number;
  created_at: string;
}

/** Phase 3: Full AI Safety Analysis result (no SIF/FPI classification — that is Phase 4+) */
export interface SafetyAnalysisResult {
  report_id: string;
  analysis_status: AnalysisStatus;
  analysis_version: string;
  model_name?: string;
  provider_name?: string;
  analyzed_at?: string;
  is_mock: boolean;

  activity?: string;
  activity_evidence?: string;
  activity_evidence_status?: EvidenceStatus;
  activity_confidence?: number;

  equipment?: string;
  equipment_evidence?: string;
  equipment_evidence_status?: EvidenceStatus;
  equipment_confidence?: number;

  hazard?: string;
  hazard_evidence?: string;
  hazard_evidence_status?: EvidenceStatus;
  hazard_confidence?: number;

  energy_source?: string;
  energy_source_evidence?: string;
  energy_source_evidence_status?: EvidenceStatus;
  energy_source_confidence?: number;

  exposure?: string;
  exposure_evidence?: string;
  exposure_evidence_status?: EvidenceStatus;
  exposure_confidence?: number;

  exposure_location?: string;
  exposure_location_evidence?: string;
  exposure_location_evidence_status?: EvidenceStatus;
  exposure_location_confidence?: number;

  barrier?: string;
  barrier_evidence?: string;
  barrier_evidence_status?: EvidenceStatus;
  barrier_confidence?: number;

  barrier_condition?: string;
  barrier_condition_evidence?: string;
  barrier_condition_evidence_status?: EvidenceStatus;
  barrier_condition_confidence?: number;

  potential_consequence?: string;
  potential_consequence_evidence?: string;
  potential_consequence_evidence_status?: EvidenceStatus;
  potential_consequence_confidence?: number;

  suggested_actions?: string;
  suggested_actions_reasoning?: string;

  evidence_items: EvidenceItem[];
}


export interface SourceReport {
  id: number;
  report_id: string;
  source_system_id?: string;
  report_date?: string;
  report_time?: string;
  site?: string;
  unit?: string;
  shift?: string;
  functional_location?: string;
  functional_location_description?: string;
  item_no?: string;
  incident_type?: string;
  incident_sub_type?: string;
  incident_cause?: string;
  fixed_short_description?: string;
  line_item?: string;
  narrative: string;
  corrective_action?: string;
  preventive_action?: string;
  man_hours?: number;
  lost_time?: number;
  operational_time_lost?: number;
  financial_implication?: number;
  currency?: string;
  affected_person_type?: string;
  employee_or_contractor?: string;
  designation?: string;
  contractor_name?: string;
  actual_outcome?: string;
  provenance?: string;
  analysis_status?: AnalysisStatus;
  sif_fpi_potential?: SifDecision;
  screening_status?: ScreeningStatus;
  primary_life_saving_rule?: string;
  priority_score?: number;
  priority_level?: PriorityLevel;
  created_at: string;
  updated_at: string;
}

export interface SafetyAnalysis {
  id: number;
  report_id: string;
  activity?: string;
  equipment?: string;
  hazard?: string;
  energy_source?: string;
  exposure?: string;
  exposure_location?: string;
  barrier?: string;
  barrier_condition?: BarrierCondition;
  potential_consequence?: string;
  sif_fpi_potential?: SifDecision;
  sif_confidence?: number;
  evidence_status?: EvidenceStatus;
  evidence_span?: string;
  reason_code?: string;
  life_saving_rule?: string;
  novelty_score?: number;
  review_required: boolean;
  review_reason?: string;
  sif_evidence_score?: number;
  barrier_score?: number;
  recurrence_score?: number;
  escalation_score?: number;
  priority_score?: number;
  priority_level?: PriorityLevel;
  created_at: string;
  updated_at: string;
}

export interface PrecursorCluster {
  id: string;
  name: string;
  mechanism: string;
  site: string;
  report_count: number;
  sif_fpi_count: number;
  escalation_score: number;
  escalation_band: 'LOW' | 'WATCH' | 'REVIEW' | 'HIGH' | 'CRITICAL';
  life_saving_rule?: string;
  barrier?: string;
  first_seen: string;
  last_seen: string;
}

// ── Phase 7: Dashboard Interfaces ──────────────────────────────────────────

export interface DashboardSummary {
  total_reports: number;
  analyzed_reports: number;
  sif_yes: number;
  sif_no: number;
  sif_uncertain: number;
  high_priority: number;
  critical: number;
  escalating_clusters: number;
  active_clusters: number;
  sif_share_pct?: number;
  comparison_period_label?: string;
  total_reports_change_pct?: number;
  sif_yes_change_pct?: number;
  high_priority_change_pct?: number;
}

export interface TrendPoint {
  date: string;
  total_reports: number;
  sif_yes: number;
  sif_uncertain: number;
  high_priority: number;
}

export interface SiteSummary {
  site: string;
  report_count: number;
  sif_count: number;
  sif_uncertain_count: number;
  high_priority_count: number;
  critical_count: number;
  cluster_count: number;
  escalating_cluster_count: number;
  total_man_hours: number;
  precursor_density?: number;
  precursor_density_unit?: string;
  precursor_concentration_pct: number;
  has_valid_man_hours: boolean;
  barrier_weakness_count: number;
}

export interface ActivitySummary {
  activity: string;
  report_count: number;
  sif_count: number;
  high_priority_count: number;
  cluster_count: number;
  escalation_score: number;
  common_hazard?: string;
  common_barrier?: string;
  common_lsr?: string;
}

export interface HazardSummary {
  hazard: string;
  report_count: number;
  sif_count: number;
  high_priority_count: number;
  associated_lsrs: string[];
  associated_barriers: string[];
  associated_clusters: string[];
}

export interface LsrSummary {
  lsr: string;
  mapped_count: number;
  sif_yes_count: number;
  high_priority_count: number;
  critical_count: number;
  escalating_cluster_count: number;
}

export interface BarrierSummary {
  barrier: string;
  total_mentions: number;
  intact_count: number;
  degraded_count: number;
  failed_count: number;
  absent_count: number;
  unknown_count: number;
  sif_count: number;
  high_priority_count: number;
  escalating_cluster_count: number;
  weakness_score: number;
}

export interface RecurringMechanismSummary {
  mechanism_name: string;
  report_count: number;
  sif_count: number;
  cluster_count: number;
  escalation_score: number;
  shared_asset?: string;
  shared_barrier?: string;
  lsr?: string;
}

export interface RecentAlertSummary {
  id: number;
  created_at: string;
  cluster_id?: number;
  cluster_name?: string;
  escalation_score: number;
  priority: string;
  mechanism?: string;
  location?: string;
  reason: string;
}

export interface DataQualitySummary {
  total_imported: number;
  analyzed_count: number;
  not_analyzed_count: number;
  failed_analysis_count: number;
  sif_screened_count: number;
  lsr_mapped_count: number;
  embedding_coverage_pct: number;
  clustered_reports_count: number;
  field_completeness: Record<string, number>;
}

// ── Phase 8: HSE Review & Human-in-the-Loop Interfaces ─────────────────────

export type ReviewStatus = 'UNREVIEWED' | 'IN_REVIEW' | 'REVIEWED' | 'NEEDS_MORE_INFORMATION';
export type ReviewDecision = 'CONFIRM_AI' | 'OVERRIDE' | 'REJECT' | 'NEEDS_MORE_INFORMATION';
export type RejectionReason =
  | 'FALSE_POSITIVE'
  | 'INSUFFICIENT_EVIDENCE'
  | 'DUPLICATE_OBSERVATION'
  | 'INCORRECT_INTERPRETATION'
  | 'NOT_A_SIF_PRECURSOR'
  | 'OTHER';

export interface ReviewResponse {
  id: number;
  report_id: string;
  reviewer_id: string;
  review_status: ReviewStatus;
  review_decision: ReviewDecision;
  original_ai_sif_potential?: string;
  original_ai_lsr?: string;
  original_ai_priority?: string;
  final_sif_potential?: string;
  final_lsr?: string;
  final_priority?: string;
  reviewer_comment?: string;
  rejection_reason?: string;
  missing_information_fields: string[];
  reviewed_at: string;
  created_at: string;
}

export interface ReviewHistoryItem {
  id: number;
  reviewer_id: string;
  review_decision: string;
  original_ai_sif_potential?: string;
  final_sif_potential?: string;
  original_ai_lsr?: string;
  final_lsr?: string;
  original_ai_priority?: string;
  final_priority?: string;
  reviewer_comment?: string;
  rejection_reason?: string;
  missing_information_fields: string[];
  reviewed_at: string;
}

export interface ReviewQueueItem {
  report_id: string;
  report_date?: string;
  site?: string;
  functional_location?: string;
  activity?: string;
  hazard?: string;
  narrative_snippet: string;
  ai_sif_potential?: string;
  ai_lsr?: string;
  ai_priority_level?: string;
  ai_priority_score?: number;
  review_status: ReviewStatus;
  latest_decision?: string;
  review_required: boolean;
  review_reason?: string;
  escalation_score?: number;
}

export interface ReviewQueueResponse {
  total: number;
  items: ReviewQueueItem[];
}

export interface ReviewAnalyticsSummary {
  total_in_scope: number;
  pending_review: number;
  total_reviewed: number;
  confirmed_count: number;
  overridden_count: number;
  rejected_count: number;
  needs_more_info_count: number;
}

export interface ConfusionMatrixData {
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
}

export interface LsrRuleMetric {
  rule: string;
  sample_count: number;
  correct_count: number;
  accuracy_pct: number;
}

export interface EvaluationRunResponse {
  id: number;
  dataset_name: string;
  dataset_version: string;
  pipeline_version: string;
  sample_count: number;
  precision: number;
  recall: number;
  f1: number;
  f2: number;
  pr_auc: number;
  confusion_matrix: ConfusionMatrixData;
  critical_misses: number;
  uncertain_count: number;
  uncertain_pct: number;
  lsr_accuracy: number;
  per_rule_metrics: LsrRuleMetric[];
  leakage_check_passed: boolean;
  robustness_score: number;
  run_timestamp: string;
}


