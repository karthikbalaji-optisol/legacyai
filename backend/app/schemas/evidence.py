from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EvidenceCategory(str, Enum):
    BUSINESS_RULE = "business_rule"
    VALIDATION = "validation"
    THRESHOLD = "threshold"
    WORKFLOW = "workflow"
    ROUTE = "route"
    AUTHORIZATION = "authorization"
    EXCEPTION_HANDLING = "exception_handling"
    DATABASE_OPERATION = "database_operation"
    EXTERNAL_CALL = "external_call"
    CONFIGURATION = "configuration"

class EvidenceRecord(BaseModel):
    id: str = Field(..., description="Stable deterministic evidence ID (e.g. ev_c4a8...)")
    repository_id: str
    relative_path: str
    symbol_name: str
    start_line: int
    end_line: int
    source_excerpt: str
    category: EvidenceCategory
    extraction_method: str = "ast_scanner"
    validation_status: str = "valid"
    threshold_operator: str | None = None
    threshold_value: str | None = None
    threshold_unit: str | None = None
    related_symbols: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DiscoveredSymbol(BaseModel):
    id: str
    name: str
    kind: str  # class, interface, method, controller, model, enum
    namespace: str | None = None
    relative_path: str
    start_line: int
    end_line: int
    roles: list[str] = Field(default_factory=list)
    route: str | None = None
    http_method: str | None = None
    parameters: list[str] = Field(default_factory=list)
    return_type: str | None = None
    calls: list[str] = Field(default_factory=list)

class MethodDependency(BaseModel):
    source_symbol: str
    target_symbol: str
    call_type: str = "direct"
    source_file: str
    line_number: int

class ScanSummary(BaseModel):
    total_files: int
    csharp_files: int
    total_lines_of_code: int
    controllers_count: int
    services_count: int
    models_count: int
    evidence_count: int
    business_rules_count: int
    routes_count: int
