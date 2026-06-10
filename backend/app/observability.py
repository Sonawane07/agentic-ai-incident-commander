from __future__ import annotations

import json
import logging
import sys
import time
from contextvars import ContextVar
from uuid import uuid4

from prometheus_client import Counter, Gauge, Histogram


request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_context.get()),
        }
        for field in (
            "method",
            "path",
            "status_code",
            "duration_ms",
            "incident_id",
            "agent_name",
            "decision",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if any(isinstance(handler.formatter, JsonFormatter) for handler in root_logger.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)


logger = logging.getLogger("incident_commander")


HTTP_REQUESTS_TOTAL = Counter(
    "incident_commander_http_requests_total",
    "Total HTTP requests handled by the API.",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "incident_commander_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)
ALERTS_INGESTED_TOTAL = Counter(
    "incident_commander_alerts_ingested_total",
    "Total alerts ingested by the incident commander.",
    ["source", "service", "severity"],
)
WORKFLOW_DURATION_SECONDS = Histogram(
    "incident_commander_workflow_duration_seconds",
    "LangGraph investigation workflow duration in seconds.",
    ["service"],
)
AGENT_STEP_DURATION_SECONDS = Histogram(
    "incident_commander_agent_step_duration_seconds",
    "Individual LangGraph agent node duration in seconds.",
    ["agent_name"],
)
EVIDENCE_ITEMS = Gauge(
    "incident_commander_evidence_items",
    "Current evidence item count per incident.",
    ["incident_id", "service"],
)
APPROVAL_DECISIONS_TOTAL = Counter(
    "incident_commander_approval_decisions_total",
    "Human approval decisions recorded.",
    ["decision"],
)
POSTMORTEMS_GENERATED_TOTAL = Counter(
    "incident_commander_postmortems_generated_total",
    "Postmortem documents generated.",
)
ACTIVE_INCIDENTS = Gauge(
    "incident_commander_active_incidents",
    "Active incidents currently tracked by the demo store.",
)
TOTAL_INCIDENTS = Gauge(
    "incident_commander_total_incidents",
    "Total incidents currently tracked by the demo store.",
)


def new_request_id() -> str:
    return f"req-{uuid4().hex[:12]}"


def current_request_id() -> str:
    return request_id_context.get()


def now_seconds() -> float:
    return time.perf_counter()
