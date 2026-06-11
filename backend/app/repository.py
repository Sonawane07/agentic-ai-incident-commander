from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models import (
    AgentTrace,
    Alert,
    ApprovalDecision,
    Evidence,
    Hypothesis,
    Incident,
    MitigationExecution,
    MitigationRecommendation,
    Postmortem,
    RecoveryCheck,
    RunbookChunk,
    TimelineEvent,
)
from backend.app.orm import (
    AgentTraceRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    EvidenceRecord,
    HypothesisRecord,
    IncidentRecord,
    MitigationExecutionRecord,
    MitigationRecommendationRecord,
    PostmortemRecord,
    RecoveryCheckRecord,
    RunbookChunkRecord,
    TimelineEventRecord,
)


ModelT = TypeVar("ModelT")


@dataclass
class IncidentRepositorySnapshot:
    alerts: dict[str, Alert] = field(default_factory=dict)
    incidents: dict[str, Incident] = field(default_factory=dict)
    evidence: dict[str, list[Evidence]] = field(default_factory=dict)
    hypotheses: dict[str, list[Hypothesis]] = field(default_factory=dict)
    recommendations: dict[str, list[MitigationRecommendation]] = field(default_factory=dict)
    approvals: dict[str, list[ApprovalDecision]] = field(default_factory=dict)
    executions: dict[str, list[MitigationExecution]] = field(default_factory=dict)
    recovery_checks: dict[str, list[RecoveryCheck]] = field(default_factory=dict)
    postmortems: dict[str, Postmortem] = field(default_factory=dict)
    timeline: dict[str, list[TimelineEvent]] = field(default_factory=dict)
    traces: dict[str, list[AgentTrace]] = field(default_factory=dict)
    runbook_chunks: list[RunbookChunk] = field(default_factory=list)


