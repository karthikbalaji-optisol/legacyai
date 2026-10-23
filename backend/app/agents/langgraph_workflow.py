from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from backend.app.agents.bedrock_provider import get_model_provider
from backend.app.code_intelligence.csharp_scanner import CSharpScanner
from backend.app.code_intelligence.evidence_validator import DeterministicEvidenceValidator
from backend.app.core.logging import logger
from backend.app.schemas.brd import (
    BRDDocument,
    BusinessRule,
    FunctionalRequirement,
    ReviewStatus,
    ValidationResult,
)
from backend.app.schemas.evidence import (
    DiscoveredSymbol,
    EvidenceRecord,
    MethodDependency,
    ScanSummary,
)


class AnalysisState(TypedDict, total=False):
    analysis_id: str
    repository_id: str
    repo_path: str
    scan_summary: Optional[ScanSummary]
    discovered_symbols: List[DiscoveredSymbol]
    evidence_records: List[EvidenceRecord]
    dependencies: List[MethodDependency]
    business_capabilities: List[str]
    candidate_requirements: List[FunctionalRequirement]
    business_rules: List[BusinessRule]
    workflows: List[Any]
    open_questions: List[Any]
    validation_results: Optional[ValidationResult]
    brd_document: Optional[BRDDocument]
    errors: List[str]
    review_status: ReviewStatus
    current_node: str

def node_validate_repository(state: AnalysisState) -> Dict[str, Any]:
    repo_path = Path(state["repo_path"])
    logger.info(f"[{state['analysis_id']}] Validating repository at: {repo_path}")
    if not repo_path.exists() or not repo_path.is_dir():
        return {
            "errors": [f"Repository directory does not exist: {repo_path}"],
            "current_node": "validate_repository",
            "review_status": ReviewStatus.REJECTED
        }
    return {"current_node": "validate_repository", "errors": []}

def node_scan_source_code(state: AnalysisState) -> Dict[str, Any]:
    repo_path = Path(state["repo_path"])
    repo_id = state["repository_id"]
    scanner = CSharpScanner(repo_id, repo_path)
    summary, symbols, evidence, deps = scanner.scan_all()
    return {
        "scan_summary": summary,
        "discovered_symbols": symbols,
        "evidence_records": evidence,
        "dependencies": deps,
        "current_node": "scan_source_code",
    }

def node_build_evidence_index(state: AnalysisState) -> Dict[str, Any]:
    return {"current_node": "build_evidence_index"}

def node_extract_business_capabilities(state: AnalysisState) -> Dict[str, Any]:
    capabilities = [
        "Order Intake & Multi-Stage Validation",
        "Dynamic Customer Tier & Volume Discounting",
        "Credit Limit Verification & Risk Assessment",
        "Third-Party Payment Gateway Integration",
        "Role-Based Order Cancellation & Privilege Control"
    ]
    return {
        "business_capabilities": capabilities,
        "current_node": "extract_business_capabilities"
    }

def node_extract_business_rules(state: AnalysisState) -> Dict[str, Any]:
    return {"current_node": "extract_business_rules"}

def node_generate_functional_requirements(state: AnalysisState) -> Dict[str, Any]:
    return {"current_node": "generate_functional_requirements"}

def node_validate_evidence(state: AnalysisState) -> Dict[str, Any]:
    return {"current_node": "validate_evidence"}

def node_identify_gaps_and_questions(state: AnalysisState) -> Dict[str, Any]:
    return {"current_node": "identify_gaps_and_questions"}

def node_generate_brd(state: AnalysisState) -> Dict[str, Any]:
    provider = get_model_provider()
    repo_path = Path(state["repo_path"])
    evidence = state.get("evidence_records", [])
    symbols = state.get("discovered_symbols", [])
    summary = state.get("scan_summary")

    brd = provider.generate_brd(
        analysis_id=state["analysis_id"],
        summary=summary,
        symbols=symbols,
        evidence=evidence
    )

    ev_index = {e.id: e for e in evidence}
    validator = DeterministicEvidenceValidator(repo_path, ev_index)
    validated_brd, val_results = validator.validate_brd(brd)

    return {
        "brd_document": validated_brd,
        "validation_results": val_results,
        "current_node": "generate_brd"
    }

def node_await_human_review(state: AnalysisState) -> Dict[str, Any]:
    return {
        "review_status": ReviewStatus.PENDING,
        "current_node": "await_human_review"
    }

def node_export_approved_document(state: AnalysisState) -> Dict[str, Any]:
    return {
        "current_node": "export_approved_document"
    }

def route_after_validation(state: AnalysisState) -> str:
    if state.get("errors"):
        return END
    return "scan_source_code"

def build_analysis_workflow() -> Any:
    workflow = StateGraph(AnalysisState)

    workflow.add_node("validate_repository", node_validate_repository)
    workflow.add_node("scan_source_code", node_scan_source_code)
    workflow.add_node("build_evidence_index", node_build_evidence_index)
    workflow.add_node("extract_business_capabilities", node_extract_business_capabilities)
    workflow.add_node("extract_business_rules", node_extract_business_rules)
    workflow.add_node("generate_functional_requirements", node_generate_functional_requirements)
    workflow.add_node("validate_evidence", node_validate_evidence)
    workflow.add_node("identify_gaps_and_questions", node_identify_gaps_and_questions)
    workflow.add_node("generate_brd", node_generate_brd)
    workflow.add_node("await_human_review", node_await_human_review)
    workflow.add_node("export_approved_document", node_export_approved_document)

    workflow.set_entry_point("validate_repository")
    workflow.add_conditional_edges(
        "validate_repository",
        route_after_validation,
        {
            "scan_source_code": "scan_source_code",
            END: END
        }
    )
    workflow.add_edge("scan_source_code", "build_evidence_index")
    workflow.add_edge("build_evidence_index", "extract_business_capabilities")
    workflow.add_edge("extract_business_capabilities", "extract_business_rules")
    workflow.add_edge("extract_business_rules", "generate_functional_requirements")
    workflow.add_edge("generate_functional_requirements", "validate_evidence")
    workflow.add_edge("validate_evidence", "identify_gaps_and_questions")
    workflow.add_edge("identify_gaps_and_questions", "generate_brd")
    workflow.add_edge("generate_brd", "await_human_review")
    workflow.add_edge("await_human_review", "export_approved_document")
    workflow.add_edge("export_approved_document", END)

    return workflow.compile()

