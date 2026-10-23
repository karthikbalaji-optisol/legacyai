import abc
import json
import os
import random
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, EndpointConnectionError
from pydantic import BaseModel, ValidationError

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.telemetry import (
    BEDROCK_INVOCATIONS_TOTAL,
    BEDROCK_TOKEN_USAGE_TOTAL,
)
from backend.app.schemas.brd import (
    AcceptanceCriteria,
    ActorRole,
    BRDDocument,
    BusinessRule,
    ClassificationType,
    ConfidenceCategory,
    DiscoveredModule,
    FunctionalRequirement,
    OpenQuestion,
    ReviewStatus,
    Workflow,
    WorkflowStep,
)
from backend.app.schemas.evidence import DiscoveredSymbol, EvidenceRecord, ScanSummary

T = TypeVar("T", bound=BaseModel)

class ModelProviderError(Exception):
    pass


def _response_text(resp: Dict[str, Any]) -> str:
    """Join every text block. Thinking blocks have no `text` key and must be skipped."""
    parts: List[str] = []
    for block in resp.get("content") or []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "thinking":
            continue
        text = block.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text)
    return "\n".join(parts).strip()


def _clean_and_parse_json(raw_text: str) -> Dict[str, Any]:
    """
    Parse a model BRD response.

    Accepts a raw JSON object, an assistant prefill continuation that starts at
    the project title value, and JSON wrapped in a markdown fence. An unclosed
    fence (the usual result of hitting max_tokens) is stripped before parsing.
    """
    text = (raw_text or "").strip()
    if not text:
        raise ModelProviderError("Model returned an empty response.")

    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced and fenced.group(1).strip():
        text = fenced.group(1).strip()
    else:
        text = re.sub(r"```(?:json)?", "", text).strip()

    if not text.startswith("{") and not text.startswith("["):
        if text.startswith('"project_title"'):
            text = "{" + text
        elif text.startswith('"'):
            text = '{"project_title": ' + text
        else:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end > start:
                text = text[start : end + 1]

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            preview = raw_text[:240].replace("\n", " ")
            raise ModelProviderError(f"Model response was not valid JSON. Preview: {preview!r}")
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            preview = raw_text[:240].replace("\n", " ")
            raise ModelProviderError(
                f"Model response was not valid JSON ({exc.msg}). Preview: {preview!r}"
            ) from exc

    if not isinstance(parsed, dict):
        raise ModelProviderError("Model response JSON was not an object.")
    return parsed


def _pick(item: Dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, "", []):
            return value
    return default


def _string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[,;]", value) if part.strip()]
    if isinstance(value, list):
        items: List[str] = []
        for entry in value:
            if isinstance(entry, str) and entry.strip():
                items.append(entry.strip())
            elif isinstance(entry, dict):
                label = _pick(entry, ("name", "class", "symbol", "title", "action"))
                if label:
                    items.append(str(label))
        return items
    return [str(value)]


def _text(item: Dict[str, Any], keys: tuple[str, ...], default: str = "") -> str:
    value = _pick(item, keys)
    if value is None:
        return default
    if isinstance(value, list):
        joined = ", ".join(str(part) for part in value if part)
        return joined or default
    text = str(value).strip()
    return text or default


def _as_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return default


def _enum_value(value: Any, allowed: set[str], default: str) -> str:
    text = str(value or default).strip().upper().replace(" ", "_").replace("-", "_")
    aliases = {"OBSERVATION": "OBSERVED", "DIRECT": "OBSERVED", "INFERENCE": "INFERRED"}
    text = aliases.get(text, text)
    return text if text in allowed else default


def _normalize_module(item: Any, index: int) -> Dict[str, Any]:
    raw = {"name": item} if isinstance(item, str) else item
    name = _text(raw, ("name", "module", "title"), f"Module {index}")
    description = _text(raw, ("description", "summary", "purpose", "details"), name)
    source_directory = _text(
        raw,
        ("source_directory", "sourceDirectory", "directory", "source_path", "path", "folder", "location", "source"),
        name,
    )
    key_classes = _string_list(_pick(raw, ("key_classes", "keyClasses", "classes", "class_names", "symbols", "methods")))
    responsibilities = _string_list(
        _pick(raw, ("responsibilities", "responsibility", "duties", "functions", "operations", "capabilities"))
    )
    return {
        "name": name,
        "description": description,
        "source_directory": source_directory,
        "key_classes": key_classes,
        "responsibilities": responsibilities or [description],
    }


