from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from backend.app.models import (
    AgentTrace,
    DemoData,
    Evidence,
    EvidenceSourceType,
    Hypothesis,
    Incident,
    IncidentStatus,
    MitigationActionType,
    MitigationRecommendation,
    TimelineEvent,
)
from backend.app.evidence_ranker import EvidenceRanker
from backend.app.retrieval import RunbookRetriever


@dataclass
class InvestigationState:
    incident: Incident
    demo_data: DemoData
    evidence: list[Evidence] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    recommendations: list[MitigationRecommendation] = field(default_factory=list)
    timeline: list[TimelineEvent] = field(default_factory=list)
    traces: list[AgentTrace] = field(default_factory=list)


class AgenticInvestigationWorkflow:
    """Deterministic LangGraph-style workflow for the local MVP."""

    def __init__(self) -> None:
        self.runbook_retriever = RunbookRetriever()
        self.evidence_ranker = EvidenceRanker()

    def run(self, incident: Incident, demo_data: DemoData) -> InvestigationState:
        state = InvestigationState(incident=incident, demo_data=demo_data)
        for agent in (
            self.alert_intake_agent,
            self.metrics_agent,
            self.logs_agent,
            self.github_deploy_agent,
            self.runbook_rag_agent,
            self.evidence_ranking_agent,
            self.root_cause_agent,
            self.mitigation_agent,
            self.approval_agent,
        ):
            self._run_agent(state, agent)
        return state

    def _run_agent(self, state: InvestigationState, agent) -> None:
        started_at = datetime.now(UTC)
        input_summary = self._input_summary(state)
        output_summary = agent(state)
        completed_at = datetime.now(UTC)
        state.traces.append(
            AgentTrace(
                id=f"trace-{uuid4().hex[:10]}",
                incident_id=state.incident.id,
                agent_name=agent.__name__.replace("_", " ").title(),
                input_summary=input_summary,
                output_summary=output_summary,
                started_at=started_at,
                completed_at=completed_at,
            )
        )

    def _input_summary(self, state: InvestigationState) -> str:
        return (
            f"{state.incident.affected_service} incident with "
            f"{len(state.evidence)} evidence items, "
            f"{len(state.hypotheses)} hypotheses, and "
            f"{len(state.recommendations)} recommendations."
        )

    def _timeline(
        self,
        state: InvestigationState,
        stage: str,
        actor: str,
        message: str,
        metadata: dict | None = None,
    ) -> None:
        state.timeline.append(
            TimelineEvent(
                id=f"tl-{uuid4().hex[:10]}",
                incident_id=state.incident.id,
                stage=stage,
                actor=actor,
                message=message,
                created_at=datetime.now(UTC),
                metadata=metadata or {},
            )
        )

    def alert_intake_agent(self, state: InvestigationState) -> str:
        self._timeline(
            state,
            stage="alert_intake_completed",
            actor="Alert Intake Agent",
            message=(
                "Normalized critical checkout-api alert and selected metrics, logs, "
                "deployments, GitHub commits, and runbooks for investigation."
            ),
        )
        return "Alert normalized and investigation branches selected."

    def metrics_agent(self, state: InvestigationState) -> str:
        relevant_metrics = [
            series
            for series in state.demo_data.metrics
            if series.service == state.incident.affected_service
        ]
        for series in relevant_metrics:
            max_sample = max(series.samples, key=lambda sample: sample.value)
            if series.metric_name in {
                "p95_latency_ms",
                "payment_failure_rate",
                "db_pool_usage_percent",
            }:
                state.evidence.append(
                    Evidence(
                        id=f"ev-metric-{series.metric_name}",
                        incident_id=state.incident.id,
                        source_type=EvidenceSourceType.METRIC,
                        source_name=f"mock_prometheus:{series.metric_name}",
                        timestamp=max_sample.timestamp,
                        summary=(
                            f"{state.incident.affected_service} {series.metric_name} peaked at {max_sample.value:g} "
                            f"{series.unit} during the alert window."
                        ),
                        raw_reference=f"data/fixtures/metrics.json#{series.metric_name}",
                        confidence=0.92,
                        relevance_score=0.9
                        if series.metric_name != "db_pool_usage_percent"
                        else 0.97,
                    )
                )
        self._timeline(
            state,
            stage="metrics_agent_completed",
            actor="Metrics Agent",
            message=f"Collected {len(relevant_metrics)} metric series for checkout-api.",
        )
        return "Metric anomalies collected for latency, payment failures, and DB pool usage."

    def logs_agent(self, state: InvestigationState) -> str:
        relevant_logs = [
            entry
            for entry in state.demo_data.logs
            if entry.service in {state.incident.affected_service, "payment-gateway-adapter"}
        ]
        error_logs = [entry for entry in relevant_logs if entry.level in {"error", "warning"}]
        for entry in error_logs:
            if entry.error_code in {
                "PAYMENT_AUTH_TIMEOUT",
                "DB_POOL_EXHAUSTED",
                "PROVIDER_LATENCY_NORMAL",
            }:
                state.evidence.append(
                    Evidence(
                        id=f"ev-log-{entry.id}",
                        incident_id=state.incident.id,
                        source_type=EvidenceSourceType.LOG,
                        source_name=f"mock_log_store:{entry.service}",
                        timestamp=entry.timestamp,
                        summary=f"{entry.error_code}: {entry.message}",
                        raw_reference=f"data/fixtures/logs.json#{entry.id}",
                        confidence=0.9,
                        relevance_score=0.95
                        if entry.error_code == "DB_POOL_EXHAUSTED"
                        else 0.84,
                    )
                )
        self._timeline(
            state,
            stage="logs_agent_completed",
            actor="Logs Agent",
            message=f"Grouped {len(error_logs)} warning/error log entries near the incident.",
        )
        return "Log signatures collected for DB pool exhaustion and payment timeouts."

    def github_deploy_agent(self, state: InvestigationState) -> str:
        deployments = [
            deployment
            for deployment in state.demo_data.deployments
            if deployment.service == state.incident.affected_service
        ]
        if not deployments:
            self._timeline(
                state,
                stage="github_deploy_agent_completed",
                actor="GitHub/Deploy Agent",
                message=(
                    f"No deployment fixture was available for "
                    f"{state.incident.affected_service}; skipped deploy correlation."
                ),
            )
            return "No matching deployment data found for this service."

        latest_deployment = max(deployments, key=lambda item: item.deployed_at)
        state.evidence.append(
            Evidence(
                id=f"ev-deploy-{latest_deployment.version.replace('.', '')}",
                incident_id=state.incident.id,
                source_type=EvidenceSourceType.DEPLOYMENT,
                source_name=f"mock_deployments:{latest_deployment.service}",
                timestamp=latest_deployment.deployed_at,
                summary=(
                    f"{latest_deployment.service} {latest_deployment.version} deployed "
                    f"shortly before the alert: {latest_deployment.summary}"
                ),
                raw_reference=f"data/fixtures/deployments.json#{latest_deployment.id}",
                confidence=0.91,
                relevance_score=0.9,
            )
        )

        commit_lookup = {commit.id: commit for commit in state.demo_data.github_commits}
        for commit_id in latest_deployment.commit_ids:
            commit = commit_lookup[commit_id]
            state.evidence.append(
                Evidence(
                    id=f"ev-commit-{commit.id}",
                    incident_id=state.incident.id,
                    source_type=EvidenceSourceType.GITHUB_COMMIT,
                    source_name=f"mock_github:{commit.sha[:7]}",
                    timestamp=commit.committed_at,
                    summary=f"{commit.message}. Risk notes: {' '.join(commit.risk_notes)}",
                    raw_reference=f"data/fixtures/github_commits.json#{commit.id}",
                    confidence=0.87,
                    relevance_score=0.91
                    if "retry" in commit.message.lower()
                    else 0.62,
                )
            )
        self._timeline(
            state,
            stage="github_deploy_agent_completed",
            actor="GitHub/Deploy Agent",
            message=(
                f"Linked deployment {latest_deployment.version} and "
                f"{len(latest_deployment.commit_ids)} commits to the incident window."
            ),
        )
        return "Recent deployment and commit risk notes collected."

    def runbook_rag_agent(self, state: InvestigationState) -> str:
        results = self.runbook_retriever.search(
            incident=state.incident,
            chunks=state.demo_data.runbook_chunks,
            evidence_summaries=[item.summary for item in state.evidence],
            top_k=4,
        )
        for result in results:
            chunk = result.chunk
            state.evidence.append(
                Evidence(
                    id=f"ev-runbook-{chunk.id}",
                    incident_id=state.incident.id,
                    source_type=EvidenceSourceType.RUNBOOK,
                    source_name=f"runbook:{chunk.runbook_title}",
                    timestamp=chunk.updated_at,
                    summary=f"{chunk.section_title}: {chunk.content[:180]}",
                    raw_reference=f"data/runbooks/{chunk.runbook_title.lower().replace(' ', '-')}.md#{chunk.section_title}",
                    confidence=0.82,
                    relevance_score=result.score,
                )
            )
        self._timeline(
            state,
            stage="runbook_rag_agent_completed",
            actor="Runbook RAG Agent",
            message=(
                f"Retrieved {len(results)} runbook chunks for checkout latency, "
                "DB pool pressure, payment timeout, and rollback."
            ),
            metadata={
                "retrieved_chunk_ids": [result.chunk.id for result in results],
                "top_score": results[0].score if results else 0,
            },
        )
        return "Relevant runbook chunks retrieved and cited as evidence."

    def evidence_ranking_agent(self, state: InvestigationState) -> str:
        state.evidence = self.evidence_ranker.rank(state.evidence, state.incident)
        self._timeline(
            state,
            stage="evidence_ranking_agent_completed",
            actor="Evidence Ranking Agent",
            message=(
                f"Ranked {len(state.evidence)} evidence items by relevance, "
                "time proximity, service match, severity, and source agreement."
            ),
            metadata={
                "top_evidence_ids": [item.id for item in state.evidence[:5]],
            },
        )
        return "Evidence ranked for root-cause synthesis."

    def root_cause_agent(self, state: InvestigationState) -> str:
        evidence_ids = {item.id for item in state.evidence}
        if not state.evidence:
            state.hypotheses = [
                Hypothesis(
                    id="hyp-insufficient-evidence",
                    incident_id=state.incident.id,
                    title="Insufficient evidence for automated root-cause ranking",
                    description=(
                        "The workflow did not find service-specific metrics, logs, "
                        "deployments, commits, or runbooks for this alert. Manual "
                        "investigation or additional fixtures are required."
                    ),
                    confidence=0.2,
                    supporting_evidence_ids=[],
                    contradicting_evidence_ids=[],
                    unknowns=[
                        "No matching service fixtures were available for this alert."
                    ],
                )
            ]
            self._timeline(
                state,
                stage="root_cause_agent_completed",
                actor="Root Cause Agent",
                message="Created low-confidence hypothesis because evidence was insufficient.",
            )
            return "Insufficient evidence hypothesis generated."

        db_support = [
            item.id
            for item in state.evidence
            if "DB_POOL_EXHAUSTED" in item.summary
            or "db_pool_usage_percent" in item.source_name
            or "pool" in item.summary.lower()
            or "retry" in item.summary.lower()
        ]
        provider_support = [
            item.id
            for item in state.evidence
            if "PAYMENT_AUTH_TIMEOUT" in item.summary
            or "payment" in item.summary.lower()
        ]
        state.hypotheses = [
            Hypothesis(
                id="hyp-db-pool-after-retry",
                incident_id=state.incident.id,
                title="Database connection pool saturation after payment retry deployment",
                description=(
                    "Metrics, logs, deployment timing, commit notes, and runbook guidance "
                    "point to the v1.42.0 retry fanout change increasing overlapping "
                    "checkout work and saturating the database connection pool."
                ),
                confidence=0.88,
                supporting_evidence_ids=db_support[:8],
                contradicting_evidence_ids=[],
                unknowns=["Confirm rollback compatibility for v1.42.0."],
            ),
            Hypothesis(
                id="hyp-provider-timeout",
                incident_id=state.incident.id,
                title="External payment provider degradation",
                description=(
                    "Payment timeouts are present, but provider adapter evidence says "
                    "provider latency is normal, making this a weaker explanation."
                ),
                confidence=0.39,
                supporting_evidence_ids=provider_support[:4],
                contradicting_evidence_ids=[
                    item_id
                    for item_id in evidence_ids
                    if "provider" in item_id or "db" in item_id
                ][:3],
                unknowns=["Provider status page is not connected in the MVP."],
            ),
        ]
        self._timeline(
            state,
            stage="root_cause_agent_completed",
            actor="Root Cause Agent",
            message="Ranked DB pool saturation after retry deployment as the leading hypothesis.",
        )
        return "Root-cause hypotheses ranked with evidence citations."

    def mitigation_agent(self, state: InvestigationState) -> str:
        if state.hypotheses and state.hypotheses[0].id == "hyp-insufficient-evidence":
            state.recommendations = [
                MitigationRecommendation(
                    id="rec-more-investigation",
                    incident_id=state.incident.id,
                    hypothesis_id="hyp-insufficient-evidence",
                    action_type=MitigationActionType.MONITOR_ONLY,
                    title="Request more investigation",
                    description=(
                        "No service-specific fixtures were available, so the safest "
                        "MVP action is to gather more evidence before recommending mitigation."
                    ),
                    risk_level="low",
                    confidence=0.3,
                    requires_approval=False,
                    expected_impact="Avoid unsupported mitigation decisions.",
                )
            ]
            self._timeline(
                state,
                stage="mitigation_agent_completed",
                actor="Mitigation Agent",
                message="Recommended more investigation because evidence was insufficient.",
            )
            return "Low-confidence recommendation generated for insufficient evidence."

        state.recommendations = [
            MitigationRecommendation(
                id="rec-rollback-v1419",
                incident_id=state.incident.id,
                hypothesis_id="hyp-db-pool-after-retry",
                action_type=MitigationActionType.ROLLBACK,
                title="Roll back checkout-api to v1.41.9",
                description=(
                    "Rollback removes the retry fanout change that aligns with the alert window, "
                    "DB pool saturation, and checkout timeout logs."
                ),
                risk_level="medium",
                confidence=0.86,
                requires_approval=True,
                expected_impact="Reduce retry fanout pressure and lower DB pool usage within 10 minutes.",
            ),
            MitigationRecommendation(
                id="rec-scale-db-pool",
                incident_id=state.incident.id,
                hypothesis_id="hyp-db-pool-after-retry",
                action_type=MitigationActionType.SCALE_RESOURCE,
                title="Temporarily increase checkout DB pool capacity",
                description=(
                    "Can relieve queueing but may transfer pressure to the database, so it "
                    "should be treated as temporary."
                ),
                risk_level="high",
                confidence=0.68,
                requires_approval=True,
                expected_impact="Lower connection wait time if database headroom is available.",
            ),
            MitigationRecommendation(
                id="rec-monitor-only",
                incident_id=state.incident.id,
                hypothesis_id="hyp-provider-timeout",
                action_type=MitigationActionType.MONITOR_ONLY,
                title="Monitor provider latency before failover",
                description="Provider degradation is weakly supported, so failover is not recommended first.",
                risk_level="low",
                confidence=0.36,
                requires_approval=False,
                expected_impact="Avoid unnecessary provider failover while collecting more evidence.",
            ),
        ]
        self._timeline(
            state,
            stage="mitigation_agent_completed",
            actor="Mitigation Agent",
            message="Ranked rollback as the strongest approval-gated mitigation.",
        )
        return "Mitigation recommendations generated and ranked."

    def approval_agent(self, state: InvestigationState) -> str:
        recommendation_id = (
            state.recommendations[0].id
            if state.recommendations
            else "rec-more-investigation"
        )
        state.incident = state.incident.model_copy(
            update={
                "status": IncidentStatus.WAITING_FOR_APPROVAL,
                "current_stage": "approval_required",
                "updated_at": datetime.now(UTC),
            }
        )
        self._timeline(
            state,
            stage="approval_required",
            actor="Approval Agent",
            message="Paused workflow until a human approves, rejects, or requests more investigation.",
            metadata={"recommendation_id": recommendation_id},
        )
        return "Workflow paused for human approval."
