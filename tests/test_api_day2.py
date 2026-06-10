from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.store import store


client = TestClient(app)


def setup_function() -> None:
    store.reset()


def test_health_endpoint() -> None:
    response = client.get("/health", headers={"x-request-id": "req-test-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-test-123"
    assert response.json() == {
        "status": "ok",
        "service": "incident-commander-api",
    }


def test_metrics_endpoint_returns_prometheus_text() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "incident_commander_active_incidents" in response.text
    assert "incident_commander_total_incidents" in response.text
    assert "incident_commander_http_requests_total" in response.text
    assert "incident_commander_workflow_duration_seconds" in response.text


def test_list_and_get_seeded_incident() -> None:
    list_response = client.get("/incidents")

    assert list_response.status_code == 200
    incidents = list_response.json()
    assert len(incidents) == 1
    assert incidents[0]["id"] == "inc-892-checkout-spike"

    detail_response = client.get("/incidents/inc-892-checkout-spike")
    assert detail_response.status_code == 200
    assert detail_response.json()["affected_service"] == "checkout-api"


def test_incident_context_endpoints_return_seeded_data() -> None:
    incident_id = "inc-892-checkout-spike"

    assert len(client.get(f"/incidents/{incident_id}/timeline").json()) >= 9
    assert len(client.get(f"/incidents/{incident_id}/evidence").json()) >= 6
    assert len(client.get(f"/incidents/{incident_id}/hypotheses").json()) >= 2
    assert len(client.get(f"/incidents/{incident_id}/recommendations").json()) >= 3
    assert len(client.get(f"/incidents/{incident_id}/traces").json()) == 9


def test_ingest_alert_creates_new_incident() -> None:
    payload = {
        "id": "alert-inventory-001",
        "source": "mock_grafana",
        "service": "inventory-api",
        "severity": "high",
        "metric_name": "error_rate_percent",
        "metric_value": 7.2,
        "threshold": 3.0,
        "started_at": "2026-06-09T15:00:00Z",
        "description": "Inventory API error rate exceeded threshold.",
        "raw_payload": {"environment": "production"},
    }

    response = client.post("/alerts", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["alert"]["id"] == "alert-inventory-001"
    assert body["incident_id"].startswith("inc-")
    assert body["status"] == "waiting_for_approval"


def test_record_approval_updates_incident_and_timeline() -> None:
    incident_id = "inc-892-checkout-spike"
    response = client.post(
        f"/incidents/{incident_id}/approvals",
        json={
            "recommendation_id": "rec-rollback-v1419",
            "decision": "approved",
            "decided_by": "darshan",
            "reason": "Rollback is aligned with evidence.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "mitigation_recorded"

    incident = client.get(f"/incidents/{incident_id}").json()
    assert incident["current_stage"] == "mitigation_approved"

    timeline = client.get(f"/incidents/{incident_id}/timeline").json()
    assert any(item["stage"] == "mitigation_approved" for item in timeline)


def test_postmortem_endpoint_returns_markdown_report() -> None:
    response = client.get("/incidents/inc-892-checkout-spike/postmortem")

    assert response.status_code == 200
    body = response.json()
    assert body["incident_id"] == "inc-892-checkout-spike"
    assert "Incident Postmortem" in body["markdown"]
    assert "Likely Root Cause" in body["markdown"]


def test_dashboard_support_endpoints_return_runbooks_and_health() -> None:
    runbooks = client.get("/runbooks")
    health = client.get("/system-health")

    assert runbooks.status_code == 200
    assert len(runbooks.json()) == 4
    assert health.status_code == 200
    assert health.json()["status"] == "degraded"


def test_unknown_incident_returns_404() -> None:
    response = client.get("/incidents/missing-incident")

    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]
