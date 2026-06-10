from __future__ import annotations

from sqlalchemy import text

from backend.app.config import load_settings
from backend.app.data_loader import load_runbook_chunks
from backend.app.database import build_engine, build_session_factory
from backend.app.embeddings import build_embedding_provider
from backend.app.repository import DatabaseIncidentRepository
from backend.app.seed_database import run_migrations
from backend.app.store import IncidentStore


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.6f}" for value in values) + "]"


def update_pgvector_column(database_url: str, chunk_embeddings: dict[str, list[float]]) -> None:
    engine = build_engine(database_url)
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        for chunk_id, embedding in chunk_embeddings.items():
            connection.execute(
                text(
                    "UPDATE runbook_chunks "
                    "SET embedding_vector = CAST(:embedding AS vector) "
                    "WHERE id = :chunk_id"
                ),
                {"embedding": vector_literal(embedding), "chunk_id": chunk_id},
            )


def ingest_runbooks() -> list[str]:
    settings = load_settings()
    run_migrations(settings.database_url)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    repository = DatabaseIncidentRepository(session_factory)
    store = IncidentStore(repository=repository)

    provider = build_embedding_provider()
    chunks = load_runbook_chunks()
    texts = [
        " ".join(
            [
                chunk.runbook_title,
                chunk.section_title,
                chunk.content,
                chunk.service,
                " ".join(chunk.tags),
            ]
        )
        for chunk in chunks
    ]
    embeddings = provider.embed_texts(texts)
    embedded_chunks = [
        chunk.model_copy(update={"embedding": embedding})
        for chunk, embedding in zip(chunks, embeddings)
    ]

    snapshot = repository.load_snapshot() if repository.has_incidents() else store._snapshot()
    snapshot.runbook_chunks = embedded_chunks
    repository.replace_snapshot(snapshot)
    update_pgvector_column(
        settings.database_url,
        {chunk.id: chunk.embedding for chunk in embedded_chunks},
    )
    return [chunk.id for chunk in embedded_chunks]


def main() -> None:
    chunk_ids = ingest_runbooks()
    print(f"Ingested {len(chunk_ids)} runbook chunks with embeddings.")
    print("First chunks: " + ", ".join(chunk_ids[:5]))


if __name__ == "__main__":
    main()