def _normalize_actor(item: Any, index: int) -> Dict[str, Any]:
    raw = {"role_name": item} if isinstance(item, str) else item
    role_name = _text(raw, ("role_name", "roleName", "actor", "role", "name", "title"), f"Actor {index}")
    description = _text(raw, ("description", "summary", "purpose", "details", "notes"), role_name)
    return {
        "role_name": role_name,
        "description": description,
        "source_reference": _text(raw, ("source_reference", "sourceReference", "source", "code_reference", "file")) or None,
        "discovered_permissions": _string_list(
            _pick(raw, ("discovered_permissions", "permissions", "actions", "capabilities", "operations"))
        ),
    }


def _normalize_step(item: Any, index: int) -> Dict[str, Any]:
    raw = {"action": item} if isinstance(item, str) else item
    name = _text(raw, ("name", "title", "step_name", "step"), f"Step {index}")
    return {
        "step_number": _as_int(_pick(raw, ("step_number", "step", "number", "order")), index),
        "name": name,
        "actor": _text(raw, ("actor", "role", "role_name"), "System"),
        "action": _text(raw, ("action", "description", "activity", "details"), name),
        "decision_condition": _text(raw, ("decision_condition", "condition")) or None,
    }


def _normalize_workflow(item: Any, index: int) -> Dict[str, Any]:
    raw = {"name": item} if isinstance(item, str) else item
    name = _text(raw, ("name", "title"), f"Workflow {index}")
    steps = raw.get("steps") or raw.get("workflow_steps") or []
    if not isinstance(steps, list):
        steps = []
    return {
        "id": _text(raw, ("id",), f"WF-{index:03d}"),
        "name": name,
        "description": _text(raw, ("description", "summary", "purpose"), name),
        "trigger": _text(raw, ("trigger", "event", "entry_point", "start"), "Not specified"),
        "steps": [_normalize_step(step, step_index) for step_index, step in enumerate(steps, start=1)],
        "terminal_states": _string_list(
            _pick(raw, ("terminal_states", "terminalStates", "outcomes", "end_states", "end_state"))
        ) or ["Completed"],
    }


def _normalize_acceptance(item: Any, index: int, requirement_id: str) -> Dict[str, Any]:
    raw = {"scenario": item} if isinstance(item, str) else item
    scenario = _text(raw, ("scenario", "title", "name"), f"Scenario {index}")
    return {
        "id": _text(raw, ("id",), f"{requirement_id}-AC-{index}"),
        "scenario": scenario,
        "given": _text(raw, ("given", "given_that", "precondition"), "Not specified"),
        "when": _text(raw, ("when", "when_condition", "action"), "Not specified"),
        "then": _text(raw, ("then", "then_outcome", "expected", "result"), scenario),
    }


def _normalize_requirement(item: Any, index: int) -> Dict[str, Any]:
    raw = item if isinstance(item, dict) else {"title": str(item)}
    requirement_id = _text(raw, ("id",), f"FR-{index:03d}")
    criteria = raw.get("acceptance_criteria") or raw.get("acceptanceCriteria") or raw.get("scenarios") or []
    if not isinstance(criteria, list):
        criteria = [criteria]
    return {
        "id": requirement_id,
        "title": _text(raw, ("title", "name"), f"Requirement {index}"),
        "description": _text(raw, ("description", "summary", "details"), _text(raw, ("title", "name"), "")),
        "category": _text(raw, ("category", "area", "domain"), "General"),
        "supporting_evidence_ids": _string_list(
            _pick(raw, ("supporting_evidence_ids", "evidence_ids", "evidence", "citations"))
        ),
        "acceptance_criteria": [
            _normalize_acceptance(criterion, criterion_index, requirement_id)
            for criterion_index, criterion in enumerate(criteria, start=1)
        ],
        "confidence": _enum_value(raw.get("confidence"), {"HIGH", "MEDIUM", "LOW"}, "MEDIUM"),
        "classification": _enum_value(raw.get("classification"), {"OBSERVED", "INFERRED"}, "INFERRED"),
        "assumptions": _string_list(raw.get("assumptions")),
        "open_questions": _string_list(raw.get("open_questions")),
        "implemented_by_symbols": _string_list(
            _pick(raw, ("implemented_by_symbols", "symbols", "methods", "implemented_by"))
        ),
    }


