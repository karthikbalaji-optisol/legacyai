from typing import Any

from mcp_server.server import (
    extract_code_symbols,
    find_business_rules,
    get_file_excerpt,
    list_source_files,
    search_code_evidence,
    trace_method_dependencies,
    validate_evidence,
)


class MCPClientAdapter:
    """
    Adapter bridging LangGraph workflows and external MCP tool invocations.
    Provides typed, scoped access to the code-intelligence tools.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def list_files(self) -> list[str]:
        return list_source_files(self.repo_path)

    def get_excerpt(self, relative_path: str, start_line: int, end_line: int) -> str:
        return get_file_excerpt(self.repo_path, relative_path, start_line, end_line)

    def extract_symbols(self, relative_path: str | None = None) -> list[dict[str, Any]]:
        return extract_code_symbols(self.repo_path, relative_path)

    def find_rules(self) -> list[dict[str, Any]]:
        return find_business_rules(self.repo_path)

    def trace_dependencies(self, method_name: str | None = None) -> list[dict[str, Any]]:
        return trace_method_dependencies(self.repo_path, method_name)

    def search_evidence(self, query: str) -> list[dict[str, Any]]:
        return search_code_evidence(self.repo_path, query)

    def verify_evidence(self, relative_path: str, start_line: int, expected_excerpt: str) -> dict[str, Any]:
        return validate_evidence(self.repo_path, relative_path, start_line, expected_excerpt)
