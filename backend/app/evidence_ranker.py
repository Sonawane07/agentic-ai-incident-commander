from __future__ import annotations

import re
from collections import Counter
from datetime import datetime

from backend.app.models import Evidence, EvidenceSourceType, Incident


SIGNAL_PATTERN = re.compile(
    r"db_pool|pool|timeout|retry|rollback|deployment|payment|latency|checkout|database",
    re.IGNORECASE,
)

SOURCE_WEIGHT = {
    EvidenceSourceType.METRIC: 0.95,
    EvidenceSourceType.LOG: 0.93,
    EvidenceSourceType.DEPLOYMENT: 0.86,
    EvidenceSourceType.GITHUB_COMMIT: 0.84,
    EvidenceSourceType.RUNBOOK: 0.78,
    EvidenceSourceType.TRACE: 0.76,
    EvidenceSourceType.HUMAN_DECISION: 0.72,
}


class EvidenceRanker:
    def rank(self, evidence: list[Evidence], incident: Incident) -> list[Evidence]:
        signal_counts = self._signal_counts(evidence)
        ranked = [
            item.model_copy(
                update={
                    "relevance_score": self.score_evidence(
                        item,
                        incident=incident,
                        signal_counts=signal_counts,
                    )
                }
            )
            for item in evidence
        ]
        return sorted(
            ranked,
            key=lambda item: (item.relevance_score, item.confidence, item.timestamp),
            reverse=True,
        )

    def score_evidence(
        self,
        evidence: Evidence,
        incident: Incident,
        signal_counts: Counter[str],
    ) -> float:
        service_score = self._service_match(evidence, incident)
        time_score = self._time_proximity(evidence.timestamp, incident.created_at)
        severity_score = self._severity_score(evidence)
        agreement_score = self._source_agreement(evidence, signal_counts)
        source_score = SOURCE_WEIGHT.get(evidence.source_type, 0.7)

        score = (
            evidence.relevance_score * 0.28
            + evidence.confidence * 0.2
            + service_score * 0.16
            + time_score * 0.16
            + severity_score * 0.12
            + agreement_score * 0.08
            + source_score * 0.08
        )
        return round(min(score, 0.99), 3)

    def _signal_counts(self, evidence: list[Evidence]) -> Counter[str]:
        counter: Counter[str] = Counter()
        for item in evidence:
            signals = {match.group(0).lower() for match in SIGNAL_PATTERN.finditer(item.summary)}
            for signal in signals:
                counter[signal] += 1
        return counter

    def _service_match(self, evidence: Evidence, incident: Incident) -> float:
        text = f"{evidence.source_name} {evidence.summary} {evidence.raw_reference}".lower()
        service = incident.affected_service.lower()
        service_family = service.split("-")[0]
        if service in text:
            return 1.0
        if service_family and service_family in text:
            return 0.82
        return 0.35

    def _time_proximity(self, evidence_time: datetime, incident_time: datetime) -> float:
        delta_minutes = abs((evidence_time - incident_time).total_seconds()) / 60
        if delta_minutes <= 10:
            return 1.0
        if delta_minutes <= 30:
            return 0.82
        if delta_minutes <= 24 * 60:
            return 0.55
        return 0.32

    def _severity_score(self, evidence: Evidence) -> float:
        text = evidence.summary.lower()
        if "db_pool_exhausted" in text or "98 percent" in text or "99 percent" in text:
            return 1.0
        if "timeout" in text or "failure" in text or "critical" in text:
            return 0.86
        if "deployment" in text or "retry" in text or "rollback" in text:
            return 0.74
        return 0.48

    def _source_agreement(self, evidence: Evidence, signal_counts: Counter[str]) -> float:
        signals = {match.group(0).lower() for match in SIGNAL_PATTERN.finditer(evidence.summary)}
        if not signals:
            return 0.35
        repeated = [signal for signal in signals if signal_counts[signal] >= 2]
        return min(1.0, 0.45 + len(repeated) * 0.18)
