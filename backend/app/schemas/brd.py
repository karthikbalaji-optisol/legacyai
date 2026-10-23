from enum import Enum

from pydantic import BaseModel, Field


class ConfidenceCategory(str, Enum):
    HIGH = "HIGH"          # Multiple verifiable code lines & tests directly matching rule
    MEDIUM = "MEDIUM"      # Clear code evidence, but business context partly inferred
    LOW = "LOW"            # Inferred pattern or ambiguous threshold

class ClassificationType(str, Enum):
    OBSERVED = "OBSERVED"   # Direct application code behavior explicitly visible in source
    INFERRED = "INFERRED"   # Inferred business intent or domain assumption

class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVISION = "NEEDS_REVISION"

class AcceptanceCriteria(BaseModel):
    id: str
    scenario: str
    given: str
    when: str
    then: str

class BusinessRule(BaseModel):
    id: str = Field(..., description="e.g. BR-001")
    title: str
    description: str
    supporting_evidence_ids: list[str]
    threshold_operator: str | None = None
    threshold_value: str | None = None
    threshold_unit: str | None = None
    source_symbol: str
    source_file: str
    impacted_requirements: list[str] = Field(default_factory=list)
    confidence: ConfidenceCategory = ConfidenceCategory.HIGH
    classification: ClassificationType = ClassificationType.OBSERVED

class FunctionalRequirement(BaseModel):
    id: str = Field(..., description="e.g. FR-001")
    title: str
    description: str
    category: str  # Order Management, Pricing & Discounts, Compliance, Security
    supporting_evidence_ids: list[str]
    acceptance_criteria: list[AcceptanceCriteria] = Field(default_factory=list)
    confidence: ConfidenceCategory = ConfidenceCategory.HIGH
    classification: ClassificationType = ClassificationType.OBSERVED
    assumptions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviewer_notes: str | None = None
    implemented_by_symbols: list[str] = Field(default_factory=list)

class WorkflowStep(BaseModel):
    step_number: int
    name: str
    actor: str
    action: str
    decision_condition: str | None = None
    next_step_on_success: int | None = None
    next_step_on_failure: int | None = None
    supporting_evidence_id: str | None = None

class Workflow(BaseModel):
    id: str
    name: str
    description: str
    trigger: str
    steps: list[WorkflowStep]
    terminal_states: list[str]

class OpenQuestion(BaseModel):
    id: str
    topic: str
    question: str
    context_code_reference: str
    stakeholder_target: str  # Business Analyst, Compliance Officer, Finance, Architect
    urgency: str = "Medium"  # High, Medium, Low

class ActorRole(BaseModel):
    role_name: str
    description: str
    source_reference: str | None = None
    discovered_permissions: list[str] = Field(default_factory=list)

class DiscoveredModule(BaseModel):
    name: str
    description: str
    source_directory: str
    key_classes: list[str]
    responsibilities: list[str]

class ValidationResult(BaseModel):
    total_requirements: int
    requirements_with_valid_evidence: int
    missing_evidence_count: int
    evidence_validation_percentage: float
    unsupported_claims_flagged: int
    validation_passed: bool
    warnings: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)

class BRDDocument(BaseModel):
    id: str
    analysis_id: str
    version: int = 1
    project_title: str
    target_framework: str = ".NET 8.0 / ASP.NET Web API"
    executive_summary: str
    business_objectives: list[str]
    application_scope: str
    modules: list[DiscoveredModule] = Field(default_factory=list)
    actors_and_roles: list[ActorRole] = Field(default_factory=list)
    functional_requirements: list[FunctionalRequirement] = Field(default_factory=list)
    business_rules: list[BusinessRule] = Field(default_factory=list)
    workflows: list[Workflow] = Field(default_factory=list)
    exceptions_and_edge_cases: list[dict[str, str]] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)
    validation_results: ValidationResult | None = None
    review_status: ReviewStatus = ReviewStatus.PENDING
    overall_confidence: ConfidenceCategory = ConfidenceCategory.HIGH
    generated_at: str
    model_provider_used: str = "Amazon Bedrock (Claude 3 Sonnet)"
