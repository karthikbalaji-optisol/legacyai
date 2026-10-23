from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from backend.app.code_intelligence.csharp_scanner import CSharpScanner

# Initialize MCP Server for LegacyLens Code Intelligence
mcp = MCPServer("legacylens-code-intelligence", version="1.0.0")

def _safe_resolve_path(repo_path: str, relative_path: str | None = None) -> Path:
    base = Path(repo_path).resolve()
    if not base.exists() or not base.is_dir():
        raise ValueError(f"Repository directory does not exist: {repo_path}")
    if relative_path is None:
        return base
    target = (base / relative_path).resolve()
    if not str(target).startswith(str(base)):
        raise PermissionError(f"Access denied: path escapes repository root: {relative_path}")
    return target

@mcp.tool()
def list_source_files(repo_path: str) -> list[str]:
    """
    Lists all C# and relevant configuration source files within the repository.
    Read-only and scoped to the repository boundary.
    """
    root = _safe_resolve_path(repo_path)
    files = []
    for p in root.glob("**/*"):
        if p.is_file() and p.suffix.lower() in [".cs", ".json", ".csproj", ".config"]:
            if not any(ig in p.parts for ig in [".git", "bin", "obj", "packages", "node_modules"]):
                files.append(str(p.relative_to(root)).replace("\\", "/"))
    return sorted(files)

@mcp.tool()
def get_file_excerpt(
    repo_path: str,
    relative_path: str,
    start_line: int,
    end_line: int,
) -> str:
    """
    Retrieves a bounded line excerpt from a repository source file.
    Enforces maximum range of 100 lines and valid line boundaries.
    """
    file_path = _safe_resolve_path(repo_path, relative_path)
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")

    start_line = max(start_line, 1)
    if end_line - start_line > 100:
        end_line = start_line + 100

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = file_path.read_text(encoding="latin-1").splitlines()

    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)

    return "\n".join(lines[start_idx:end_idx])

@mcp.tool()
def extract_code_symbols(
    repo_path: str,
    relative_path: str | None = None
) -> list[dict[str, Any]]:
    """
    Extracts structured classes, methods, controllers, interfaces, and routes.
    """
    root = _safe_resolve_path(repo_path)
    scanner = CSharpScanner("mcp_inspection", root)
    _, symbols, _, _ = scanner.scan_all()
    if relative_path:
        rel_norm = relative_path.replace("\\", "/")
        symbols = [s for s in symbols if s.relative_path == rel_norm]
    return [s.model_dump() for s in symbols]

@mcp.tool()
def find_business_rules(repo_path: str) -> list[dict[str, Any]]:
    """
    Discovers deterministic business rule anchors, validation constraints, and thresholds.
    """
    root = _safe_resolve_path(repo_path)
    scanner = CSharpScanner("mcp_inspection", root)
    _, _, evidence, _ = scanner.scan_all()
    rules = [e for e in evidence if e.category.value in ["business_rule", "threshold", "validation", "authorization"]]
    return [r.model_dump() for r in rules]

@mcp.tool()
def trace_method_dependencies(
    repo_path: str,
    method_name: str | None = None
) -> list[dict[str, Any]]:
    """
    Traces invocation and dependency links between methods and services.
    """
    root = _safe_resolve_path(repo_path)
    scanner = CSharpScanner("mcp_inspection", root)
    _, _, _, deps = scanner.scan_all()
    if method_name:
        deps = [d for d in deps if method_name in d.source_symbol or method_name in d.target_symbol]
    return [d.model_dump() for d in deps]

@mcp.tool()
def search_code_evidence(repo_path: str, query: str) -> list[dict[str, Any]]:
    """
    Searches for matching code evidence items containing the query string.
    """
    root = _safe_resolve_path(repo_path)
    scanner = CSharpScanner("mcp_inspection", root)
    _, _, evidence, _ = scanner.scan_all()
    q = query.lower()
    matches = [
        e for e in evidence
        if q in e.source_excerpt.lower() or q in e.symbol_name.lower() or q in e.relative_path.lower()
    ]
    return [m.model_dump() for m in matches[:25]]

@mcp.tool()
def validate_evidence(
    repo_path: str,
    relative_path: str,
    start_line: int,
    expected_excerpt: str
) -> dict[str, Any]:
    """
    Deterministically validates that an excerpt exists at the specified line in source.
    """
    file_path = _safe_resolve_path(repo_path, relative_path)
    if not file_path.exists():
        return {"valid": False, "reason": "File does not exist"}

    lines = file_path.read_text(encoding="utf-8").splitlines()
    if start_line < 1 or start_line > len(lines):
        return {"valid": False, "reason": f"Line {start_line} out of range (1..{len(lines)})"}

    actual_line = lines[start_line - 1].strip()
    match = expected_excerpt.strip() in actual_line or actual_line in expected_excerpt.strip()
    return {
        "valid": match,
        "actual_line": actual_line,
        "matched": match
    }

if __name__ == "__main__":
    mcp.run()
