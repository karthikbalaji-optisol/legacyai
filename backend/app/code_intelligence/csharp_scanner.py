import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from backend.app.core.logging import logger
from backend.app.schemas.evidence import (
    DiscoveredSymbol,
    EvidenceCategory,
    EvidenceRecord,
    MethodDependency,
    ScanSummary,
)


def compute_evidence_id(repo_id: str, rel_path: str, start_line: int, symbol: str) -> str:
    seed = f"{repo_id}:{rel_path}:{start_line}:{symbol}".encode("utf-8")
    return f"ev_{hashlib.sha256(seed).hexdigest()[:12]}"

class CSharpScanner:
    """
    Deterministic C# syntax and pattern scanner for ASP.NET and enterprise C# patterns.
    Analyzes controllers, services, models, methods, business logic, thresholds,
    exceptions, status transitions, role checks, and dependencies.
    """

    def __init__(self, repository_id: str, repo_root: Path):
        self.repository_id = repository_id
        self.repo_root = repo_root
        self.symbols: List[DiscoveredSymbol] = []
        self.evidence_records: List[EvidenceRecord] = []
        self.dependencies: List[MethodDependency] = []
        self.file_lines: Dict[str, List[str]] = {}

    def scan_all(self) -> Tuple[ScanSummary, List[DiscoveredSymbol], List[EvidenceRecord], List[MethodDependency]]:
        cs_files = sorted(list(self.repo_root.glob("**/*.cs")))
        config_files = sorted(list(self.repo_root.glob("**/appsettings*.json")))

        total_lines = 0
        controllers_count = 0
        services_count = 0
        models_count = 0

        # Scan C# files
        for fpath in cs_files:
            rel_path = str(fpath.relative_to(self.repo_root)).replace("\\", "/")
            try:
                content = fpath.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    content = fpath.read_text(encoding="latin-1")
                except Exception:
                    continue

            lines = content.splitlines()
            self.file_lines[rel_path] = lines
            total_lines += len(lines)

            # Analyze file
            symbols_in_file = self._analyze_cs_file(rel_path, lines)
            self.symbols.extend(symbols_in_file)

            for sym in symbols_in_file:
                if sym.kind == "controller":
                    controllers_count += 1
                elif "Service" in sym.name or "Engine" in sym.name:
                    services_count += 1
                elif sym.kind == "model" or sym.kind == "enum":
                    models_count += 1

        # Scan config files
        for cfg_path in config_files:
            rel_path = str(cfg_path.relative_to(self.repo_root)).replace("\\", "/")
            self._analyze_json_config(rel_path, cfg_path)

        # Detect cross-symbol method dependencies
        self._resolve_dependencies()

        rule_count = sum(1 for e in self.evidence_records if e.category in [
            EvidenceCategory.BUSINESS_RULE,
            EvidenceCategory.THRESHOLD,
            EvidenceCategory.VALIDATION
        ])

        routes_count = sum(1 for e in self.evidence_records if e.category == EvidenceCategory.ROUTE)

        summary = ScanSummary(
            total_files=len(cs_files) + len(config_files),
            csharp_files=len(cs_files),
            total_lines_of_code=total_lines,
            controllers_count=controllers_count,
            services_count=services_count,
            models_count=models_count,
            evidence_count=len(self.evidence_records),
            business_rules_count=rule_count,
            routes_count=routes_count,
        )

        logger.info(
            f"Repository scan completed: {summary.csharp_files} C# files, "
            f"{len(self.symbols)} symbols, {len(self.evidence_records)} evidence items."
        )

        return summary, self.symbols, self.evidence_records, self.dependencies

    def _analyze_cs_file(self, rel_path: str, lines: List[str]) -> List[DiscoveredSymbol]:
        symbols: List[DiscoveredSymbol] = []
        current_namespace = None
        current_class = None
        current_class_kind = "class"
        class_start_line = 1
        class_roles: List[str] = []
        base_route: Optional[str] = None

        re_namespace = re.compile(r"^\s*namespace\s+([\w\.]+)")
        re_class = re.compile(r"^\s*(?:public|internal|protected|private)?\s*(?:static|abstract|sealed)?\s*(class|interface|enum)\s+(\w+)(?:\s*:\s*([\w\s,]+))?")
        re_method = re.compile(r"^\s*(?:public|protected|internal|private)?\s*(?:static|async|virtual|override)?\s*([\w\<\>\[\],]+)\s+(\w+)\s*\((.*?)\)")
        re_route_attr = re.compile(r'\[(?:Route|HttpGet|HttpPost|HttpPut|HttpDelete)\s*\(\s*"(.*?)"\s*\)\]')
        re_auth_attr = re.compile(r'\[Authorize\s*\(\s*Roles\s*=\s*"(.*?)"\s*\)\]')

        for i, line in enumerate(lines):
            line_num = i + 1
            line_str = line.strip()

            # 1. Namespace
            ns_match = re_namespace.match(line_str)
            if ns_match:
                current_namespace = ns_match.group(1)
                continue

            # 2. Authorization Attributes
            auth_match = re_auth_attr.search(line_str)
            if auth_match:
                roles = [r.strip() for r in auth_match.group(1).split(",")]
                class_roles.extend(roles)
                ev_id = compute_evidence_id(self.repository_id, rel_path, line_num, f"Authorize:{auth_match.group(1)}")
                self.evidence_records.append(EvidenceRecord(
                    id=ev_id,
                    repository_id=self.repository_id,
                    relative_path=rel_path,
                    symbol_name="AuthorizeAttribute",
                    start_line=line_num,
                    end_line=line_num,
                    source_excerpt=line_str,
                    category=EvidenceCategory.AUTHORIZATION,
                    metadata={"roles": roles}
                ))

            # 3. Route Attributes
            route_match = re_route_attr.search(line_str)
            if route_match:
                r_val = route_match.group(1)
                if current_class is None:
                    base_route = r_val
                ev_id = compute_evidence_id(self.repository_id, rel_path, line_num, f"Route:{r_val}")
                self.evidence_records.append(EvidenceRecord(
                    id=ev_id,
                    repository_id=self.repository_id,
                    relative_path=rel_path,
                    symbol_name="RouteAttribute",
                    start_line=line_num,
                    end_line=line_num,
                    source_excerpt=line_str,
                    category=EvidenceCategory.ROUTE,
                    metadata={"route": r_val}
                ))

            # 4. Class / Interface / Enum declaration
            class_match = re_class.match(line_str)
            if class_match and not line_str.startswith("//"):
                k, cname, _ = class_match.groups()
                current_class = cname
                class_start_line = line_num
                if "Controller" in cname:
                    current_class_kind = "controller"
                elif k == "enum":
                    current_class_kind = "enum"
                elif "Model" in cname or "Dto" in cname or "Entity" in cname or "Customer" in cname or "Order" in cname:
                    current_class_kind = "model"
                else:
                    current_class_kind = k

                sym = DiscoveredSymbol(
                    id=f"{rel_path}:{cname}",
                    name=cname,
                    kind=current_class_kind,
                    namespace=current_namespace,
                    relative_path=rel_path,
                    start_line=line_num,
                    end_line=line_num,
                    roles=list(class_roles),
                    route=base_route,
                )
                symbols.append(sym)
                continue

            # 5. Method declaration
            method_match = re_method.match(line_str)
            if method_match and not line_str.startswith("//") and not any(kw in line_str for kw in ["if (", "while (", "foreach (", "switch ("]):
                ret_type, mname, params_str = method_match.groups()
                if mname not in ["if", "for", "while", "switch", "catch", "using"]:
                    end_idx = min(len(lines), line_num + 30)
                    method_sym = DiscoveredSymbol(
                        id=f"{rel_path}:{current_class or 'Global'}.{mname}",
                        name=f"{current_class or 'Global'}.{mname}",
                        kind="method",
                        namespace=current_namespace,
                        relative_path=rel_path,
                        start_line=line_num,
                        end_line=end_idx,
                        return_type=ret_type.strip(),
                        parameters=[p.strip() for p in params_str.split(",") if p.strip()]
                    )
                    symbols.append(method_sym)

            # 6. Business Rules & Threshold Expressions
            self._check_business_rules(rel_path, line_str, line_num, lines, current_class)

            # 7. Status Transitions
            self._check_status_transitions(rel_path, line_str, line_num, current_class)

            # 8. External API calls & Database operations
            self._check_external_and_db(rel_path, line_str, line_num, current_class)

        return symbols

    def _check_business_rules(self, rel_path: str, line_str: str, line_num: int, lines: List[str], current_class: Optional[str]):
        threshold_patterns = [
            (r'([\w\.]+)\s*(>=|<=|>|<|==|!=)\s*(\d+(?:\.\d+)?m?)', "threshold_comparison"),
            (r'if\s*\((.*?)\s*(>=|<=|>|<)\s*(.*?)\)', "general_condition"),
            (r'throw\s+new\s+(\w+Exception)\s*\(\s*"(.*?)"\s*\)', "exception_rule"),
            (r'(\w+Tier\.\w+)', "tier_condition"),
            (r'MaxDiscountPercentageCap\s*=\s*(\d+\.\d+m?)', "discount_cap"),
        ]

        comment_rule_match = re.search(r'//\s*(RULE-\d+):\s*(.*)', line_str)
        if comment_rule_match:
            rule_tag, rule_title = comment_rule_match.groups()
            ev_id = compute_evidence_id(self.repository_id, rel_path, line_num, rule_tag)
            self.evidence_records.append(EvidenceRecord(
                id=ev_id,
                repository_id=self.repository_id,
                relative_path=rel_path,
                symbol_name=f"{current_class or 'Unknown'}",
                start_line=line_num,
                end_line=min(len(lines), line_num + 4),
                source_excerpt="\n".join(lines[line_num - 1 : min(len(lines), line_num + 4)]).strip(),
                category=EvidenceCategory.BUSINESS_RULE,
                extraction_method="comment_and_syntax_anchor",
                metadata={"rule_tag": rule_tag, "rule_title": rule_title}
            ))

        for pattern, kind in threshold_patterns:
            m = re.search(pattern, line_str)
            if m:
                if kind == "threshold_comparison":
                    left_var, op, right_val = m.groups()
                    if left_var not in ["i", "attempt", "maxAttempts"]:
                        ev_id = compute_evidence_id(self.repository_id, rel_path, line_num, f"{left_var}_{op}_{right_val}")
                        self.evidence_records.append(EvidenceRecord(
                            id=ev_id,
                            repository_id=self.repository_id,
                            relative_path=rel_path,
                            symbol_name=f"{current_class or 'Logic'}",
                            start_line=line_num,
                            end_line=line_num,
                            source_excerpt=line_str,
                            category=EvidenceCategory.THRESHOLD,
                            threshold_operator=op,
                            threshold_value=right_val,
                            metadata={"left": left_var, "operator": op, "right": right_val}
                        ))
                elif kind == "general_condition":
                    left_expr, op, right_expr = m.groups()
                    if not any(k in left_expr for k in ["attempt", "i"]):
                        ev_id = compute_evidence_id(self.repository_id, rel_path, line_num, f"Cond_{left_expr.strip()}_{op}")
                        self.evidence_records.append(EvidenceRecord(
                            id=ev_id,
                            repository_id=self.repository_id,
                            relative_path=rel_path,
                            symbol_name=f"{current_class or 'Logic'}",
                            start_line=line_num,
                            end_line=line_num,
                            source_excerpt=line_str,
                            category=EvidenceCategory.BUSINESS_RULE,
                            threshold_operator=op,
                            threshold_value=right_expr.strip(),
                            metadata={"left": left_expr.strip(), "operator": op, "right": right_expr.strip()}
                        ))
                elif kind == "exception_rule":
                    exc_type, exc_msg = m.groups()
                    ev_id = compute_evidence_id(self.repository_id, rel_path, line_num, exc_type)
                    self.evidence_records.append(EvidenceRecord(
                        id=ev_id,
                        repository_id=self.repository_id,
                        relative_path=rel_path,
                        symbol_name=f"{current_class or 'Logic'}",
                        start_line=line_num,
                        end_line=line_num,
                        source_excerpt=line_str,
                        category=EvidenceCategory.EXCEPTION_HANDLING,
                        metadata={"exception_type": exc_type, "message": exc_msg}
                    ))

    def _check_status_transitions(self, rel_path: str, line_str: str, line_num: int, current_class: Optional[str]):
        m = re.search(r'Status\s*=\s*OrderStatus\.(\w+)', line_str)
        if m:
            new_status = m.group(1)
            ev_id = compute_evidence_id(self.repository_id, rel_path, line_num, f"Transition:{new_status}")
            self.evidence_records.append(EvidenceRecord(
                id=ev_id,
                repository_id=self.repository_id,
                relative_path=rel_path,
                symbol_name=f"{current_class or 'Workflow'}",
                start_line=line_num,
                end_line=line_num,
                source_excerpt=line_str,
                category=EvidenceCategory.WORKFLOW,
                metadata={"status_transition_to": new_status}
            ))

    def _check_external_and_db(self, rel_path: str, line_str: str, line_num: int, current_class: Optional[str]):
        if "PostAsync" in line_str or "GetAsync" in line_str or "http" in line_str.lower():
            url_match = re.search(r'https?://[^\s"]+', line_str)
            ev_id = compute_evidence_id(self.repository_id, rel_path, line_num, "ExternalCall")
            self.evidence_records.append(EvidenceRecord(
                id=ev_id,
                repository_id=self.repository_id,
                relative_path=rel_path,
                symbol_name=f"{current_class or 'Integration'}",
                start_line=line_num,
                end_line=line_num,
                source_excerpt=line_str,
                category=EvidenceCategory.EXTERNAL_CALL,
                metadata={"url": url_match.group(0) if url_match else "external_endpoint"}
            ))

        if any(db_kw in line_str for db_kw in ["InsertOrderAsync", "UpdateOrderStatusAsync", "RecordAuditLogAsync", "GetByIdAsync", "GetCustomerAsync"]):
            ev_id = compute_evidence_id(self.repository_id, rel_path, line_num, "DbOperation")
            self.evidence_records.append(EvidenceRecord(
                id=ev_id,
                repository_id=self.repository_id,
                relative_path=rel_path,
                symbol_name=f"{current_class or 'Repository'}",
                start_line=line_num,
                end_line=line_num,
                source_excerpt=line_str,
                category=EvidenceCategory.DATABASE_OPERATION,
                metadata={"operation": line_str.strip()}
            ))

    def _analyze_json_config(self, rel_path: str, cfg_path: Path):
        try:
            content = cfg_path.read_text(encoding="utf-8")
            data = json.loads(content)
            lines = content.splitlines()

            for k, v in data.items():
                if isinstance(v, dict):
                    for subk, subv in v.items():
                        ev_id = compute_evidence_id(self.repository_id, rel_path, 1, f"Config:{k}.{subk}")
                        self.evidence_records.append(EvidenceRecord(
                            id=ev_id,
                            repository_id=self.repository_id,
                            relative_path=rel_path,
                            symbol_name="Configuration",
                            start_line=1,
                            end_line=min(15, len(lines)),
                            source_excerpt=f'"{k}": {{ "{subk}": "{subv}" }}',
                            category=EvidenceCategory.CONFIGURATION,
                            metadata={"section": k, "key": subk, "value": subv}
                        ))
        except Exception as e:
            logger.warning(f"Could not parse JSON configuration in {rel_path}: {e}")

    def _resolve_dependencies(self):
        known_methods = [s for s in self.symbols if s.kind == "method"]
        for sym in known_methods:
            rel_path = sym.relative_path
            lines = self.file_lines.get(rel_path, [])
            start = sym.start_line
            end = min(len(lines), sym.end_line)
            method_body = "\n".join(lines[start - 1 : end])

            for target in known_methods:
                if target.name != sym.name:
                    short_target = target.name.split(".")[-1]
                    if f"{short_target}(" in method_body:
                        call_line = start
                        for idx in range(start - 1, end):
                            if f"{short_target}(" in lines[idx]:
                                call_line = idx + 1
                                break
                        dep = MethodDependency(
                            source_symbol=sym.name,
                            target_symbol=target.name,
                            call_type="async" if "Async" in short_target else "sync",
                            source_file=rel_path,
                            line_number=call_line
                        )
                        self.dependencies.append(dep)
