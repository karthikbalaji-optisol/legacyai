from pathlib import Path

import pytest

from mcp_server.server import (
    extract_code_symbols,
    find_business_rules,
    get_file_excerpt,
    list_source_files,
    search_code_evidence,
    validate_evidence,
)


@pytest.fixture
def repo_path():
    return str(Path(__file__).resolve().parent.parent / "samples" / "LegacyOrders")

def test_mcp_list_source_files(repo_path):
    files = list_source_files(repo_path)
    assert len(files) >= 6
    assert any("Controllers/OrdersController.cs" in f for f in files)
    assert any("Services/DiscountRuleEngine.cs" in f for f in files)

def test_mcp_get_file_excerpt(repo_path):
    excerpt = get_file_excerpt(repo_path, "Services/DiscountRuleEngine.cs", 14, 18)
    assert "MaxDiscountPercentageCap" in excerpt
    assert "BulkQuantityThreshold" in excerpt

def test_mcp_extract_code_symbols(repo_path):
    symbols = extract_code_symbols(repo_path)
    assert len(symbols) > 10
    names = [s["name"] for s in symbols]
    assert any("OrdersController" in n for n in names)
    assert any("DiscountRuleEngine" in n for n in names)

def test_mcp_find_business_rules(repo_path):
    rules = find_business_rules(repo_path)
    assert len(rules) >= 5
    categories = [r["category"] for r in rules]
    assert "business_rule" in categories or "threshold" in categories

def test_mcp_search_code_evidence(repo_path):
    results = search_code_evidence(repo_path, "VIP")
    assert len(results) > 0
    assert any("VIP" in r["source_excerpt"] for r in results)

def test_mcp_validate_evidence(repo_path):
    res = validate_evidence(repo_path, "Services/DiscountRuleEngine.cs", 14, "MaxDiscountPercentageCap")
    assert res["valid"] is True
    assert res["matched"] is True

def test_mcp_rejects_path_traversal(repo_path):
    with pytest.raises(PermissionError):
        get_file_excerpt(repo_path, "../../etc/passwd", 1, 10)
