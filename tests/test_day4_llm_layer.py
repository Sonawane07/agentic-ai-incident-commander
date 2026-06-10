from __future__ import annotations

import httpx

from backend.app.data_loader import load_demo_data
from backend.app.llm import (
    DeterministicLLMProvider,
    LLMRequest,
    build_llm_provider,
)
from backend.app.store import IncidentStore
from backend.app.workflow import AgenticInvestigationWorkflow


def test_deterministic_llm_provider_returns_stable_incident_text() -> None:
    provider = DeterministicLLMProvider()

    first = provider.generate(LLMRequest(task="root_cause", prompt="checkout db pool"))
    second = provider.generate(LLMRequest(task="root_cause", prompt="checkout db pool"))

    assert first.text == second.text
    assert first.provider == "deterministic"
    assert first.model == "rules-v1"
    assert first.fallback_used is False
    assert "database connection pool" in first.text


def test_ollama_provider_uses_local_generate_endpoint(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return httpx.Response(
            200,
            json={"response": "Ollama generated incident summary."},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1")
    monkeypatch.setattr("backend.app.llm.httpx.post", fake_post)

    provider = build_llm_provider()
    response = provider.generate(LLMRequest(task="mitigation", prompt="rollback?"))

    assert response.text == "Ollama generated incident summary."
    assert response.provider == "ollama"
    assert response.model == "llama3.1"
    assert response.fallback_used is False
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["json"]["stream"] is False


def test_ollama_provider_falls_back_when_local_model_is_unavailable(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        raise httpx.ConnectError("Ollama is not running")

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setattr("backend.app.llm.httpx.post", fake_post)

    provider = build_llm_provider()
    response = provider.generate(LLMRequest(task="postmortem", prompt="write summary"))

    assert response.provider == "deterministic"
    assert response.fallback_used is True
    assert "approval-gated rollback" in response.text


def test_workflow_records_llm_provider_metadata_in_timeline(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "deterministic")
    data = load_demo_data()
    workflow = AgenticInvestigationWorkflow()

    state = workflow.run(data.incidents[0], data)
    root_cause_event = next(
        item for item in state.timeline if item.stage == "root_cause_agent_completed"
    )
    mitigation_event = next(
        item for item in state.timeline if item.stage == "mitigation_agent_completed"
    )

    assert root_cause_event.metadata["llm_provider"] == "deterministic"
    assert mitigation_event.metadata["llm_provider"] == "deterministic"
    assert state.hypotheses[0].description
    assert state.recommendations[0].description


def test_postmortem_includes_llm_generated_executive_summary(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "deterministic")
    store = IncidentStore(demo_data=load_demo_data())

    postmortem = store.get_postmortem("inc-892-checkout-spike")

    assert "retry fanout" in postmortem.markdown
    assert "## Follow-Up Actions" in postmortem.markdown