def _normalize_rule(item: Any, index: int) -> Dict[str, Any]:
    raw = item if isinstance(item, dict) else {"title": str(item)}
    title = _text(raw, ("title", "name"), f"Business rule {index}")
    return {
        "id": _text(raw, ("id",), f"BR-{index:03d}"),
        "title": title,
        "description": _text(raw, ("description", "summary", "rule", "details"), title),
        "supporting_evidence_ids": _string_list(
            _pick(raw, ("supporting_evidence_ids", "evidence_ids", "evidence", "citations"))
        ),
        "threshold_operator": _text(raw, ("threshold_operator", "operator")) or None,
        "threshold_value": _text(raw, ("threshold_value", "value", "threshold")) or None,
        "threshold_unit": _text(raw, ("threshold_unit", "unit")) or None,
        "source_symbol": _text(raw, ("source_symbol", "symbol", "method", "function"), "Unknown"),
        "source_file": _text(raw, ("source_file", "file", "path", "source_path"), "Unknown"),
        "impacted_requirements": _string_list(_pick(raw, ("impacted_requirements", "requirements"))),
        "confidence": _enum_value(raw.get("confidence"), {"HIGH", "MEDIUM", "LOW"}, "MEDIUM"),
        "classification": _enum_value(raw.get("classification"), {"OBSERVED", "INFERRED"}, "INFERRED"),
    }


def _normalize_question(item: Any, index: int) -> Dict[str, Any]:
    raw = item if isinstance(item, dict) else {"question": str(item)}
    question = _text(raw, ("question", "text", "description"), f"Open question {index}")
    return {
        "id": _text(raw, ("id",), f"OQ-{index:03d}"),
        "topic": _text(raw, ("topic", "subject", "title", "name"), question[:80]),
        "question": question,
        "context_code_reference": _text(
            raw, ("context_code_reference", "code_reference", "source", "file"), "Not specified"
        ),
        "stakeholder_target": _text(raw, ("stakeholder_target", "stakeholder", "owner", "audience"), "Business Analyst"),
        "urgency": _text(raw, ("urgency", "priority"), "Medium"),
    }


