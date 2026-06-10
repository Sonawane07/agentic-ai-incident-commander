from __future__ import annotations

from backend.app.data_loader import load_demo_data
from backend.app.database import build_engine, build_session_factory
from backend.app.embeddings import DeterministicHashEmbeddingProvider, cosine_similarity
from backend.app.ingest_runbooks import ingest_runbooks
from backend.app.repository import DatabaseIncidentRepository
from backend.app.retrieval import RunbookRetriever, runbook_chunk_text


def test_hash_embedding_provider_is_deterministic_and_normalized() -> None:
    provider = DeterministicHashEmbeddingProvider()

    first = provider.embed_text("checkout latency db pool timeout")
    second = provider.embed_text("checkout latency db pool timeout")
    unrelated = provider.embed_text("team access permissions audit")

    assert first == second
    assert len(first) == 384
    assert cosine_similarity(first, second) > 0.99
    assert cosine_similarity(first, unrelated) < 0.5


def test_hybrid_retriever_returns_score_breakdown_with_embedded_chunks() -> None:
    data = load_demo_data()
    incident = data.incidents[0]
    provider = DeterministicHashEmbeddingProvider()
    embedded_chunks = [
        chunk.model_copy(update={"embedding": provider.embed_text(runbook_chunk_text(chunk))})
        for chunk in data.runbook_chunks
    ]
    retriever = RunbookRetriever(embedding_provider=provider)

    results = retriever.search(
        incident=incident,
        chunks=embedded_chunks,
        evidence_summaries=[
            "DB_POOL_EXHAUSTED while reserving cart inventory.",
            "Payment authorization timeout after deployment v1.42.0.",
        ],
        top_k=4,
    )

    assert len(results) == 4
    assert results[0].score >= results[-1].score
    assert all(result.vector_score > 0 for result in results)
    assert all(result.lexical_score > 0 for result in results)
    assert "Database Connection Pool" in {result.chunk.runbook_title for result in results}


def test_runbook_ingestion_persists_embeddings_to_database(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite:///{tmp_path / 'rag_ingestion.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")

    chunk_ids = ingest_runbooks()

    repository = DatabaseIncidentRepository(
        build_session_factory(build_engine(database_url))
    )
    snapshot = repository.load_snapshot()

    assert len(chunk_ids) == len(snapshot.runbook_chunks)
    assert snapshot.runbook_chunks
    assert all(len(chunk.embedding) == 384 for chunk in snapshot.runbook_chunks)
    assert snapshot.incidents["inc-892-checkout-spike"].affected_service == "checkout-api"
