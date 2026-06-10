from __future__ import annotations

import re
from dataclasses import dataclass

from backend.app.embeddings import (
    EmbeddingProvider,
    build_embedding_provider,
    cosine_similarity,
)
from backend.app.models import Incident, RunbookChunk


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


DOMAIN_SYNONYMS = {
    "checkout": {"checkout", "cart", "order"},
    "latency": {"latency", "slow", "wait", "timeout", "p95"},
    "payment": {"payment", "authorization", "provider", "auth"},
    "database": {"database", "db", "connection", "pool"},
    "rollback": {"rollback", "deploy", "deployment", "version"},
}


@dataclass(frozen=True)
class RunbookSearchResult:
    chunk: RunbookChunk
    score: float
    matched_terms: list[str]
    lexical_score: float = 0.0
    vector_score: float = 0.0
    service_score: float = 0.0
    incident_relevance_score: float = 0.0


def tokenize(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


def expand_terms(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for canonical, synonyms in DOMAIN_SYNONYMS.items():
        if tokens & synonyms:
            expanded.add(canonical)
            expanded.update(synonyms)
    return expanded


class RunbookRetriever:
    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or build_embedding_provider()

    def search(
        self,
        incident: Incident,
        chunks: list[RunbookChunk],
        evidence_summaries: list[str],
        top_k: int = 4,
    ) -> list[RunbookSearchResult]:
        query_text = " ".join(
            [
                incident.title,
                incident.summary,
                incident.affected_service,
                *evidence_summaries,
            ]
        )
        query_terms = expand_terms(tokenize(query_text))
        query_embedding = self.embedding_provider.embed_text(query_text)
        results: list[RunbookSearchResult] = []

        for chunk in chunks:
            chunk_text = runbook_chunk_text(chunk)
            chunk_terms = expand_terms(tokenize(chunk_text))
            matched_terms = sorted(query_terms & chunk_terms)

            chunk_embedding = (
                chunk.embedding
                if chunk.embedding
                else self.embedding_provider.embed_text(chunk_text)
            )
            vector_score = max(0.0, cosine_similarity(query_embedding, chunk_embedding))
            if not matched_terms and vector_score < 0.2:
                continue

            lexical_score = min(1.0, len(matched_terms) / 8)
            service_score = 1.0 if chunk.service == incident.affected_service else 0.0
            incident_relevance_score = self._incident_relevance_score(
                incident=incident,
                chunk=chunk,
                matched_terms=matched_terms,
            )
            score = min(
                0.99,
                (
                    0.36 * lexical_score
                    + 0.34 * vector_score
                    + 0.18 * service_score
                    + 0.12 * incident_relevance_score
                ),
            )
            results.append(
                RunbookSearchResult(
                    chunk=chunk,
                    score=round(score, 3),
                    matched_terms=matched_terms,
                    lexical_score=round(lexical_score, 3),
                    vector_score=round(vector_score, 3),
                    service_score=round(service_score, 3),
                    incident_relevance_score=round(incident_relevance_score, 3),
                )
            )

        sorted_results = sorted(results, key=lambda result: result.score, reverse=True)
        selected: list[RunbookSearchResult] = []
        seen_titles: set[str] = set()

        for result in sorted_results:
            if result.chunk.runbook_title in seen_titles:
                continue
            selected.append(result)
            seen_titles.add(result.chunk.runbook_title)
            if len(selected) == top_k:
                return selected

        for result in sorted_results:
            if result in selected:
                continue
            selected.append(result)
            if len(selected) == top_k:
                break

        return selected

    def _incident_relevance_score(
        self,
        incident: Incident,
        chunk: RunbookChunk,
        matched_terms: list[str],
    ) -> float:
        title_and_section = f"{chunk.runbook_title} {chunk.section_title}".lower()
        incident_text = f"{incident.title} {incident.summary} {incident.affected_service}".lower()
        score = 0.0
        if "checkout" in title_and_section and "checkout" in incident_text:
            score += 0.35
        if "database" in title_and_section or "pool" in title_and_section:
            score += 0.25
        if "latency" in title_and_section and "latency" in incident_text:
            score += 0.2
        if "rollback" in title_and_section:
            score += 0.1
        if {"database", "db", "pool"} & set(matched_terms):
            score += 0.1
        return min(1.0, score)


def runbook_chunk_text(chunk: RunbookChunk) -> str:
    return " ".join(
        [
            chunk.runbook_title,
            chunk.section_title,
            chunk.content,
            chunk.service,
            " ".join(chunk.tags),
        ]
    )
