from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.store import store
from evals.evaluate_demo import evaluate_demo_incident


client = TestClient(app)


def setup_function() -> None:
    store.reset()


def test_invalid_approval_decision_returns_validation_error() -> None:
    response = client.post(
        "/incidents/inc-892-checkout-spike/approvals",
        json={
            "recommendation_id": "rec-rollback-v1419",
            "decision": "execute_without_human",
            "decided_by": "darshan",
            "reason": "This should not be accepted.",
        },
    )

    assert response.status_code == 422


def test_missing_recommendation_approval_returns_404() -> None:
    response = client.post(
        "/incidents/inc-892-checkout-spike/approvals",
        json={
            "recommendation_id": "rec-does-not-exist",
            "decision": "approved",
            "decided_by": "darshan",
            "reason": "Missing recommendation should fail cleanly.",
        },
    )

    assert response.status_code == 404
    assert "Recommendation" in response.json()["detail"]


def test_empty_recommendation_list_cannot_be_approved() -> None:
    store.recommendations["inc-892-checkout-spike"] = []

    response = client.post(
        "/incidents/inc-892-checkout-spike/approvals",
        json={
            "recommendation_id": "rec-rollback-v1419",
            "decision": "approved",
            "decided_by": "darshan",
            "reason": "No recommendation exists in store.",
        },
    )

    assert response.status_code == 404


def test_more_investigation_decision_returns_incident_to_investigating() -> None:
    response = client.post(
        "/incidents/inc-892-checkout-spike/approvals",
        json={
            "recommendation_id": "rec-rollback-v1419",
            "decision": "more_investigation_required",
            "decided_by": "darshan",
            "reason": "Need one more evidence pass.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "investigating"

    incident = client.get("/incidents/inc-892-checkout-spike").json()
    assert incident["current_stage"] == "more_investigation_required"


def test_postmortem_uses_current_incident_state_and_sections() -> None:
    client.post(
        "/incidents/inc-892-checkout-spike/approvals",
        json={
            "recommendation_id": "rec-rollback-v1419",
            "decision": "approved",
            "decided_by": "darshan",
            "reason": "Rollback is aligned with DB pool evidence.",
        },
    )

    response = client.get("/incidents/inc-892-checkout-spike/postmortem")
    body = response.json()
    markdown = body["markdown"]

    assert response.status_code == 200
    assert "## Alert" in markdown
    assert "## Human Approval" in markdown
    assert "approved by darshan" in markdown
    assert "## Evidence" in markdown
    assert "## Timeline" in markdown
    assert "DB pool" in markdown or "DB_POOL_EXHAUSTED" in markdown
    assert len(body["follow_up_actions"]) >= 4


def test_postmortem_uses_latest_changed_mitigation_decision() -> None:
    client.post(
        "/incidents/inc-892-checkout-spike/approvals",
        json={
            "recommendation_id": "rec-rollback-v1419",
            "decision": "approved",
            "decided_by": "darshan",
            "reason": "Initial rollback approval.",
        },
    )
    client.post(
        "/incidents/inc-892-checkout-spike/approvals",
        json={
            "recommendation_id": "rec-scale-db-pool",
            "decision": "approved",
            "decided_by": "darshan",
            "reason": "Changed to DB pool expansion.",
        },
    )

    markdown = client.get("/incidents/inc-892-checkout-spike/postmortem").json()["markdown"]

    assert "Temporarily increase checkout DB pool capacity" in markdown
    assert "Changed to DB pool expansion." in markdown
    assert "current human-selected response is Temporarily increase checkout DB pool capacity" in markdown


def test_demo_eval_harness_passes_expected_checks() -> None:
    results = evaluate_demo_incident()

    assert all(item.passed for item in results)
    assert {item.name for item in results} == {
        "agent_graph_completeness",
        "evidence_source_coverage",
        "root_cause_confidence",
        "human_approval_gate",
        "postmortem_section_coverage",
    }