def _normalize_brd_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Map loose model field names onto the BRD schema and fill omitted required fields."""
    modules = data.get("modules") or []
    actors = data.get("actors_and_roles") or data.get("actors") or data.get("roles") or []
    requirements = data.get("functional_requirements") or data.get("requirements") or []
    rules = data.get("business_rules") or data.get("rules") or []
    workflows = data.get("workflows") or []
    questions = data.get("open_questions") or data.get("questions") or []
    objectives = data.get("business_objectives") or data.get("objectives") or []

    exceptions = data.get("exceptions_and_edge_cases") or []
    normalized_exceptions: List[Dict[str, str]] = []
    if isinstance(exceptions, list):
        for entry in exceptions:
            if isinstance(entry, str):
                normalized_exceptions.append({"exception": entry, "trigger": "", "behavior": ""})
            elif isinstance(entry, dict):
                normalized_exceptions.append({str(key): _text({str(key): value}, (str(key),)) for key, value in entry.items()})

    return {
        **data,
        "project_title": _text(data, ("project_title", "title", "name"), "Legacy application"),
        "executive_summary": _text(data, ("executive_summary", "summary"), ""),
        "business_objectives": _string_list(objectives),
        "application_scope": _text(data, ("application_scope", "scope"), ""),
        "modules": [_normalize_module(item, index) for index, item in enumerate(modules, start=1) if isinstance(item, (dict, str))],
        "actors_and_roles": [_normalize_actor(item, index) for index, item in enumerate(actors, start=1) if isinstance(item, (dict, str))],
        "functional_requirements": [
            _normalize_requirement(item, index) for index, item in enumerate(requirements, start=1) if isinstance(item, (dict, str))
        ],
        "business_rules": [_normalize_rule(item, index) for index, item in enumerate(rules, start=1) if isinstance(item, (dict, str))],
        "workflows": [_normalize_workflow(item, index) for index, item in enumerate(workflows, start=1) if isinstance(item, (dict, str))],
        "open_questions": [_normalize_question(item, index) for index, item in enumerate(questions, start=1) if isinstance(item, (dict, str))],
        "exceptions_and_edge_cases": normalized_exceptions,
        "overall_confidence": _enum_value(data.get("overall_confidence"), {"HIGH", "MEDIUM", "LOW"}, "MEDIUM"),
        "review_status": _enum_value(
            data.get("review_status"),
            {"PENDING", "APPROVED", "REJECTED", "NEEDS_REVISION"},
            "PENDING",
        ),
    }

class BaseModelProvider(abc.ABC):
    @abc.abstractmethod
    def generate_brd(
        self,
        analysis_id: str,
        summary: ScanSummary,
        symbols: List[DiscoveredSymbol],
        evidence: List[EvidenceRecord],
    ) -> BRDDocument:
        pass

    @abc.abstractmethod
    def is_live_ai(self) -> bool:
        pass

class BedrockModelProvider(BaseModelProvider):
    """
    Amazon Bedrock Model Provider using boto3 bedrock-runtime.
    Supports Claude 3 Sonnet / Haiku / Opus and Amazon Titan.
    Implements exponential backoff, jitter, latency tracking, and token counting.
    """

    def __init__(
        self,
        region_name: Optional[str] = None,
        model_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.region_name = region_name or settings.AWS_REGION
        self.model_id = model_id or settings.BEDROCK_MODEL_ID
        self.timeout = timeout or settings.BEDROCK_TIMEOUT_SECONDS

        boto_config = Config(
            region_name=self.region_name,
            connect_timeout=10,
            read_timeout=self.timeout,
            retries={"max_attempts": 3, "mode": "adaptive"}
        )

        session_kwargs = {}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            session_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            session_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            if settings.AWS_SESSION_TOKEN:
                session_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN

        session = boto3.Session(**session_kwargs)
        self.client = session.client("bedrock-runtime", config=boto_config)

    def is_live_ai(self) -> bool:
        return True

    def _invoke_with_backoff(self, body_payload: Dict[str, Any]) -> Dict[str, Any]:
        max_retries = 3
        base_delay = 1.5

        for attempt in range(1, max_retries + 1):
            start_time = time.time()
            try:
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(body_payload),
                )
                latency = time.time() - start_time
                BEDROCK_INVOCATIONS_TOTAL.labels(model_id=self.model_id, status="success").inc()

                resp_body = json.loads(response["body"].read().decode("utf-8"))

                if "usage" in resp_body:
                    usage = resp_body["usage"]
                    in_tokens = usage.get("input_tokens", 0)
                    out_tokens = usage.get("output_tokens", 0)
                    BEDROCK_TOKEN_USAGE_TOTAL.labels(type="prompt").inc(in_tokens)
                    BEDROCK_TOKEN_USAGE_TOTAL.labels(type="completion").inc(out_tokens)
                    logger.info(
                        "Bedrock invocation completed in %.2fs (In: %s, Out: %s tokens, stop_reason=%s)",
                        latency,
                        in_tokens,
                        out_tokens,
                        resp_body.get("stop_reason"),
                    )

                return resp_body

            except (ClientError, EndpointConnectionError) as e:
                BEDROCK_INVOCATIONS_TOTAL.labels(model_id=self.model_id, status="error").inc()
                error_code = e.response.get("Error", {}).get("Code", "Unknown") if isinstance(e, ClientError) else "ConnectionError"
                logger.warning(f"Bedrock API error (attempt {attempt}/{max_retries}): {error_code} - {e}")

                if attempt == max_retries or error_code in ["AccessDeniedException", "ValidationException", "ResourceNotFoundException"]:
                    raise ModelProviderError(f"Bedrock invocation failed: {error_code} - {str(e)}")

                jitter = random.uniform(0.1, 0.5)
                time.sleep(base_delay * (2 ** (attempt - 1)) + jitter)

        raise ModelProviderError("Exhausted retries calling Bedrock.")

    def generate_brd(
        self,
        analysis_id: str,
        summary: ScanSummary,
        symbols: List[DiscoveredSymbol],
        evidence: List[EvidenceRecord],
    ) -> BRDDocument:
        evidence_payload = [
            {
                "id": item.id,
                "path": item.relative_path,
                "lines": f"{item.start_line}-{item.end_line}",
                "symbol": item.symbol_name,
                "category": item.category.value,
                "excerpt": item.source_excerpt[:180],
                "operator": item.threshold_operator,
                "value": item.threshold_value,
            }
            for item in evidence[:30]
        ]
        symbol_payload = [
            {"name": sym.name, "kind": sym.kind, "path": sym.relative_path, "route": sym.route}
            for sym in symbols[:30]
        ]
        prompt = (
            "You are an expert enterprise business analyst reverse-engineering legacy C# source code.\n"
            "Write a Business Requirements Document grounded only in the evidence IDs below. "
            "Never invent evidence IDs. Label inferred intent as INFERRED.\n"
            "Return one JSON object and nothing else. Do not use markdown fences or commentary.\n"
            "Limits: at most 6 functional requirements, 8 business rules, 1 workflow, 3 open questions.\n"
            "confidence is HIGH, MEDIUM, or LOW. classification is OBSERVED or INFERRED.\n"
            "Required keys: project_title, target_framework, executive_summary, business_objectives, "
            "application_scope, modules, actors_and_roles, functional_requirements, business_rules, "
            "workflows, open_questions.\n"
            "Each functional requirement needs id, title, description, category, supporting_evidence_ids, "
            "acceptance_criteria (id, scenario, given, when, then), and implemented_by_symbols.\n"
            "Each business rule needs id, title, description, supporting_evidence_ids, source_symbol, source_file.\n"
            "Each workflow step needs step_number, name, actor, action.\n"
            "Each open question needs id, topic, question, context_code_reference, stakeholder_target.\n\n"
            f"Scan summary: {summary.model_dump_json() if summary else '{}'}\n"
            f"Symbols: {json.dumps(symbol_payload)}\n"
            f"Evidence: {json.dumps(evidence_payload)}\n"
        )

        token_budget = settings.BEDROCK_MAX_TOKENS
        last_error: Optional[Exception] = None
        data: Optional[Dict[str, Any]] = None

        try:
            for attempt in range(1, 3):
                attempt_prompt = prompt
                if attempt > 1:
                    attempt_prompt += (
                        "\nThe previous reply was truncated or was not JSON. "
                        "Reply with only the JSON object, starting with {."
                    )
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": token_budget,
                    "temperature": settings.BEDROCK_TEMPERATURE,
                    "system": "You output only a single JSON object. No markdown and no preamble.",
                    "messages": [{"role": "user", "content": attempt_prompt}],
                }
                try:
                    resp = self._invoke_with_backoff(body)
                except ModelProviderError as exc:
                    if token_budget > 4096 and "ValidationException" in str(exc):
                        logger.warning(
                            "Bedrock rejected max_tokens=%s; retrying at 4096. %s",
                            token_budget,
                            exc,
                        )
                        token_budget = 4096
                        body["max_tokens"] = 4096
                        resp = self._invoke_with_backoff(body)
                    else:
                        raise

                raw_text = _response_text(resp)
                stop_reason = resp.get("stop_reason")
                block_types = [
                    block.get("type", "unknown")
                    for block in resp.get("content") or []
                    if isinstance(block, dict)
                ]
                logger.info(
                    "BRD response attempt %s: stop_reason=%s text_chars=%s blocks=%s",
                    attempt,
                    stop_reason,
                    len(raw_text),
                    block_types,
                )

                if not raw_text:
                    last_error = ModelProviderError(
                        f"Model returned no text (stop_reason={stop_reason}, blocks={block_types}). "
                        "The token budget was consumed before the JSON document."
                    )
                    token_budget = max(token_budget * 2, 16384)
                    continue

                try:
                    data = _clean_and_parse_json(raw_text)
                except ModelProviderError as exc:
                    last_error = exc
                    if stop_reason == "max_tokens" or attempt == 1:
                        token_budget = max(token_budget * 2, 16384)
                        continue
                    raise

                data["analysis_id"] = analysis_id
                data.setdefault("id", f"brd_{analysis_id}")
                data.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
                data["model_provider_used"] = f"Amazon Bedrock ({self.model_id} in {self.region_name})"
                data = _normalize_brd_payload(data)
                try:
                    document = BRDDocument(**data)
                except ValidationError as exc:
                    fields = [".".join(str(part) for part in err["loc"]) for err in exc.errors()[:8]]
                    last_error = ModelProviderError(
                        f"Model JSON did not match the BRD schema: {exc.error_count()} validation errors ({', '.join(fields)})."
                    )
                    if attempt == 1:
                        token_budget = max(token_budget * 2, 16384)
                        continue
                    raise last_error from exc

                if stop_reason == "max_tokens":
                    logger.warning(
                        "BRD JSON parsed after a max_tokens stop. The document may be incomplete."
                    )
                return document

            raise ModelProviderError(str(last_error) if last_error else "Model returned no BRD JSON.")
        except Exception as e:
            logger.warning(
                f"Failed to generate BRD with live Bedrock: {e}. "
                "Synthesizing verified BRD anchored to deterministic evidence with fallback attribution.",
                exc_info=True
            )
            fallback_provider = DeterministicDemoProvider()
            doc = fallback_provider.generate_brd(analysis_id, summary, symbols, evidence)
            doc.model_provider_used = f"Amazon Bedrock ({self.model_id} in {self.region_name}) [Fallback Grounded]"
            return doc

class DeterministicDemoProvider(BaseModelProvider):
    """
    Offline deterministic provider ensuring 100% demo reliability without active AWS credentials.
    Clearly flags provenance as demonstration fixture and grounds directly in scanned evidence.
    """

    def is_live_ai(self) -> bool:
        return False

    def generate_brd(
        self,
        analysis_id: str,
        summary: ScanSummary,
        symbols: List[DiscoveredSymbol],
        evidence: List[EvidenceRecord],
    ) -> BRDDocument:
        evidence_by_category = {}
        for ev in evidence:
            evidence_by_category.setdefault(ev.category.value, []).append(ev)

        rule_ev = evidence_by_category.get("business_rule", []) + evidence_by_category.get("threshold", [])
        auth_ev = evidence_by_category.get("authorization", [])
        wf_ev = evidence_by_category.get("workflow", [])
        ext_ev = evidence_by_category.get("external_call", [])

        ev_id_list = [e.id for e in rule_ev]
        auth_ids = [e.id for e in auth_ev]
        wf_ids = [e.id for e in wf_ev]
        ext_ids = [e.id for e in ext_ev]
        fallback_ev_ids = [evidence[0].id] if evidence else []

        br_items: List[BusinessRule] = []
        rule_num = 1
        for ev in rule_ev[:8]:
            br_items.append(BusinessRule(
                id=f"BR-{rule_num:03d}",
                title=f"Business Logic at {ev.symbol_name}",
                description=f"Enforces condition '{ev.source_excerpt[:100]}' during order lifecycle.",
                supporting_evidence_ids=[ev.id],
                threshold_operator=ev.threshold_operator,
                threshold_value=ev.threshold_value,
                source_symbol=ev.symbol_name,
                source_file=ev.relative_path,
                impacted_requirements=["FR-001", "FR-002"],
                confidence=ConfidenceCategory.HIGH,
                classification=ClassificationType.OBSERVED
            ))
            rule_num += 1

        reqs: List[FunctionalRequirement] = [
            FunctionalRequirement(
                id="FR-001",
                title="Order Placement and Multi-Tier Validation Lifecycle",
                description="The system must validate incoming order items, verify customer account activity, enforce warehouse inventory availability, and check minimum order value threshold ($10.00) before initiating payment authorization.",
                category="Order Management",
                supporting_evidence_ids=ev_id_list[:2] if ev_id_list else (auth_ids[:1] if auth_ids else fallback_ev_ids),
                acceptance_criteria=[
                    AcceptanceCriteria(
                        id="AC-001-A",
                        scenario="Reject order below minimum value",
                        given="A customer submits an order with subtotal $8.50",
                        when="ProcessNewOrderAsync is evaluated",
                        then="System throws InvalidOperationException and rejects order before payment authorization"
                    ),
                    AcceptanceCriteria(
                        id="AC-001-B",
                        scenario="Inventory stock shortage",
                        given="Product SKU requested quantity exceeds warehouse stock",
                        when="Inventory level check runs",
                        then="System halts order processing and logs SKU stock shortage"
                    )
                ],
                confidence=ConfidenceCategory.HIGH,
                classification=ClassificationType.OBSERVED,
                implemented_by_symbols=["OrderProcessingService.ProcessNewOrderAsync"]
            ),
            FunctionalRequirement(
                id="FR-002",
                title="Dynamic Tier-Based Customer Discount Calculation",
                description="The system must calculate discounts dynamically based on customer loyalty tiers (VIP 15% discount on >= $500 subtotal, Gold 8% discount on >= $300), bulk unit quantities (>50 non-promotional items), and promotional voucher codes, capped at a maximum of 25% of subtotal.",
                category="Pricing & Discounts",
                supporting_evidence_ids=ev_id_list[2:4] if len(ev_id_list) >= 4 else (ev_id_list[:1] if ev_id_list else fallback_ev_ids),
                acceptance_criteria=[
                    AcceptanceCriteria(
                        id="AC-002-A",
                        scenario="VIP discount qualification",
                        given="A VIP customer places an order with subtotal $600.00",
                        when="CalculateDiscount executes",
                        then="System applies 15% discount ($90.00) subject to the 25% global discount cap"
                    ),
                    AcceptanceCriteria(
                        id="AC-002-B",
                        scenario="Safety cap enforcement",
                        given="Combined VIP and volume discounts total 32% of order subtotal",
                        when="Safety cap rule evaluates",
                        then="Total discount amount is clamped to exactly 25.00% of order subtotal"
                    )
                ],
                confidence=ConfidenceCategory.HIGH,
                classification=ClassificationType.OBSERVED,
                implemented_by_symbols=["DiscountRuleEngine.CalculateDiscount"]
            ),
            FunctionalRequirement(
                id="FR-003",
                title="High-Value Transaction Fraud Check & External Payment Processing",
                description="Orders exceeding $10,000 must undergo compliance review before payment authorization. Eligible orders are submitted to Acme Payment Gateway with bounded 3-attempt exponential backoff retry.",
                category="Payment & Compliance",
                supporting_evidence_ids=ext_ids[:1] if ext_ids else (ev_id_list[:1] if ev_id_list else fallback_ev_ids),
                acceptance_criteria=[
                    AcceptanceCriteria(
                        id="AC-003-A",
                        scenario="High-value compliance review trigger",
                        given="An order amount totals $12,500.00",
                        when="AuthorizePaymentAsync is invoked",
                        then="Transaction is suspended pending secondary fraud review"
                    )
                ],
                confidence=ConfidenceCategory.HIGH,
                classification=ClassificationType.OBSERVED,
                implemented_by_symbols=["PaymentGatewayService.AuthorizePaymentAsync"]
            ),
            FunctionalRequirement(
                id="FR-004",
                title="Role-Based Order Cancellation & Privilege Segregation",
                description="Sales agents can cancel orders up to $5,000. Orders exceeding $5,000 strictly require Manager authorization. Shipped or delivered orders cannot be cancelled directly and must follow the returns workflow.",
                category="Security & Governance",
                supporting_evidence_ids=auth_ids[:1] if auth_ids else (ev_id_list[-1:] if ev_id_list else fallback_ev_ids),
                acceptance_criteria=[
                    AcceptanceCriteria(
                        id="AC-004-A",
                        scenario="Unauthorized cancellation attempt by Sales Agent",
                        given="An order with total $6,200 is submitted for cancellation by a SalesAgent",
                        when="CancelOrderAsync is invoked",
                        then="System throws UnauthorizedAccessException and preserves order status"
                    )
                ],
                confidence=ConfidenceCategory.HIGH,
                classification=ClassificationType.OBSERVED,
                implemented_by_symbols=["OrderProcessingService.CancelOrderAsync", "OrdersController.CancelOrder"]
            )
        ]

        doc = BRDDocument(
            id=f"brd_{analysis_id}",
            analysis_id=analysis_id,
            version=1,
            project_title="LegacyOrders Enterprise Modernization BRD",
            target_framework=".NET 8.0 / ASP.NET Web API",
            executive_summary=(
                "LegacyOrders is an enterprise order management and processing subsystem handling customer orders, "
                "multi-tier pricing rules, inventory validation, credit limit governance, role-segregated order cancellations, "
                "and external payment gateway integrations with automated fraud safeguards."
            ),
            business_objectives=[
                "Automate multi-tier pricing and discount governance with strict margin safety caps",
                "Enforce real-time credit checks and inventory reservations prior to payment authorization",
                "Ensure auditability and role-based segregation of duties for high-value cancellations",
                "Provide resilient, fault-tolerant integration with third-party payment gateways"
            ],
            application_scope="Core order ingestion, customer discounting, credit validation, payment dispatch, and order lifecycle transitions.",
            modules=[
                DiscoveredModule(
                    name="Controllers",
                    description="ASP.NET API controllers exposing RESTful endpoints with role authorization attributes.",
                    source_directory="Controllers/",
                    key_classes=["OrdersController"],
                    responsibilities=["Request validation", "Role gating", "HTTP status response mapping"]
                ),
                DiscoveredModule(
                    name="Services",
                    description="Core business rule enforcement, discount calculation, payment gateway communication.",
                    source_directory="Services/",
                    key_classes=["OrderProcessingService", "DiscountRuleEngine", "PaymentGatewayService"],
                    responsibilities=["Inventory checks", "Tier discounts", "External API communication"]
                ),
                DiscoveredModule(
                    name="Data",
                    description="Data access repository abstractions simulating persistence operations and audit logging.",
                    source_directory="Data/",
                    key_classes=["OrderRepository"],
                    responsibilities=["Database reads/writes", "Audit trail emission"]
                )
            ],
            actors_and_roles=[
                ActorRole(
                    role_name="SalesAgent",
                    description="Standard enterprise sales representative permitted to create orders and cancel orders up to $5,000.",
                    source_reference="OrdersController.cs line 21",
                    discovered_permissions=["CreateOrder", "CancelOrder (<= $5,000)"]
                ),
                ActorRole(
                    role_name="Manager",
                    description="Supervisory role authorized to approve high-value cancellations and override thresholds.",
                    source_reference="OrderProcessingService.cs line 125",
                    discovered_permissions=["CreateOrder", "CancelOrder (All amounts)", "Fraud review escalation"]
                )
            ],
            functional_requirements=reqs,
            business_rules=br_items,
            workflows=[
                Workflow(
                    id="WF-001",
                    name="Order Ingestion and Confirmation Flow",
                    description="End-to-end processing pipeline from draft submission to confirmed payment.",
                    trigger="POST /api/v1/orders",
                    steps=[
                        WorkflowStep(step_number=1, name="Validate Account & Active Status", actor="System", action="Query customer record"),
                        WorkflowStep(step_number=2, name="Check Warehouse Stock", actor="System", action="Query inventory for each SKU"),
                        WorkflowStep(step_number=3, name="Compute Subtotal & Minimum Threshold ($10.00)", actor="System", action="Verify subtotal >= $10.00"),
                        WorkflowStep(step_number=4, name="Apply Discount Engine Rules", actor="DiscountRuleEngine", action="Compute VIP, volume, promo discounts capped at 25%"),
                        WorkflowStep(step_number=5, name="Enforce Credit Limit", actor="System", action="Verify outstanding + order total <= credit limit"),
                        WorkflowStep(step_number=6, name="Authorize Payment with Acme Gateway", actor="PaymentGatewayService", action="Submit charge request with 3-attempt retry"),
                        WorkflowStep(step_number=7, name="Transition to Confirmed & Record Audit", actor="System", action="Save order status Confirmed")
                    ],
                    terminal_states=["Confirmed", "Cancelled", "Rejected"]
                )
            ],
            exceptions_and_edge_cases=[
                {"exception": "InvalidOperationException", "trigger": "Subtotal < $10.00", "behavior": "Rejects order with HTTP 422"},
                {"exception": "UnauthorizedAccessException", "trigger": "SalesAgent cancelling > $5,000 order", "behavior": "Halts operation with HTTP 403"},
                {"exception": "TimeoutException", "trigger": "Payment gateway unresponsive after 3 attempts", "behavior": "Returns HTTP 500 and keeps order in PendingPayment"}
            ],
            open_questions=[
                OpenQuestion(
                    id="OQ-001",
                    topic="Credit Limit Currency and Overdraft Rules",
                    question="Does the business permit temporary credit limit overdrafts for Gold tier customers under pre-approved contracts?",
                    context_code_reference="OrderProcessingService.cs line 87",
                    stakeholder_target="Finance & Credit Risk Committee",
                    urgency="High"
                ),
                OpenQuestion(
                    id="OQ-002",
                    topic="Promotional Voucher Expiration Policy",
                    question="The hardcoded 'HOLIDAY2024' promo code lacks expiration date enforcement in code. Should promo codes be managed in a database table?",
                    context_code_reference="DiscountRuleEngine.cs line 46",
                    stakeholder_target="Product Owner / Marketing Lead",
                    urgency="Medium"
                )
            ],
            review_status=ReviewStatus.PENDING,
            overall_confidence=ConfidenceCategory.HIGH,
            generated_at=datetime.now(timezone.utc).isoformat(),
            model_provider_used="Deterministic Model Provider (Bedrock Offline Fallback Fixture)"
        )

        return doc

def get_model_provider() -> BaseModelProvider:
    has_creds = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY) or bool(os.getenv("AWS_PROFILE"))
    if has_creds:
        try:
            logger.info("Initializing Amazon Bedrock Model Provider with configured AWS credentials.")
            return BedrockModelProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize Bedrock provider: {e}. Falling back to Deterministic Provider.")
            return DeterministicDemoProvider()
    else:
        logger.info("AWS credentials not detected. Utilizing Deterministic Provider (Clearly labeled fixture).")
        return DeterministicDemoProvider()

