# LegacyLens AI — Observability & Telemetry

## 1. Metrics & Prometheus Exporter

LegacyLens AI provides real-time application metrics exposed at `/metrics`:

- `legacylens_analysis_total`: Total repository analyses categorized by status (`started`, `completed`, `failed`).
- `legacylens_analysis_duration_seconds`: Histogram of end-to-end pipeline execution latency.
- `legacylens_evidence_extracted_total`: Count of extracted evidence items partitioned by category (`business_rule`, `threshold`, `route`, `authorization`, etc.).
- `legacylens_evidence_validation_score_ratio`: Ratio of requirements with verified evidence citations.
- `legacylens_bedrock_invocations_total`: Amazon Bedrock API invocations partitioned by model ID and status.
- `legacylens_bedrock_tokens_total`: Total prompt and completion tokens tracked.

## 2. Distributed Tracing & Request Correlation

- **Correlation IDs**: All incoming HTTP requests receive an `X-Request-ID` header.
- **Trace Propagation**: Correlation IDs are attached to structured log messages and LangGraph workflow spans.
- **OpenTelemetry SDK**: Configured TracerProvider with spans tracing code extraction, MCP tool calls, and model invocations.
- **LangSmith**: Optional LangSmith tracing integration enabled via `LANGSMITH_TRACING=true`.

## 3. Structured JSON Logging

All logs output single-line JSON format adhering to:
```json
{
  "timestamp": "2026-10-23T12:00:00.000Z",
  "level": "INFO",
  "logger": "legacylens",
  "message": "Repository scan completed: 6 C# files, 43 symbols, 64 evidence items.",
  "module": "csharp_scanner",
  "function": "scan_all",
  "line": 99,
  "request_id": "c7a8b9-...",
  "analysis_id": "f1e2d3-..."
}
```
Credentials and sensitive headers are redacted before emission.
