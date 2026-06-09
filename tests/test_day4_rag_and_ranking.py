from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.data_loader import load_demo_data
from backend.app.evidence_ranker import EvidenceRanker
from backend.app.main import app
from backend.app.retrieval import RunbookRetriever
from backend.app.store import store


client = TestClient(app)


def setup_function() -> None:
    store.reset()


def test_runbook_retriever_returns_relevant_checkout_incident_chunks() -> None:
    data = load_demo_data()
    incident = data.incidents[0]
    retriever = RunbookRetriever()

    results = retriever.search(
        incident=incident,
        chunks=data.runbook_chunks,
        evidence_summaries=[
            "DB_POOL_EXHAUSTED while reserving cart inventory.",
            "Payment authorization timeout after deployment v1.42.0.",
        ],
        top_k=4,
    )

    titles = {result.chunk.runbook_title for result in results}
    assert "Database Connection Pool" in titles
    assert "Checkout Latency" in titles
    assert len(results) == 4
    assert results[0].score >= results[-1].score
    assert all(result.matched_terms for result in results)


def test_evidence_ranker_promotes_high_signal_incident_evidence() -> None:
    incident_id = "inc-892-checkout-spike"
    incident = store.get_incident(incident_id)
    evidence = store.get_evidence(incident_id)
    ranker = EvidenceRanker()

    ranked = ranker.rank(evidence, incident)

    assert ranked[0].relevance_score >= ranked[-1].relevance_score
    assert any("DB_POOL_EXHAUSTED" in item.summary for item in ranked[:5])
    assert any(item.source_type == "metric" for item in ranked[:5])


def test_workflow_exposes_ranked_evidence_and_rag_metadata() -> None:
    incident_id = "inc-892-checkout-spike"

    evidence = client.get(f"/incidents/{incident_id}/evidence").json()
    scores = [item["relevance_score"] for item in evidence]
    assert scores == sorted(scores, reverse=True)

    timeline = client.get(f"/incidents/{incident_id}/timeline").json()
    rag_event = next(item for item in timeline if item["stage"] == "runbook_rag_agent_completed")
    ranking_event = next(
        item for item in timeline if item["stage"] == "evidence_ranking_agent_completed"
    )

    assert len(rag_event["metadata"]["retrieved_chunk_ids"]) == 4
    assert rag_event["metadata"]["top_score"] > 0
    assert len(ranking_event["metadata"]["top_evidence_ids"]) == 5
