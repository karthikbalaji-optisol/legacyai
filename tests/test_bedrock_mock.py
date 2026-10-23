import json
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from backend.app.agents.bedrock_provider import (
    BedrockModelProvider,
    _clean_and_parse_json,
    _normalize_brd_payload,
)
from backend.app.schemas.brd import BRDDocument
from backend.app.schemas.evidence import ScanSummary


def test_clean_and_parse_json_handles_preamble_and_markdown():
    preamble_text = (
        "Here is the generated Business Requirements Document based on the provided evidence:\n\n"
        "```json\n"
        "{\n"
        '  "project_title": "Order Processing Enterprise System",\n'
        '  "executive_summary": "Core processing subsystem.",\n'
        '  "business_objectives": ["Process orders quickly"],\n'
        '  "application_scope": "Order lifecycle",\n'
        '  "modules": [],\n'
        '  "actors_and_roles": [],\n'
        '  "functional_requirements": [],\n'
        '  "business_rules": [],\n'
        '  "workflows": [],\n'
        '  "open_questions": []\n'
        "}\n"
        "```\n\n"
        "Please let me know if you would like me to adjust any requirements."
    )
    parsed = _clean_and_parse_json(preamble_text)
    assert parsed["project_title"] == "Order Processing Enterprise System"
    assert len(parsed["business_objectives"]) == 1

def test_clean_and_parse_json_handles_assistant_prefill():
    prefilled_text = (
        '{\n  "project_title": "Prefilled System",\n'
        '  "executive_summary": "Summary",\n'
        '  "business_objectives": [],\n'
        '  "application_scope": "Scope",\n'
        '  "modules": [],\n'
        '  "actors_and_roles": [],\n'
        '  "functional_requirements": [],\n'
        '  "business_rules": [],\n'
        '  "workflows": [],\n'
        '  "open_questions": []\n'
        "}"
    )
    parsed = _clean_and_parse_json(prefilled_text)
    assert parsed["project_title"] == "Prefilled System"

def test_clean_and_parse_json_handles_unclosed_markdown_fence():
    raw = (
        "```json\n"
        "{\n"
        '  "project_title": "Truncated Fence",\n'
        '  "executive_summary": "Summary",\n'
        '  "business_objectives": [],\n'
        '  "application_scope": "Scope",\n'
        '  "modules": [],\n'
        '  "actors_and_roles": [],\n'
        '  "functional_requirements": [],\n'
        '  "business_rules": [],\n'
        '  "workflows": [],\n'
        '  "open_questions": []\n'
        "}"
    )
    parsed = _clean_and_parse_json(raw)
    assert parsed["project_title"] == "Truncated Fence"


def _brd_json_text() -> str:
    return json.dumps({
        "project_title": "From Text Block",
        "executive_summary": "Summary",
        "business_objectives": ["Obj1"],
        "application_scope": "Scope",
        "modules": [],
        "actors_and_roles": [],
        "functional_requirements": [],
        "business_rules": [],
        "workflows": [],
        "open_questions": [],
    })


def test_normalize_brd_payload_maps_loose_model_fields():
    payload = {
        "project_title": "Caliber Data Access",
        "executive_summary": "Encrypts and stores operational data.",
        "business_objectives": ["Protect stored strings"],
        "application_scope": "AES helpers and data access",
        "modules": [
            {"name": "AES Encryption", "classes": ["DecryptStringFromBytes"], "summary": "Encrypts strings"},
            {"name": "Common Data Access", "classes": ["CaliberData"]},
        ],
        "actors_and_roles": [
            {"actor": "Application Controller", "actions": ["Manage async operations"]},
            {"actor": "Database Engine", "permissions": ["Return result sets"]},
        ],
        "workflows": [
            {
                "name": "Secure Data Encryption",
                "steps": [{"name": "Return status", "action": "Return status to caller"}],
            }
        ],
        "functional_requirements": [],
        "business_rules": [],
        "open_questions": [],
        "id": "brd_test",
        "analysis_id": "analysis_test",
        "generated_at": "2026-10-23T00:00:00+00:00",
    }
    document = BRDDocument(**_normalize_brd_payload(payload))
    assert document.modules[0].key_classes == ["DecryptStringFromBytes"]
    assert document.modules[0].source_directory == "AES Encryption"
    assert document.actors_and_roles[0].role_name == "Application Controller"
    assert document.actors_and_roles[0].discovered_permissions == ["Manage async operations"]
    assert document.workflows[0].id == "WF-001"
    assert document.workflows[0].trigger == "Not specified"
    assert document.workflows[0].terminal_states == ["Completed"]
    assert document.workflows[0].steps[0].step_number == 1


def test_generate_brd_reads_text_after_thinking_block():
    with patch("boto3.Session") as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.invoke_model.return_value = {
            "body": MagicMock(read=lambda: json.dumps({
                "content": [
                    {"type": "thinking", "thinking": "planning the document"},
                    {"type": "text", "text": _brd_json_text()},
                ],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 100, "output_tokens": 200},
            }).encode("utf-8"))
        }

        provider = BedrockModelProvider(region_name="us-east-1", model_id="test-model")
        summary = ScanSummary(
            total_files=1, csharp_files=1, total_lines_of_code=10,
            controllers_count=0, services_count=1, models_count=0,
            evidence_count=1, business_rules_count=1, routes_count=0,
        )
        brd = provider.generate_brd("thinking_case", summary, [], [])
        assert brd.project_title == "From Text Block"
        assert mock_client.invoke_model.call_count == 1


def test_bedrock_provider_retry_on_throttling():
    with patch("boto3.Session") as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        throttle_error = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "InvokeModel"
        )
        success_response = {
            "body": MagicMock(read=lambda: json.dumps({
                "content": [{"text": (
                    '"Mock BRD",\n'
                    '"executive_summary": "Test summary",\n'
                    '"business_objectives": ["Obj1"],\n'
                    '"application_scope": "Scope",\n'
                    '"modules": [],\n'
                    '"actors_and_roles": [],\n'
                    '"functional_requirements": [],\n'
                    '"business_rules": [],\n'
                    '"workflows": [],\n'
                    '"open_questions": []\n'
                    '}'
                )}],
                "usage": {"input_tokens": 150, "output_tokens": 300}
            }).encode("utf-8"))
        }

        mock_client.invoke_model.side_effect = [throttle_error, success_response]

        provider = BedrockModelProvider(region_name="us-east-1", model_id="anthropic.claude-3-sonnet-20240229-v1:0")
        summary = ScanSummary(
            total_files=5, csharp_files=5, total_lines_of_code=200,
            controllers_count=1, services_count=2, models_count=2,
            evidence_count=10, business_rules_count=5, routes_count=2
        )
        brd = provider.generate_brd("test_mock", summary, [], [])

        assert brd.project_title == "Mock BRD"
        assert mock_client.invoke_model.call_count == 2
