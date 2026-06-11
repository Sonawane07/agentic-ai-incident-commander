from __future__ import annotations

from pydantic import BaseModel

from backend.app.models import Alert, ApprovalDecisionValue


class HealthResponse(BaseModel):
    status: str
    service: str


class AlertIngestResponse(BaseModel):
    alert: Alert
    incident_id: str
    status: str
    message: str


class ApprovalRequest(BaseModel):
    recommendation_id: str
    decision: ApprovalDecisionValue
    decided_by: str = "on-call-engineer"
    reason: str = ""


class ApprovalResponse(BaseModel):
    incident_id: str
    recommendation_id: str
    decision: ApprovalDecisionValue
    status: str
    message: str


class ResolveIncidentRequest(BaseModel):
    resolved_by: str = "on-call-engineer"
