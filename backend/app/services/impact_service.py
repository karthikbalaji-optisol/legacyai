from typing import Any

from backend.app.schemas.api import ImpactEdge, ImpactGraphResponse, ImpactNode
from backend.app.schemas.brd import BRDDocument
from backend.app.schemas.evidence import (
    DiscoveredSymbol,
    EvidenceRecord,
    MethodDependency,
)


class ImpactAnalysisService:
    """
    Constructs the Business Rule Impact Explorer graph:
    Business Rule -> Source Method -> Related Service -> Functional Requirement -> Acceptance Criteria
    Grounds connections in real discovered source evidence and dependencies.
    """

    @staticmethod
    def build_impact_graph(
        analysis_id: str,
        brd: BRDDocument,
        evidence: list[EvidenceRecord],
        symbols: list[DiscoveredSymbol],
        dependencies: list[MethodDependency]
    ) -> ImpactGraphResponse:
        nodes: list[ImpactNode] = []
        edges: list[ImpactEdge] = []
        node_ids: set[str] = set()

        def add_node(nid: str, label: str, ntype: str, details: dict[str, Any]):
            if nid not in node_ids:
                nodes.append(ImpactNode(id=nid, label=label, node_type=ntype, details=details))
                node_ids.add(nid)

        # 1. Add Business Rules
        for rule in brd.business_rules:
            r_id = f"rule_{rule.id}"
            add_node(r_id, f"{rule.id}: {rule.title}", "rule", {
                "description": rule.description,
                "threshold": f"{rule.threshold_operator or ''} {rule.threshold_value or ''}".strip(),
                "source_file": rule.source_file,
                "confidence": rule.confidence.value,
                "classification": rule.classification.value
            })

            # Connect Rule to its Source Method / Class
            sym_id = f"symbol_{rule.source_symbol.replace('.', '_')}"
            add_node(sym_id, rule.source_symbol, "method", {
                "file": rule.source_file
            })
            edges.append(ImpactEdge(
                id=f"e_{r_id}_{sym_id}",
                source=r_id,
                target=sym_id,
                label="implemented_in",
                relationship="implements",
                confirmed=True
            ))

        # 2. Add Method-to-Method / Service Dependencies
        for dep in dependencies:
            src_id = f"symbol_{dep.source_symbol.replace('.', '_')}"
            tgt_id = f"symbol_{dep.target_symbol.replace('.', '_')}"
            add_node(src_id, dep.source_symbol, "method", {"file": dep.source_file})
            add_node(tgt_id, dep.target_symbol, "method", {"file": dep.source_file})
            edges.append(ImpactEdge(
                id=f"e_{src_id}_{tgt_id}",
                source=src_id,
                target=tgt_id,
                label=f"calls ({dep.call_type})",
                relationship="calls",
                confirmed=True
            ))

        # 3. Add Functional Requirements and connect to Methods
        for req in brd.functional_requirements:
            req_node_id = f"req_{req.id}"
            add_node(req_node_id, f"{req.id}: {req.title}", "requirement", {
                "description": req.description,
                "category": req.category,
                "confidence": req.confidence.value,
                "classification": req.classification.value
            })

            # Connect Methods implementing this requirement
            for impl in req.implemented_by_symbols:
                s_id = f"symbol_{impl.replace('.', '_')}"
                add_node(s_id, impl, "method", {})
                edges.append(ImpactEdge(
                    id=f"e_{s_id}_{req_node_id}",
                    source=s_id,
                    target=req_node_id,
                    label="supports_requirement",
                    relationship="implements",
                    confirmed=True
                ))

            # 4. Add Acceptance Criteria linked to Requirement
            for ac in req.acceptance_criteria:
                ac_node_id = f"ac_{ac.id}"
                add_node(ac_node_id, f"{ac.id}: {ac.scenario}", "acceptance_criteria", {
                    "scenario": ac.scenario,
                    "given": ac.given,
                    "when": ac.when,
                    "then": ac.then
                })
                edges.append(ImpactEdge(
                    id=f"e_{req_node_id}_{ac_node_id}",
                    source=req_node_id,
                    target=ac_node_id,
                    label="validated_by_scenario",
                    relationship="validates",
                    confirmed=True
                ))

        return ImpactGraphResponse(
            analysis_id=analysis_id,
            nodes=nodes,
            edges=edges
        )
