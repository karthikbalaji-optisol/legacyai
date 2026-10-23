from pathlib import Path

from backend.app.code_intelligence.csharp_scanner import CSharpScanner
from backend.app.schemas.evidence import EvidenceCategory


def test_csharp_scanner_extracts_symbols_and_rules():
    sample_dir = Path(__file__).resolve().parent.parent / "samples" / "LegacyOrders"
    scanner = CSharpScanner("test_repo_1", sample_dir)
    summary, symbols, evidence, deps = scanner.scan_all()

    # 1. Verify Scan Summary
    assert summary.csharp_files >= 5
    assert summary.total_lines_of_code > 100
    assert summary.controllers_count >= 1
    assert summary.services_count >= 2
    assert summary.business_rules_count >= 5

    # 2. Verify Discovered Symbols
    symbol_names = [s.name for s in symbols]
    assert any("OrdersController" in n for n in symbol_names)
    assert any("DiscountRuleEngine" in n for n in symbol_names)
    assert any("OrderProcessingService" in n for n in symbol_names)
    assert any("PaymentGatewayService" in n for n in symbol_names)

    # 3. Verify Specific Business Rules & Comparison Operators
    rule_excerpts = [e.source_excerpt for e in evidence]
    assert any(">= VipSubtotalThreshold" in exc or "500.00m" in exc for exc in rule_excerpts)
    assert any("> BulkQuantityThreshold" in exc or "50" in exc for exc in rule_excerpts)
    assert any("MinimumOrderAmount" in exc or "10.00m" in exc for exc in rule_excerpts)
    assert any("MaxDiscountPercentageCap" in exc or "0.25m" in exc for exc in rule_excerpts)

    # 4. Verify Authorization Evidence
    auth_evidence = [e for e in evidence if e.category == EvidenceCategory.AUTHORIZATION]
    assert len(auth_evidence) > 0
    assert any("SalesAgent" in str(e.metadata) for e in auth_evidence)

    # 5. Verify Method Dependencies
    assert len(deps) > 0
