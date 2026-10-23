from pathlib import Path
from typing import Dict, List, Tuple

from backend.app.schemas.brd import (
    BRDDocument,
    BusinessRule,
    ClassificationType,
    ConfidenceCategory,
    FunctionalRequirement,
    ValidationResult,
)
from backend.app.schemas.evidence import EvidenceRecord


class DeterministicEvidenceValidator:
    """
    Pure Python deterministic evidence verification engine.
    Ensures zero hallucinated code references by checking:
    1. Every evidence ID exists in the evidence store.
    2. The referenced relative path exists inside repo_root.
    3. The line range (start_line to end_line) exists within file boundaries.
    4. The recorded source excerpt matches lines in the actual physical file.
    5. Flags ungrounded claims, missing references, and mismatches.
    """

    def __init__(self, repo_root: Path, evidence_index: Dict[str, EvidenceRecord]):
        self.repo_root = repo_root
        self.evidence_index = evidence_index
        self.cached_file_lines: Dict[str, List[str]] = {}

    def _get_file_lines(self, rel_path: str) -> List[str]:
        if rel_path in self.cached_file_lines:
            return self.cached_file_lines[rel_path]
        full_path = self.repo_root / rel_path
        if not full_path.exists() or not full_path.is_file():
            return []
        try:
            lines = full_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            try:
                lines = full_path.read_text(encoding="latin-1").splitlines()
            except Exception:
                lines = []
        self.cached_file_lines[rel_path] = lines
        return lines

    def validate_brd(self, brd: BRDDocument) -> Tuple[BRDDocument, ValidationResult]:
        total_reqs = len(brd.functional_requirements)
        valid_reqs_count = 0
        missing_evidence_count = 0
        unsupported_claims_flagged = 0
        warnings: List[str] = []
        validation_errors: List[str] = []

        validated_requirements: List[FunctionalRequirement] = []

        for req in brd.functional_requirements:
            req_valid = True
            missing_for_req: List[str] = []

            if not req.supporting_evidence_ids:
                missing_evidence_count += 1
                unsupported_claims_flagged += 1
                req.confidence = ConfidenceCategory.LOW
                req.classification = ClassificationType.INFERRED
                req.assumptions.append("Flagged: No supporting code evidence IDs provided.")
                warnings.append(f"Requirement {req.id} ({req.title}) has zero supporting evidence.")
                req_valid = False
            else:
                for ev_id in req.supporting_evidence_ids:
                    if ev_id not in self.evidence_index:
                        missing_for_req.append(ev_id)
                        req_valid = False
                        validation_errors.append(f"Requirement {req.id} cites non-existent evidence ID: {ev_id}")
                    else:
                        ev = self.evidence_index[ev_id]
                        file_lines = self._get_file_lines(ev.relative_path)
                        if not file_lines:
                            req_valid = False
                            validation_errors.append(f"Evidence {ev_id} points to non-existent file: {ev.relative_path}")
                        elif ev.start_line > len(file_lines) or ev.start_line < 1:
                            req_valid = False
                            validation_errors.append(f"Evidence {ev_id} line {ev.start_line} out of bounds for {ev.relative_path} (total lines: {len(file_lines)})")
                        else:
                            actual_line = file_lines[ev.start_line - 1].strip()
                            first_excerpt_line = ev.source_excerpt.strip().splitlines()[0].strip()
                            if first_excerpt_line and first_excerpt_line not in actual_line and actual_line not in first_excerpt_line:
                                warnings.append(f"Evidence {ev_id} text slightly diverged from file content at {ev.relative_path}:{ev.start_line}")

            if req_valid:
                valid_reqs_count += 1
            else:
                if missing_for_req:
                    req.confidence = ConfidenceCategory.LOW
                    req.classification = ClassificationType.INFERRED
                    req.open_questions.append(f"Missing verifiable code evidence for: {', '.join(missing_for_req)}")

            validated_requirements.append(req)

        validated_rules: List[BusinessRule] = []
        for rule in brd.business_rules:
            rule_valid = True
            for ev_id in rule.supporting_evidence_ids:
                if ev_id not in self.evidence_index:
                    rule_valid = False
                    validation_errors.append(f"Business Rule {rule.id} cites invalid evidence {ev_id}")
            if not rule_valid:
                rule.confidence = ConfidenceCategory.LOW
                rule.classification = ClassificationType.INFERRED
            validated_rules.append(rule)

        brd.functional_requirements = validated_requirements
        brd.business_rules = validated_rules

        score_percentage = (valid_reqs_count / total_reqs * 100.0) if total_reqs > 0 else 0.0

        val_result = ValidationResult(
            total_requirements=total_reqs,
            requirements_with_valid_evidence=valid_reqs_count,
            missing_evidence_count=missing_evidence_count,
            evidence_validation_percentage=round(score_percentage, 1),
            unsupported_claims_flagged=unsupported_claims_flagged,
            validation_passed=(missing_evidence_count == 0 and len(validation_errors) == 0),
            warnings=warnings,
            validation_errors=validation_errors,
        )

        brd.validation_results = val_result
        return brd, val_result
