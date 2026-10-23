from pathlib import Path

from backend.app.agents.bedrock_provider import DeterministicDemoProvider
from backend.app.code_intelligence.csharp_scanner import CSharpScanner
from backend.app.code_intelligence.evidence_validator import (
    DeterministicEvidenceValidator,
)
from backend.app.schemas.brd import (
    ClassificationType,
    ConfidenceCategory,
    FunctionalRequirement,
)


def test_evidence_validator_validates_authentic_citations():
    sample_dir = Path(__file__).resolve().parent.parent / "samples" / "LegacyOrders"
    scanner = CSharpScanner("test_repo_val", sample_dir)
    summary, symbols, evidence, deps = scanner.scan_all()

    provider = DeterministicDemoProvider()
    brd = provider.generate_brd("test_analysis_val", summary, symbols, evidence)

    ev_index = {e.id: e for e in evidence}
    validator = DeterministicEvidenceValidator(sample_dir, ev_index)
    validated_brd, result = validator.validate_brd(brd)

    assert result.validation_passed is True
    assert result.evidence_validation_percentage == 100.0
    assert result.missing_evidence_count == 0
    assert result.unsupported_claims_flagged == 0

def test_evidence_validator_flags_hallucinated_citations():
    sample_dir = Path(__file__).resolve().parent.parent / "samples" / "LegacyOrders"
    scanner = CSharpScanner("test_repo_hallucinated", sample_dir)
    summary, symbols, evidence, deps = scanner.scan_all()

    provider = DeterministicDemoProvider()
    brd = provider.generate_brd("test_analysis_fake", summary, symbols, evidence)

    # Inject a fabricated requirement with non-existent evidence ID
    brd.functional_requirements.append(
        FunctionalRequirement(
            id="FR-999-FABRICATED",
            title="Invented Cryptocurrency Payment Feature",
            description="Customers can pay with Bitcoin.",
            category="Payments",
            supporting_evidence_ids=["ev_fake_nonexistent_id_9999"],
            confidence=ConfidenceCategory.HIGH,
            classification=ClassificationType.OBSERVED
        )
    )

    ev_index = {e.id: e for e in evidence}
    validator = DeterministicEvidenceValidator(sample_dir, ev_index)
    validated_brd, result = validator.validate_brd(brd)

    assert result.validation_passed is False
    assert result.evidence_validation_percentage < 100.0
    # Fabricated requirement should be demoted to LOW confidence and INFERRED classification
    flagged_req = next(r for r in validated_brd.functional_requirements if r.id == "FR-999-FABRICATED")
    assert flagged_req.confidence == ConfidenceCategory.LOW
    assert flagged_req.classification == ClassificationType.INFERRED
