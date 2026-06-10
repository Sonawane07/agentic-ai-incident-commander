from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.data_loader import load_demo_data
from backend.app.main import app
from backend.app.store import store
from backend.app.workflow import AgenticInvestigationWorkflow


client = TestClient(app)


def setup_function() -> None:
    store.reset()


def test_seeded_incident_runs_agentic_workflow() -> None:
    incident_id = "inc-892-checkout-spike"

    incident = client.get(f"/incidents/{incident_id}").json()
    assert incident["status"] == "waiting_for_approval"
    assert incident["current_stage"] == "approval_required"

    timeline = client.get(f"/incidents/{incident_id}/timeline").json()
    stages = {item["stage"] for item in timeline}
    assert "metrics_agent_completed" in stages
    assert "logs_agent_completed" in stages
    assert "github_deploy_agent_completed" in stages
    assert "runbook_rag_agent_completed" in stages
    assert "evidence_ranking_agent_completed" in stages
    assert "root_cause_agent_completed" in stages
    assert "mitigation_agent_completed" in stages
    assert "approval_required" in stages


def test_workflow_traces_capture_each_agent_step() -> None:
    traces = client.get("/incidents/inc-892-checkout-spike/traces").json()

    assert len(traces) == 9
    agent_names = [trace["agent_name"] for trace in traces]
    assert agent_names == [
        "Alert Intake Agent",
        "Metrics Agent",
        "Logs Agent",
        "Github Deploy Agent",
        "Runbook Rag Agent",
        "Evidence Ranking Agent",
        "Root Cause Agent",
        "Mitigation Agent",
        "Approval Agent",
    ]
    assert all(trace["status"] == "completed" for trace in traces)
    assert all(trace["input_summary"] for trace in traces)
    assert all(trace["output_summary"] for trace in traces)


def test_workflow_is_backed_by_real_langgraph_state_graph() -> None:
    workflow = AgenticInvestigationWorkflow()

    assert workflow.is_langgraph_backed is True
    assert "langgraph" in type(workflow.graph).__module__


def test_langgraph_executes_expected_agent_nodes_in_order() -> None:
    demo_data = load_demo_data()
    workflow = AgenticInvestigationWorkflow()

    state = workflow.run(demo_data.incidents[0], demo_data)

    assert state.graph_nodes_executed == [
        "alert_intake",
        "metrics",
        "logs",
        "github_deploy",
        "runbook_rag",
        "evidence_ranking",
        "root_cause",
        "mitigation",
        "approval",
    ]
    assert len(state.traces) == 9


def test_workflow_generates_evidence_backed_hypotheses_and_recommendations() -> None:
    incident_id = "inc-892-checkout-spike"

    evidence = client.get(f"/incidents/{incident_id}/evidence").json()
    source_types = {item["source_type"] for item in evidence}
    assert {"metric", "log", "deployment", "github_commit", "runbook"} <= source_types

    hypotheses = client.get(f"/incidents/{incident_id}/hypotheses").json()
    top_hypothesis = hypotheses[0]
    assert top_hypothesis["id"] == "hyp-db-pool-after-retry"
    assert top_hypothesis["confidence"] >= 0.8
    assert len(top_hypothesis["supporting_evidence_ids"]) >= 4

    recommendations = client.get(f"/incidents/{incident_id}/recommendations").json()
    assert recommendations[0]["id"] == "rec-rollback-v1419"
    assert recommendations[0]["requires_approval"] is True


def test_manual_investigation_rerun_refreshes_trace_records() -> None:
    incident_id = "inc-892-checkout-spike"
    before = client.get(f"/incidents/{incident_id}/traces").json()

    response = client.post(f"/incidents/{incident_id}/investigate")

    assert response.status_code == 200
    after = client.get(f"/incidents/{incident_id}/traces").json()
    assert len(after) == 9
    assert after[0]["id"] != before[0]["id"]