class DatabaseIncidentRepository:
    def __init__(self, session_factory: sessionmaker) -> None:
        self.session_factory = session_factory

    def has_incidents(self) -> bool:
        with self.session_factory() as session:
            return session.scalar(select(IncidentRecord.id).limit(1)) is not None

    def load_snapshot(self) -> IncidentRepositorySnapshot:
        with self.session_factory() as session:
            return IncidentRepositorySnapshot(
                alerts={
                    item.id: self._to_alert(item)
                    for item in session.scalars(select(AlertRecord)).all()
                },
                incidents={
                    item.id: self._to_incident(item)
                    for item in session.scalars(select(IncidentRecord)).all()
                },
                evidence=self._group_by_incident(
                    session,
                    EvidenceRecord,
                    Evidence,
                    order_by=EvidenceRecord.relevance_score.desc(),
                ),
                hypotheses=self._group_by_incident(
                    session,
                    HypothesisRecord,
                    Hypothesis,
                    order_by=HypothesisRecord.confidence.desc(),
                ),
                recommendations=self._group_by_incident(
                    session,
                    MitigationRecommendationRecord,
                    MitigationRecommendation,
                    order_by=MitigationRecommendationRecord.confidence.desc(),
                ),
                approvals=self._group_by_incident(
                    session,
                    ApprovalDecisionRecord,
                    ApprovalDecision,
                    order_by=ApprovalDecisionRecord.created_at.asc(),
                ),
                executions=self._group_by_incident(
                    session,
                    MitigationExecutionRecord,
                    MitigationExecution,
                    order_by=MitigationExecutionRecord.started_at.asc(),
                ),
                recovery_checks=self._group_by_incident(
                    session,
                    RecoveryCheckRecord,
                    RecoveryCheck,
                    order_by=RecoveryCheckRecord.checked_at.asc(),
                ),
                postmortems={
                    item.incident_id: self._to_postmortem(item)
                    for item in session.scalars(select(PostmortemRecord)).all()
                },
                timeline=self._group_by_incident(
                    session,
                    TimelineEventRecord,
                    TimelineEvent,
                    order_by=TimelineEventRecord.created_at.asc(),
                ),
                traces=self._group_by_incident(
                    session,
                    AgentTraceRecord,
                    AgentTrace,
                    order_by=AgentTraceRecord.started_at.asc(),
                ),
                runbook_chunks=[
                    self._to_runbook_chunk(item)
                    for item in session.scalars(select(RunbookChunkRecord)).all()
                ],
            )

    def replace_snapshot(self, snapshot: IncidentRepositorySnapshot) -> None:
        with self.session_factory() as session:
            for record_type in (
                AgentTraceRecord,
                TimelineEventRecord,
                PostmortemRecord,
                RecoveryCheckRecord,
                MitigationExecutionRecord,
                ApprovalDecisionRecord,
                MitigationRecommendationRecord,
                HypothesisRecord,
                EvidenceRecord,
                IncidentRecord,
                AlertRecord,
                RunbookChunkRecord,
            ):
                session.execute(delete(record_type))

            session.add_all(self._alert_record(item) for item in snapshot.alerts.values())
            session.add_all(self._incident_record(item) for item in snapshot.incidents.values())
            session.add_all(
                self._evidence_record(item)
                for items in snapshot.evidence.values()
                for item in items
            )
            session.add_all(
                self._hypothesis_record(item)
                for items in snapshot.hypotheses.values()
                for item in items
            )
            session.add_all(
                self._recommendation_record(item)
                for items in snapshot.recommendations.values()
                for item in items
            )
            session.add_all(
                self._approval_record(item)
                for items in snapshot.approvals.values()
                for item in items
            )
            session.add_all(
                self._execution_record(item)
                for items in snapshot.executions.values()
                for item in items
            )
            session.add_all(
                self._recovery_check_record(item)
                for items in snapshot.recovery_checks.values()
                for item in items
            )
            session.add_all(
                self._postmortem_record(item)
                for item in snapshot.postmortems.values()
            )
            session.add_all(
                self._timeline_record(item)
                for items in snapshot.timeline.values()
                for item in items
            )
            session.add_all(
                self._trace_record(item)
                for items in snapshot.traces.values()
                for item in items
            )
            session.add_all(self._runbook_chunk_record(item) for item in snapshot.runbook_chunks)
            session.commit()

    def _group_by_incident(
        self,
        session: Session,
        record_type,
        model_type: type[ModelT],
        order_by,
    ) -> dict[str, list[ModelT]]:
        grouped: dict[str, list[ModelT]] = {}
        records = session.scalars(select(record_type).order_by(order_by)).all()
        for record in records:
            grouped.setdefault(record.incident_id, []).append(
                self._record_to_model(record, model_type)
            )
        return grouped

    def _record_to_model(self, record, model_type: type[ModelT]) -> ModelT:
        if model_type is TimelineEvent:
            return self._to_timeline_event(record)  # type: ignore[return-value]
        return model_type.model_validate(self._record_payload(record))

    def _record_payload(self, record) -> dict:
        return {
            column.name: getattr(record, column.name)
            for column in record.__table__.columns
            if column.name != "event_metadata"
        }

    def _alert_record(self, item: Alert) -> AlertRecord:
        return AlertRecord(**item.model_dump(mode="python"))

    def _incident_record(self, item: Incident) -> IncidentRecord:
        payload = item.model_dump(mode="python")
        payload["status"] = str(item.status)
        return IncidentRecord(**payload)

    def _evidence_record(self, item: Evidence) -> EvidenceRecord:
        payload = item.model_dump(mode="python")
        payload["source_type"] = str(item.source_type)
        return EvidenceRecord(**payload)

    def _hypothesis_record(self, item: Hypothesis) -> HypothesisRecord:
        return HypothesisRecord(**item.model_dump(mode="python"))

    def _recommendation_record(
        self,
        item: MitigationRecommendation,
    ) -> MitigationRecommendationRecord:
        payload = item.model_dump(mode="python")
        payload["action_type"] = str(item.action_type)
        return MitigationRecommendationRecord(**payload)

    def _approval_record(self, item: ApprovalDecision) -> ApprovalDecisionRecord:
        payload = item.model_dump(mode="python")
        payload["decision"] = str(item.decision)
        return ApprovalDecisionRecord(**payload)

    def _execution_record(self, item: MitigationExecution) -> MitigationExecutionRecord:
        payload = item.model_dump(mode="python")
        payload["action_type"] = str(item.action_type)
        payload["status"] = str(item.status)
        return MitigationExecutionRecord(**payload)

    def _recovery_check_record(self, item: RecoveryCheck) -> RecoveryCheckRecord:
        payload = item.model_dump(mode="python")
        payload["status"] = str(item.status)
        return RecoveryCheckRecord(**payload)

    def _postmortem_record(self, item: Postmortem) -> PostmortemRecord:
        return PostmortemRecord(**item.model_dump(mode="python"))

    def _timeline_record(self, item: TimelineEvent) -> TimelineEventRecord:
        payload = item.model_dump(mode="python")
        payload["event_metadata"] = payload.pop("metadata")
        return TimelineEventRecord(**payload)

    def _trace_record(self, item: AgentTrace) -> AgentTraceRecord:
        return AgentTraceRecord(**item.model_dump(mode="python"))

    def _runbook_chunk_record(self, item: RunbookChunk) -> RunbookChunkRecord:
        return RunbookChunkRecord(**item.model_dump(mode="python"))

    def _to_alert(self, item: AlertRecord) -> Alert:
        return Alert.model_validate(self._record_payload(item))

    def _to_incident(self, item: IncidentRecord) -> Incident:
        return Incident.model_validate(self._record_payload(item))

    def _to_postmortem(self, item: PostmortemRecord) -> Postmortem:
        return Postmortem.model_validate(self._record_payload(item))

    def _to_runbook_chunk(self, item: RunbookChunkRecord) -> RunbookChunk:
        return RunbookChunk.model_validate(self._record_payload(item))

    def _to_timeline_event(self, item: TimelineEventRecord) -> TimelineEvent:
        payload = self._record_payload(item)
        payload["metadata"] = item.event_metadata
        return TimelineEvent.model_validate(payload)
