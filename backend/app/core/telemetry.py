from prometheus_client import Counter, Gauge, Histogram

# Prometheus Metrics
ANALYSIS_TOTAL = Counter(
    "legacylens_analysis_total",
    "Total number of repository analyses started",
    ["status"]
)

ANALYSIS_DURATION_SECONDS = Histogram(
    "legacylens_analysis_duration_seconds",
    "Duration of complete analysis pipeline in seconds",
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

EVIDENCE_EXTRACTED_TOTAL = Counter(
    "legacylens_evidence_extracted_total",
    "Count of deterministic evidence items extracted",
    ["category"]
)

EVIDENCE_VALIDATION_SCORE = Gauge(
    "legacylens_evidence_validation_score_ratio",
    "Ratio of requirements with validated source citations",
    ["analysis_id"]
)

BEDROCK_INVOCATIONS_TOTAL = Counter(
    "legacylens_bedrock_invocations_total",
    "Total Bedrock API calls",
    ["model_id", "status"]
)

BEDROCK_TOKEN_USAGE_TOTAL = Counter(
    "legacylens_bedrock_tokens_total",
    "Total Bedrock tokens consumed",
    ["type"]  # prompt / completion
)

# OpenTelemetry tracer wrapper
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider

    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("legacylens", "1.0.0")
except Exception:
    tracer = None

def get_tracer():
    return tracer
