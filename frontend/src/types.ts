export type ReviewStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'NEEDS_REVISION';
export type ConfidenceCategory = 'HIGH' | 'MEDIUM' | 'LOW';
export type ClassificationType = 'OBSERVED' | 'INFERRED';

export interface AcceptanceCriteria {
  id: string;
  scenario: string;
  given: string;
  when: string;
  then: string;
}

export interface BusinessRule {
  id: string;
  title: string;
  description: string;
  supporting_evidence_ids: string[];
  threshold_operator?: string;
  threshold_value?: string;
  threshold_unit?: string;
  source_symbol: string;
  source_file: string;
  impacted_requirements: string[];
  confidence: ConfidenceCategory;
  classification: ClassificationType;
}

export interface FunctionalRequirement {
  id: string;
  title: string;
  description: string;
  category: string;
  supporting_evidence_ids: string[];
  acceptance_criteria: AcceptanceCriteria[];
  confidence: ConfidenceCategory;
  classification: ClassificationType;
  assumptions: string[];
  open_questions: string[];
  review_status: ReviewStatus;
  reviewer_notes?: string;
  implemented_by_symbols: string[];
}

export interface DiscoveredModule {
  name: string;
  description: string;
  source_directory: string;
  key_classes: string[];
  responsibilities: string[];
}

export interface ActorRole {
  role_name: string;
  description: string;
  source_reference?: string;
  discovered_permissions: string[];
}

export interface WorkflowStep {
  step_number: number;
  name: string;
  actor: string;
  action: string;
  decision_condition?: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  trigger: string;
  steps: WorkflowStep[];
  terminal_states: string[];
}

export interface OpenQuestion {
  id: string;
  topic: string;
  question: string;
  context_code_reference: string;
  stakeholder_target: string;
  urgency: string;
}

export interface ValidationResult {
  total_requirements: number;
  requirements_with_valid_evidence: number;
  missing_evidence_count: number;
  evidence_validation_percentage: number;
  unsupported_claims_flagged: number;
  validation_passed: boolean;
  warnings: string[];
  validation_errors: string[];
}

export interface BRDDocument {
  id: string;
  analysis_id: string;
  version: number;
  project_title: string;
  target_framework: string;
  executive_summary: string;
  business_objectives: string[];
  application_scope: string;
  modules: DiscoveredModule[];
  actors_and_roles: ActorRole[];
  functional_requirements: FunctionalRequirement[];
  business_rules: BusinessRule[];
  workflows: Workflow[];
  open_questions: OpenQuestion[];
  validation_results?: ValidationResult;
  review_status: ReviewStatus;
  overall_confidence: ConfidenceCategory;
  generated_at: string;
  model_provider_used: string;
}

export interface EvidenceRecord {
  id: string;
  repository_id: string;
  relative_path: string;
  symbol_name: string;
  start_line: number;
  end_line: number;
  source_excerpt: string;
  category: string;
  extraction_method: string;
  validation_status: string;
  metadata: Record<string, any>;
}

export interface DiscoveredSymbol {
  id: string;
  name: string;
  kind: string;
  namespace?: string;
  relative_path: string;
  start_line: number;
  end_line: number;
  roles: string[];
  route?: string;
  parameters: string[];
  return_type?: string;
}

export interface ScanSummary {
  total_files: number;
  csharp_files: number;
  total_lines_of_code: number;
  controllers_count: number;
  services_count: number;
  models_count: number;
  evidence_count: number;
  business_rules_count: number;
  routes_count: number;
}

export interface AnalysisStatus {
  analysis_id: string;
  repository_id: string;
  status: string;
  current_node?: string;
  progress_percentage: number;
  error?: string;
  started_at: string;
  completed_at?: string;
  scan_summary?: ScanSummary;
  validation_score?: number;
  review_status: ReviewStatus;
}

export interface ImpactNode {
  id: string;
  label: string;
  node_type: string;
  details: Record<string, any>;
}

export interface ImpactEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  relationship: string;
  confirmed: boolean;
}

export interface ImpactGraph {
  analysis_id: string;
  nodes: ImpactNode[];
  edges: ImpactEdge[];
}

export interface AnalysisStreamEvent {
  analysis_id: string;
  type: 'step_progress' | 'log' | 'completed' | 'failed';
  node: string;
  step: number;
  total_steps: number;
  progress_percentage: number;
  status: string;
  message: string;
  badge?: string;
  timestamp: string;
  details?: Record<string, any>;
}

export interface AgentLog {
  id: string;
  timestamp: string;
  node: string;
  message: string;
  badge: string;
  type: 'info' | 'success' | 'warning' | 'error';
  step?: number;
}
