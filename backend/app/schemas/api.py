from typing import Any

from pydantic import BaseModel, Field

from backend.app.schemas.brd import ReviewStatus
from backend.app.schemas.evidence import (
    ScanSummary,
)


class RepositoryCreateResponse(BaseModel):
    repository_id: str
    name: str
    file_count: int
    total_size_bytes: int
    created_at: str

class AnalysisStartResponse(BaseModel):
    analysis_id: str
    repository_id: str
    status: str
    message: str

class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    repository_id: str
    status: str  # pending, scanning, analyzing, validating, awaiting_review, approved, failed
    current_node: str | None = None
    progress_percentage: int
    error: str | None = None
    started_at: str
    completed_at: str | None = None
    scan_summary: ScanSummary | None = None
    validation_score: float | None = None
    review_status: ReviewStatus = ReviewStatus.PENDING

class RequirementUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    review_status: ReviewStatus | None = None
    reviewer_notes: str | None = None

class HumanReviewDecisionRequest(BaseModel):
    decision: ReviewStatus  # APPROVED, REJECTED, NEEDS_REVISION
    reviewer_name: str
    notes: str | None = None

class ImpactNode(BaseModel):
    id: str
    label: str
    node_type: str  # rule, method, service, requirement, acceptance_criteria
    details: dict[str, Any] = Field(default_factory=dict)

class ImpactEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None
    relationship: str  # implements, calls, validates, tests, depends_on
    confirmed: bool = True

class ImpactGraphResponse(BaseModel):
    analysis_id: str
    nodes: list[ImpactNode]
    edges: list[ImpactEdge]
