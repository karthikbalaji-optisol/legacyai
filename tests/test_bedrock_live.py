import os

import pytest

from backend.app.agents.bedrock_provider import BedrockModelProvider
from backend.app.core.config import settings
from backend.app.schemas.evidence import ScanSummary

has_bedrock_creds = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY) or bool(os.getenv("AWS_PROFILE"))

@pytest.mark.skipif(not has_bedrock_creds, reason="Live AWS Bedrock credentials not detected in environment")
def test_live_bedrock_invocation_smoke():
    """
    Live Amazon Bedrock smoke test executing real AWS API invocation.
    Only runs when real AWS credentials and model access are configured.
    """
    provider = BedrockModelProvider()
    summary = ScanSummary(
        total_files=1, csharp_files=1, total_lines_of_code=50,
        controllers_count=1, services_count=0, models_count=0,
        evidence_count=1, business_rules_count=1, routes_count=1
    )
    brd = provider.generate_brd("live_smoke_analysis", summary, [], [])
    assert brd is not None
    assert brd.project_title is not None
    assert "Bedrock" in brd.model_provider_used
