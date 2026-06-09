from __future__ import annotations

import re
from dataclasses import dataclass

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
        results: list[RunbookSearchResult] = []

        for chunk in chunks:
            chunk_text = " ".join(
                [
                    chunk.runbook_title,
                    chunk.section_title,
                    chunk.content,
                    chunk.service,
                    " ".join(chunk.tags),
                ]
            )
            chunk_terms = expand_terms(tokenize(chunk_text))
            matched_terms = sorted(query_terms & chunk_terms)
            if not matched_terms:
                continue

            lexical_score = len(matched_terms) / max(len(query_terms), 1)
            service_boost = 0.18 if chunk.service == incident.affected_service else 0.0
            title_boost = 0.08 if any(term in chunk.runbook_title.lower() for term in matched_terms) else 0.0
            section_boost = 0.06 if any(term in chunk.section_title.lower() for term in matched_terms) else 0.0
            score = min(0.99, 0.45 + lexical_score + service_boost + title_boost + section_boost)
            results.append(
                RunbookSearchResult(
                    chunk=chunk,
                    score=round(score, 3),
                    matched_terms=matched_terms,
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
