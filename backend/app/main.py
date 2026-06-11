from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from backend.app.models import Alert
from backend.app.observability import (
    ACTIVE_INCIDENTS,
    ALERTS_INGESTED_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
    TOTAL_INCIDENTS,
    configure_logging,
    logger,
    new_request_id,
    now_seconds,
    request_id_context,
)
from backend.app.schemas import (
    AlertIngestResponse,
    ApprovalRequest,
    ApprovalResponse,
    HealthResponse,
    ResolveIncidentRequest,
)
from backend.app.store import (
    IncidentNotFoundError,
    LifecycleConflictError,
    RecommendationNotFoundError,
    store,
)


configure_logging()

app = FastAPI(
    title="Agentic AI Incident Commander API",
    description="FastAPI backend for the e-commerce incident response MVP.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_observability(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or new_request_id()
    token = request_id_context.set(request_id)
    start_time = now_seconds()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["x-request-id"] = request_id
        return response
    finally:
        duration = now_seconds() - start_time
        path = request.url.path
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=path,
            status_code=str(status_code),
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            path=path,
        ).observe(duration)
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )
        request_id_context.reset(token)


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="incident-commander-api")


@app.get("/metrics")
def metrics() -> Response:
    incidents = store.list_incidents()
    active_incidents = [
        incident
        for incident in incidents
        if incident.status not in {"closed", "mitigation_recorded"}
    ]
    ACTIVE_INCIDENTS.set(len(active_incidents))
    TOTAL_INCIDENTS.set(len(incidents))
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/alerts", response_model=AlertIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_alert(alert: Alert) -> AlertIngestResponse:
    incident = store.ingest_alert(alert)
    ALERTS_INGESTED_TOTAL.labels(
        source=alert.source,
        service=alert.service,
        severity=alert.severity,
    ).inc()
    return AlertIngestResponse(
        alert=alert,
        incident_id=incident.id,
        status=incident.status,
        message="Alert ingested and incident record is ready for investigation.",
    )


@app.get("/incidents")
def list_incidents():
    return store.list_incidents()


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    try:
        return store.get_incident(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")


@app.get("/incidents/{incident_id}/timeline")
def get_timeline(incident_id: str):
    try:
        return store.get_timeline(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")


@app.get("/incidents/{incident_id}/evidence")
def get_evidence(incident_id: str):
    try:
        return store.get_evidence(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")


@app.get("/incidents/{incident_id}/hypotheses")
def get_hypotheses(incident_id: str):
    try:
        return store.get_hypotheses(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")


@app.get("/incidents/{incident_id}/recommendations")
def get_recommendations(incident_id: str):
    try:
        return store.get_recommendations(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")


@app.get("/incidents/{incident_id}/traces")
def get_traces(incident_id: str):
    try:
        return store.get_traces(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")


@app.post("/incidents/{incident_id}/investigate")
def run_investigation(incident_id: str):
    try:
        return store.run_investigation(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")
    except LifecycleConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@app.post("/incidents/{incident_id}/approvals", response_model=ApprovalResponse)
def create_approval(incident_id: str, request: ApprovalRequest) -> ApprovalResponse:
    try:
        approval = store.record_approval(
            incident_id=incident_id,
            recommendation_id=request.recommendation_id,
            decision=request.decision,
            decided_by=request.decided_by,
            reason=request.reason,
        )
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")
    except RecommendationNotFoundError:
        raise not_found(
            f"Recommendation '{request.recommendation_id}' was not found for incident '{incident_id}'."
        )
    except LifecycleConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return ApprovalResponse(
        incident_id=incident_id,
        recommendation_id=approval.recommendation_id,
        decision=approval.decision,
        status=store.get_incident(incident_id).status,
        message="Approval decision recorded in the incident timeline.",
    )


@app.get("/incidents/{incident_id}/approvals")
def get_approvals(incident_id: str):
    try:
        return store.get_approvals(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")


@app.get("/incidents/{incident_id}/executions")
def get_executions(incident_id: str):
    try:
        return store.get_executions(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")


@app.post("/incidents/{incident_id}/execute-mitigation")
def execute_mitigation(incident_id: str):
    try:
        return store.execute_approved_mitigation(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")
    except RecommendationNotFoundError:
        raise not_found("The approved mitigation recommendation was not found.")
    except LifecycleConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@app.get("/incidents/{incident_id}/recovery-checks")
def get_recovery_checks(incident_id: str):
    try:
        return store.get_recovery_checks(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")


@app.post("/incidents/{incident_id}/monitor-recovery")
def monitor_recovery(incident_id: str):
    try:
        return store.monitor_recovery(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")
    except LifecycleConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@app.post("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: str, request: ResolveIncidentRequest):
    try:
        return store.resolve_incident(incident_id, request.resolved_by)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")
    except LifecycleConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@app.get("/incidents/{incident_id}/postmortem")
def get_postmortem(incident_id: str):
    try:
        return store.get_postmortem(incident_id)
    except IncidentNotFoundError:
        raise not_found(f"Incident '{incident_id}' was not found.")


@app.get("/runbooks")
def list_runbooks():
    return store.list_runbooks()


@app.get("/system-health")
def get_system_health():
    return store.get_system_health()


@app.post("/dev/reset")
def reset_store():
    store.reset()
    return {"status": "ok", "message": "Demo store reset from fixtures."}
