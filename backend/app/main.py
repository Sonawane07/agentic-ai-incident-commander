from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from backend.app.models import Alert
from backend.app.schemas import (
    AlertIngestResponse,
    ApprovalRequest,
    ApprovalResponse,
    HealthResponse,
)
from backend.app.store import (
    IncidentNotFoundError,
    RecommendationNotFoundError,
    store,
)


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
    body = "\n".join(
        [
            "# HELP incident_commander_active_incidents Active incidents currently tracked by the demo store.",
            "# TYPE incident_commander_active_incidents gauge",
            f"incident_commander_active_incidents {len(active_incidents)}",
            "# HELP incident_commander_total_incidents Total incidents currently tracked by the demo store.",
            "# TYPE incident_commander_total_incidents gauge",
            f"incident_commander_total_incidents {len(incidents)}",
            "",
        ]
    )
    return Response(content=body, media_type="text/plain; version=0.0.4")


@app.post("/alerts", response_model=AlertIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_alert(alert: Alert) -> AlertIngestResponse:
    incident = store.ingest_alert(alert)
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
