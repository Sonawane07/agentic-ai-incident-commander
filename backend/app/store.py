from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.app.config import load_settings
from backend.app.data_loader import load_demo_data
from backend.app.database import SessionLocal
from backend.app.llm import LLMRequest
from backend.app.models import (
    AgentTrace,
    Alert,
    ApprovalDecision,
    ApprovalDecisionValue,
    DemoData,
    Evidence,
    EvidenceSourceType,
    Hypothesis,
    Incident,
    IncidentStatus,
    MitigationActionType,
    MitigationExecution,
    MitigationExecutionStatus,
    MitigationRecommendation,
    Postmortem,
    RecoveryCheck,
    RecoveryStatus,
    TimelineEvent,
)
from backend.app.observability import (
    APPROVAL_DECISIONS_TOTAL,
    POSTMORTEMS_GENERATED_TOTAL,
    logger,
)
from backend.app.prompts import build_postmortem_prompt
from backend.app.repository import DatabaseIncidentRepository, IncidentRepositorySnapshot
from backend.app.workflow import AgenticInvestigationWorkflow


class IncidentNotFoundError(KeyError):
    pass


class RecommendationNotFoundError(KeyError):
    pass


class LifecycleConflictError(ValueError):
    pass


class IncidentStore:
    def __init__(
        self,
        demo_data: DemoData | None = None,
        repository: DatabaseIncidentRepository | None = None,
    ) -> None:
        self.demo_data = demo_data or load_demo_data()
        self.repository = repository or self._repository_from_settings()
        self.workflow = AgenticInvestigationWorkflow()
        self.llm_provider = self.workflow.llm_provider
        if self.repository and self.repository.has_incidents():
            self._load_snapshot(self.repository.load_snapshot())
        else:
            self._initialize_from_demo_data()
            self._persist()

    def _repository_from_settings(self) -> DatabaseIncidentRepository | None:
        settings = load_settings()
        if settings.storage_backend != "database":
            return None
        return DatabaseIncidentRepository(SessionLocal)

    def _initialize_from_demo_data(self) -> None:
        self.alerts = {item.id: item for item in self.demo_data.alerts}
        self.incidents = {item.id: item for item in self.demo_data.incidents}
        self.evidence: dict[str, list[Evidence]] = {}
        self.hypotheses: dict[str, list[Hypothesis]] = {}
        self.recommendations: dict[str, list[MitigationRecommendation]] = {}
        self.approvals: dict[str, list[ApprovalDecision]] = {}
        self.executions: dict[str, list[MitigationExecution]] = {}
        self.recovery_checks: dict[str, list[RecoveryCheck]] = {}
        self.postmortems: dict[str, Postmortem] = {}
        self.timeline: dict[str, list[TimelineEvent]] = {}
        self.traces: dict[str, list[AgentTrace]] = {}
        self._seed_incident_views()

    def _load_snapshot(self, snapshot: IncidentRepositorySnapshot) -> None:
        self.alerts = snapshot.alerts
        self.incidents = snapshot.incidents
        self.evidence = snapshot.evidence
        self.hypotheses = snapshot.hypotheses
        self.recommendations = snapshot.recommendations
        self.approvals = snapshot.approvals
        self.executions = snapshot.executions
        self.recovery_checks = snapshot.recovery_checks
        self.postmortems = snapshot.postmortems
        self.timeline = snapshot.timeline
        self.traces = snapshot.traces
        if snapshot.runbook_chunks:
            self.demo_data = self.demo_data.model_copy(
                update={"runbook_chunks": snapshot.runbook_chunks}
            )

    def _snapshot(self) -> IncidentRepositorySnapshot:
        return IncidentRepositorySnapshot(
            alerts=self.alerts,
            incidents=self.incidents,
            evidence=self.evidence,
            hypotheses=self.hypotheses,
            recommendations=self.recommendations,
            approvals=self.approvals,
            executions=self.executions,
            recovery_checks=self.recovery_checks,
            postmortems=self.postmortems,
            timeline=self.timeline,
            traces=self.traces,
            runbook_chunks=self.demo_data.runbook_chunks,
        )

    def _persist(self) -> None:
        if self.repository:
            self.repository.replace_snapshot(self._snapshot())

    def _seed_incident_views(self) -> None:
        for incident in self.incidents.values():
            self.timeline[incident.id] = self._build_seed_timeline(incident)
            self.run_investigation(incident.id)

    def _build_seed_evidence(self, incident_id: str) -> list[Evidence]:
        return [
            Evidence(
                id="ev-metric-db-pool",
                incident_id=incident_id,
                source_type=EvidenceSourceType.METRIC,
                source_name="mock_prometheus:db_pool_usage_percent",
                timestamp="2026-06-09T14:07:00Z",
                summary="DB connection pool usage reached 98 percent near the alert window.",
                raw_reference="data/fixtures/metrics.json#db_pool_usage_percent",
                confidence=0.95,
                relevance_score=0.96,
            ),
            Evidence(
                id="ev-log-db-pool",
                incident_id=incident_id,
                source_type=EvidenceSourceType.LOG,
                source_name="mock_log_store:checkout-api",
                timestamp="2026-06-09T14:06:11Z",
                summary="Checkout logs show DB_POOL_EXHAUSTED while reserving cart inventory.",
                raw_reference="data/fixtures/logs.json#log-003",
                confidence=0.93,
                relevance_score=0.94,
            ),
            Evidence(
                id="ev-log-payment-timeout",
                incident_id=incident_id,
                source_type=EvidenceSourceType.LOG,
                source_name="mock_log_store:checkout-api",
                timestamp="2026-06-09T14:07:02Z",
                summary="Payment authorization timeout appears in failed checkout requests.",
                raw_reference="data/fixtures/logs.json#log-004",
                confidence=0.88,
                relevance_score=0.86,
            ),
            Evidence(
                id="ev-deploy-v1420",
                incident_id=incident_id,
                source_type=EvidenceSourceType.DEPLOYMENT,
                source_name="mock_deployments:checkout-api",
                timestamp="2026-06-09T14:01:30Z",
                summary="Deployment v1.42.0 completed about five minutes before the alert.",
                raw_reference="data/fixtures/deployments.json#deploy-checkout-v1420",
                confidence=0.91,
                relevance_score=0.9,
            ),
            Evidence(
                id="ev-commit-retry",
                incident_id=incident_id,
                source_type=EvidenceSourceType.GITHUB_COMMIT,
                source_name="mock_github:commit-91af3c2",
                timestamp="2026-06-09T13:42:00Z",
                summary="Commit changed payment retry fanout in the checkout authorization path.",
                raw_reference="data/fixtures/github_commits.json#commit-91af3c2",
                confidence=0.89,
                relevance_score=0.91,
            ),
            Evidence(
                id="ev-runbook-db-pool",
                incident_id=incident_id,
                source_type=EvidenceSourceType.RUNBOOK,
                source_name="runbook:database-connection-pool",
                timestamp="2026-06-01T12:00:00Z",
                summary="Runbook says stable throughput plus rising pool usage often means code is holding connections longer or creating overlapping work.",
                raw_reference="data/runbooks/database-connection-pool.md",
                confidence=0.84,
                relevance_score=0.89,
            ),
        ]

    def _build_seed_hypotheses(self, incident_id: str) -> list[Hypothesis]:
        return [
            Hypothesis(
                id="hyp-db-pool-after-retry",
                incident_id=incident_id,
                title="Database connection pool saturation after payment retry deployment",
                description=(
                    "Checkout latency rose after v1.42.0, DB pool usage hit 98 percent, "
                    "and logs show DB_POOL_EXHAUSTED. The retry fanout change likely "
                    "created overlapping checkout work that held database connections longer."
                ),
                confidence=0.86,
                supporting_evidence_ids=[
                    "ev-metric-db-pool",
                    "ev-log-db-pool",
                    "ev-deploy-v1420",
                    "ev-commit-retry",
                    "ev-runbook-db-pool",
                ],
                contradicting_evidence_ids=[],
                unknowns=["Need confirmation that migration rollback is safe."],
            ),
            Hypothesis(
                id="hyp-provider-timeout",
                incident_id=incident_id,
                title="External payment provider degradation",
                description=(
                    "Payment timeout logs increased, but provider adapter logs say provider "
                    "latency remained normal. This is possible but less supported than a "
                    "checkout-side database pressure issue."
                ),
                confidence=0.42,
                supporting_evidence_ids=["ev-log-payment-timeout"],
                contradicting_evidence_ids=["ev-metric-db-pool"],
                unknowns=["External provider status page has not been queried in the MVP."],
            ),
        ]

    def _build_seed_recommendations(
        self, incident_id: str
    ) -> list[MitigationRecommendation]:
        return [
            MitigationRecommendation(
                id="rec-rollback-v1419",
                incident_id=incident_id,
                hypothesis_id="hyp-db-pool-after-retry",
                action_type=MitigationActionType.ROLLBACK,
                title="Roll back checkout-api to v1.41.9",
                description=(
                    "Rollback is the safest first mitigation because the incident began "
                    "shortly after v1.42.0 and the previous release is marked stable."
                ),
                risk_level="medium",
                confidence=0.84,
                requires_approval=True,
                expected_impact="Reduce retry fanout pressure and lower DB pool usage within 10 minutes.",
            ),
            MitigationRecommendation(
                id="rec-scale-db-pool",
                incident_id=incident_id,
                hypothesis_id="hyp-db-pool-after-retry",
                action_type=MitigationActionType.SCALE_RESOURCE,
                title="Temporarily increase checkout DB pool capacity",
                description=(
                    "May reduce queueing, but should be treated as temporary because it "
                    "does not address the retry fanout change."
                ),
                risk_level="high",
                confidence=0.67,
                requires_approval=True,
                expected_impact="Lower connection wait time if database headroom is available.",
            ),
            MitigationRecommendation(
                id="rec-monitor-only",
                incident_id=incident_id,
                hypothesis_id="hyp-provider-timeout",
                action_type=MitigationActionType.MONITOR_ONLY,
                title="Monitor provider latency before failover",
                description=(
                    "Provider-side evidence is weak, so failover is not the first "
                    "recommended action in this demo."
                ),
                risk_level="low",
                confidence=0.38,
                requires_approval=False,
                expected_impact="Avoid unnecessary provider failover while confirming signals.",
            ),
        ]

    def _build_seed_timeline(self, incident: Incident) -> list[TimelineEvent]:
        return [
            TimelineEvent(
                id="tl-alert-received",
                incident_id=incident.id,
                stage="alert_received",
                actor="mock_datadog",
                message="Critical checkout p95 latency alert received.",
                created_at="2026-06-09T14:07:05Z",
            ),
            TimelineEvent(
                id="tl-incident-created",
                incident_id=incident.id,
                stage="incident_created",
                actor="incident-store",
                message="Incident record created from alert-checkout-892.",
                created_at="2026-06-09T14:07:06Z",
            ),
        ]

    def reset(self) -> None:
        self.demo_data = load_demo_data()
        self._initialize_from_demo_data()
        self._persist()

    def ingest_alert(self, alert: Alert) -> Incident:
        self.alerts[alert.id] = alert
        existing = next(
            (item for item in self.incidents.values() if item.alert_id == alert.id),
            None,
        )
        if existing:
            return existing

        now = datetime.now(UTC)
        incident = Incident(
            id=f"inc-{uuid4().hex[:10]}",
            title=f"{alert.service} {alert.metric_name} breach",
            status=IncidentStatus.NEW,
            severity=alert.severity,
            affected_service=alert.service,
            created_at=now,
            updated_at=now,
            current_stage="awaiting_investigation",
            summary=alert.description,
            alert_id=alert.id,
        )
        self.incidents[incident.id] = incident
        self.evidence[incident.id] = []
        self.hypotheses[incident.id] = []
        self.recommendations[incident.id] = []
        self.approvals[incident.id] = []
        self.executions[incident.id] = []
        self.recovery_checks[incident.id] = []
        self.timeline[incident.id] = [
            TimelineEvent(
                id=f"tl-{uuid4().hex[:10]}",
                incident_id=incident.id,
                stage="alert_received",
                actor=alert.source,
                message=alert.description,
                created_at=now,
            )
        ]
        return self.run_investigation(incident.id)

    def run_investigation(self, incident_id: str) -> Incident:
        incident = self.get_incident(incident_id)
        approvals = self.get_approvals(incident_id)
        if self.get_executions(incident_id) or (
            approvals and approvals[-1].decision == ApprovalDecisionValue.APPROVED
        ):
            raise LifecycleConflictError(
                "The approved response lifecycle has started. Reset the demo before rerunning investigation."
            )
        state = self.workflow.run(incident, self.demo_data)
        self.incidents[incident_id] = state.incident
        self.evidence[incident_id] = state.evidence
        self.hypotheses[incident_id] = state.hypotheses
        self.recommendations[incident_id] = state.recommendations
        self.timeline.setdefault(incident_id, []).extend(state.timeline)
        self.traces[incident_id] = state.traces
        self.postmortems.pop(incident_id, None)
        self._persist()
        return state.incident

    def list_incidents(self) -> list[Incident]:
        return sorted(self.incidents.values(), key=lambda item: item.created_at, reverse=True)

    def get_incident(self, incident_id: str) -> Incident:
        try:
            return self.incidents[incident_id]
        except KeyError as exc:
            raise IncidentNotFoundError(incident_id) from exc

    def get_timeline(self, incident_id: str) -> list[TimelineEvent]:
        self.get_incident(incident_id)
        return self.timeline.get(incident_id, [])

    def get_evidence(self, incident_id: str) -> list[Evidence]:
        self.get_incident(incident_id)
        return self.evidence.get(incident_id, [])

    def get_hypotheses(self, incident_id: str) -> list[Hypothesis]:
        self.get_incident(incident_id)
        return self.hypotheses.get(incident_id, [])

    def get_recommendations(self, incident_id: str) -> list[MitigationRecommendation]:
        self.get_incident(incident_id)
        return self.recommendations.get(incident_id, [])

    def get_traces(self, incident_id: str) -> list[AgentTrace]:
        self.get_incident(incident_id)
        return self.traces.get(incident_id, [])

    def get_executions(self, incident_id: str) -> list[MitigationExecution]:
        self.get_incident(incident_id)
        return self.executions.get(incident_id, [])

    def get_recovery_checks(self, incident_id: str) -> list[RecoveryCheck]:
        self.get_incident(incident_id)
        return self.recovery_checks.get(incident_id, [])

    def list_runbooks(self) -> list[dict]:
        grouped: dict[str, dict] = {}
        for chunk in self.demo_data.runbook_chunks:
            group = grouped.setdefault(
                chunk.runbook_title,
                {
                    "title": chunk.runbook_title,
                    "service": chunk.service,
                    "updated_at": chunk.updated_at,
                    "tags": sorted(set(chunk.tags)),
                    "sections": [],
                },
            )
            group["sections"].append(
                {
                    "id": chunk.id,
                    "title": chunk.section_title,
                    "content": chunk.content,
                    "tags": chunk.tags,
                    "relevance_hint": self._runbook_relevance_hint(chunk.content),
                }
            )
        return sorted(grouped.values(), key=lambda item: item["title"])

    def get_system_health(self) -> dict:
        incident = self.get_incident("inc-892-checkout-spike")
        evidence = self.get_evidence(incident.id)
        recommendations = self.get_recommendations(incident.id)
        executions = self.get_executions(incident.id)
        recovery_checks = self.get_recovery_checks(incident.id)
        latest_execution = executions[-1] if executions else None
        latest_recovery = recovery_checks[-1] if recovery_checks else None
        service_metrics = (
            latest_execution.after_metrics
            if latest_execution
            else self._baseline_metrics()
        )
        if incident.status == IncidentStatus.MITIGATION_RECORDED:
            health_summary = (
                "Mitigation approved and recorded; checkout API remains degraded pending execution."
            )
        elif incident.status == IncidentStatus.RECOVERY_MONITORING:
            health_summary = "Mitigation executed; recovery telemetry is awaiting verification."
        elif incident.status == IncidentStatus.READY_TO_RESOLVE:
            health_summary = "Recovery verified; incident is ready for human resolution."
        elif incident.status == IncidentStatus.CLOSED:
            health_summary = "Checkout API incident is resolved and closed."
        else:
            health_summary = "Checkout API is degraded while approval is pending."
        critical_evidence = [
            item
            for item in evidence
            if item.relevance_score >= 0.9
            and item.source_type in {EvidenceSourceType.METRIC, EvidenceSourceType.LOG}
        ]
        return {
            "status": (
                "healthy"
                if incident.status == IncidentStatus.CLOSED
                else "recovering"
                if latest_recovery and latest_recovery.status == RecoveryStatus.VERIFIED
                else "degraded"
            ),
            "summary": health_summary,
            "active_incidents": len(
                [
                    item
                    for item in self.incidents.values()
                    if item.status != IncidentStatus.CLOSED
                ]
            ),
            "services": [
                {
                    "name": "checkout-api",
                    "status": (
                        "healthy"
                        if incident.status == IncidentStatus.CLOSED
                        else "recovering"
                        if latest_execution
                        else "critical"
                    ),
                    **service_metrics,
                },
                {
                    "name": "payment-gateway-adapter",
                    "status": "watch",
                    "latency_ms": 310,
                    "error_rate_percent": 1.2,
                    "db_pool_usage_percent": None,
                },
                {
                    "name": "inventory-api",
                    "status": "healthy",
                    "latency_ms": 190,
                    "error_rate_percent": 0.6,
                    "db_pool_usage_percent": 42,
                },
            ],
            "agent_confidence": recommendations[0].confidence if recommendations else 0,
            "critical_evidence_count": len(critical_evidence),
        }

    def _runbook_relevance_hint(self, content: str) -> str:
        lowered = content.lower()
        if "db_pool_exhausted" in lowered or "pool" in lowered:
            return "High relevance for DB saturation signals."
        if "rollback" in lowered:
            return "Useful for approval-gated mitigation."
        if "payment" in lowered or "provider" in lowered:
            return "Useful for payment timeout investigation."
        return "General checkout incident context."

    def record_approval(
        self,
        incident_id: str,
        recommendation_id: str,
        decision: ApprovalDecisionValue,
        decided_by: str,
        reason: str,
    ) -> ApprovalDecision:
        incident = self.get_incident(incident_id)
        if self.get_executions(incident_id):
            raise LifecycleConflictError(
                "A mitigation has already been executed. Reset the demo before changing approval."
            )
        recommendations = self.get_recommendations(incident_id)
        if not any(item.id == recommendation_id for item in recommendations):
            raise RecommendationNotFoundError(recommendation_id)

        now = datetime.now(UTC)
        approval = ApprovalDecision(
            id=f"approval-{uuid4().hex[:10]}",
            incident_id=incident_id,
            recommendation_id=recommendation_id,
            decision=decision,
            decided_by=decided_by,
            reason=reason,
            created_at=now,
        )
        self.approvals.setdefault(incident_id, []).append(approval)

        if decision == ApprovalDecisionValue.APPROVED:
            status = IncidentStatus.MITIGATION_RECORDED
            stage = "mitigation_approved"
            message = f"{decided_by} approved {recommendation_id}."
        elif decision == ApprovalDecisionValue.REJECTED:
            status = IncidentStatus.WAITING_FOR_APPROVAL
            stage = "mitigation_rejected"
            message = f"{decided_by} rejected {recommendation_id}."
        else:
            status = IncidentStatus.INVESTIGATING
            stage = "more_investigation_required"
            message = f"{decided_by} requested more investigation for {recommendation_id}."

        self.incidents[incident_id] = incident.model_copy(
            update={"status": status, "current_stage": stage, "updated_at": now}
        )
        self.timeline.setdefault(incident_id, []).append(
            TimelineEvent(
                id=f"tl-{uuid4().hex[:10]}",
                incident_id=incident_id,
                stage=stage,
                actor=decided_by,
                message=message,
                created_at=now,
                metadata={"recommendation_id": recommendation_id, "decision": decision},
            )
        )
        self.postmortems.pop(incident_id, None)
        self._persist()
        APPROVAL_DECISIONS_TOTAL.labels(decision=str(decision)).inc()
        logger.info(
            "approval_recorded",
            extra={
                "incident_id": incident_id,
                "decision": str(decision),
            },
        )
        return approval

    def get_approvals(self, incident_id: str) -> list[ApprovalDecision]:
        self.get_incident(incident_id)
        return self.approvals.get(incident_id, [])

    def execute_approved_mitigation(self, incident_id: str) -> MitigationExecution:
        incident = self.get_incident(incident_id)
        approvals = self.get_approvals(incident_id)
        if not approvals or approvals[-1].decision != ApprovalDecisionValue.APPROVED:
            raise LifecycleConflictError(
                "An approved mitigation is required before execution."
            )
        if incident.status == IncidentStatus.CLOSED:
            raise LifecycleConflictError("Closed incidents cannot execute mitigations.")

        existing = self.get_executions(incident_id)
        if existing:
            return existing[-1]

        approval = approvals[-1]
        recommendation = next(
            (
                item
                for item in self.get_recommendations(incident_id)
                if item.id == approval.recommendation_id
            ),
            None,
        )
        if recommendation is None:
            raise RecommendationNotFoundError(approval.recommendation_id)

        started_at = datetime.now(UTC)
        before_metrics = self._baseline_metrics()
        after_metrics = self._simulated_after_metrics(recommendation.action_type)
        steps = self._execution_steps(recommendation)
        execution = MitigationExecution(
            id=f"exec-{uuid4().hex[:10]}",
            incident_id=incident_id,
            recommendation_id=recommendation.id,
            action_type=recommendation.action_type,
            status=MitigationExecutionStatus.COMPLETED,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            summary=(
                f"Simulated execution completed for '{recommendation.title}'. "
                "No real repository, deployment, or infrastructure was changed."
            ),
            steps=steps,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
        )
        self.executions.setdefault(incident_id, []).append(execution)
        now = datetime.now(UTC)
        self.incidents[incident_id] = incident.model_copy(
            update={
                "status": IncidentStatus.RECOVERY_MONITORING,
                "current_stage": "mitigation_executed",
                "updated_at": now,
            }
        )
        self.timeline.setdefault(incident_id, []).extend(
            [
                TimelineEvent(
                    id=f"tl-{uuid4().hex[:10]}",
                    incident_id=incident_id,
                    stage="mitigation_execution_started",
                    actor="mitigation-executor",
                    message=f"Started simulated execution of {recommendation.title}.",
                    created_at=started_at,
                    metadata={"execution_id": execution.id},
                ),
                TimelineEvent(
                    id=f"tl-{uuid4().hex[:10]}",
                    incident_id=incident_id,
                    stage="mitigation_execution_completed",
                    actor="mitigation-executor",
                    message=execution.summary,
                    created_at=now,
                    metadata={"execution_id": execution.id},
                ),
            ]
        )
        self.postmortems.pop(incident_id, None)
        self._persist()
        return execution

    def monitor_recovery(self, incident_id: str) -> RecoveryCheck:
        incident = self.get_incident(incident_id)
        executions = self.get_executions(incident_id)
        if not executions:
            raise LifecycleConflictError(
                "Execute the approved mitigation before monitoring recovery."
            )
        existing = self.get_recovery_checks(incident_id)
        if existing:
            return existing[-1]

        execution = executions[-1]
        thresholds = {
            "latency_ms": 800.0,
            "error_rate_percent": 3.0,
            "db_pool_usage_percent": 80.0,
        }
        measured = execution.after_metrics
        recovered = all(measured[key] <= value for key, value in thresholds.items())
        status = RecoveryStatus.VERIFIED if recovered else RecoveryStatus.NOT_RECOVERED
        observations = [
            f"Checkout latency changed from {execution.before_metrics['latency_ms']:.0f}ms to {measured['latency_ms']:.0f}ms.",
            f"Error rate changed from {execution.before_metrics['error_rate_percent']:.1f}% to {measured['error_rate_percent']:.1f}%.",
            f"DB pool usage changed from {execution.before_metrics['db_pool_usage_percent']:.0f}% to {measured['db_pool_usage_percent']:.0f}%.",
            (
                "All monitored signals are below recovery thresholds."
                if recovered
                else "One or more monitored signals remain above recovery thresholds."
            ),
        ]
        check = RecoveryCheck(
            id=f"recovery-{uuid4().hex[:10]}",
            incident_id=incident_id,
            execution_id=execution.id,
            status=status,
            checked_at=datetime.now(UTC),
            observations=observations,
            thresholds=thresholds,
            measured_metrics=measured,
        )
        self.recovery_checks.setdefault(incident_id, []).append(check)
        next_status = (
            IncidentStatus.READY_TO_RESOLVE
            if recovered
            else IncidentStatus.RECOVERY_MONITORING
        )
        next_stage = "recovery_verified" if recovered else "recovery_not_verified"
        self.incidents[incident_id] = incident.model_copy(
            update={
                "status": next_status,
                "current_stage": next_stage,
                "updated_at": check.checked_at,
            }
        )
        self.timeline.setdefault(incident_id, []).append(
            TimelineEvent(
                id=f"tl-{uuid4().hex[:10]}",
                incident_id=incident_id,
                stage=next_stage,
                actor="recovery-agent",
                message=observations[-1],
                created_at=check.checked_at,
                metadata={"recovery_check_id": check.id, "status": str(status)},
            )
        )
        self.postmortems.pop(incident_id, None)
        self._persist()
        return check

    def resolve_incident(self, incident_id: str, resolved_by: str) -> Incident:
        incident = self.get_incident(incident_id)
        checks = self.get_recovery_checks(incident_id)
        if not checks or checks[-1].status != RecoveryStatus.VERIFIED:
            raise LifecycleConflictError(
                "Recovery must be verified before the incident can be resolved."
            )
        now = datetime.now(UTC)
        resolved = incident.model_copy(
            update={
                "status": IncidentStatus.CLOSED,
                "current_stage": "incident_resolved",
                "updated_at": now,
            }
        )
        self.incidents[incident_id] = resolved
        self.timeline.setdefault(incident_id, []).append(
            TimelineEvent(
                id=f"tl-{uuid4().hex[:10]}",
                incident_id=incident_id,
                stage="incident_resolved",
                actor=resolved_by,
                message="Recovery verified and incident marked resolved.",
                created_at=now,
            )
        )
        self.postmortems.pop(incident_id, None)
        self._persist()
        return resolved

    def _baseline_metrics(self) -> dict[str, float]:
        return {
            "latency_ms": 2400.0,
            "error_rate_percent": 14.6,
            "db_pool_usage_percent": 98.0,
        }

    def _simulated_after_metrics(
        self,
        action_type: MitigationActionType,
    ) -> dict[str, float]:
        if action_type == MitigationActionType.ROLLBACK:
            return {
                "latency_ms": 610.0,
                "error_rate_percent": 1.2,
                "db_pool_usage_percent": 57.0,
            }
        if action_type == MitigationActionType.SCALE_RESOURCE:
            return {
                "latency_ms": 740.0,
                "error_rate_percent": 2.1,
                "db_pool_usage_percent": 63.0,
            }
        if action_type == MitigationActionType.MONITOR_ONLY:
            return self._baseline_metrics()
        return {
            "latency_ms": 780.0,
            "error_rate_percent": 2.5,
            "db_pool_usage_percent": 70.0,
        }

    def _execution_steps(
        self,
        recommendation: MitigationRecommendation,
    ) -> list[dict[str, str]]:
        action_step = {
            MitigationActionType.ROLLBACK: "Simulated rollback to checkout-api v1.41.9.",
            MitigationActionType.SCALE_RESOURCE: "Simulated checkout DB pool capacity increase.",
            MitigationActionType.MONITOR_ONLY: "Recorded monitor-only action without infrastructure change.",
        }.get(
            recommendation.action_type,
            f"Simulated {recommendation.action_type} action.",
        )
        return [
            {"name": "Validate approval", "status": "completed"},
            {"name": "Capture baseline telemetry", "status": "completed"},
            {"name": action_step, "status": "completed"},
            {"name": "Publish post-change telemetry", "status": "completed"},
        ]

    def get_postmortem(self, incident_id: str) -> Postmortem:
        self.get_incident(incident_id)
        if incident_id not in self.postmortems:
            self.postmortems[incident_id] = self._build_postmortem(incident_id)
            POSTMORTEMS_GENERATED_TOTAL.inc()
            logger.info("postmortem_generated", extra={"incident_id": incident_id})
            self._persist()
        return self.postmortems[incident_id]

    def _build_postmortem(self, incident_id: str) -> Postmortem:
        incident = self.get_incident(incident_id)
        hypotheses = self.get_hypotheses(incident_id)
        recommendations = self.get_recommendations(incident_id)
        evidence = self.get_evidence(incident_id)
        approvals = self.get_approvals(incident_id)
        executions = self.get_executions(incident_id)
        recovery_checks = self.get_recovery_checks(incident_id)
        timeline = self.get_timeline(incident_id)

        top_hypothesis = hypotheses[0] if hypotheses else None
        latest_approval = approvals[-1] if approvals else None
        selected_recommendation = next(
            (
                item
                for item in recommendations
                if latest_approval and item.id == latest_approval.recommendation_id
            ),
            recommendations[0] if recommendations else None,
        )
        alert = self.alerts.get(incident.alert_id)
        approval_summary = (
            (
                f"{latest_approval.decision} by {latest_approval.decided_by} for "
                f"{selected_recommendation.title if selected_recommendation else latest_approval.recommendation_id}: "
                f"{latest_approval.reason}"
            )
            if latest_approval
            else "No human approval decision has been recorded yet. Workflow remains approval-gated."
        )
        root_cause_summary = (
            top_hypothesis.title
            if top_hypothesis
            else "Insufficient evidence for a confident root-cause hypothesis"
        )
        impact_summary = (
            "Checkout latency and payment failures increased in production."
            if incident.affected_service == "checkout-api"
            else f"{incident.affected_service} breached alert threshold in production."
        )
        mitigation_summary = (
            f"{selected_recommendation.title}: {selected_recommendation.expected_impact}"
            if selected_recommendation
            else "No mitigation recommendation is available yet."
        )
        evidence_lines = "\n".join(
            f"- {item.source_type}: {item.summary} (relevance {item.relevance_score:.2f})"
            for item in evidence[:8]
        )
        timeline_lines = "\n".join(
            f"- {item.created_at.isoformat()} - {item.stage} - {item.message}"
            for item in timeline
        )
        follow_up_actions = [
            "Add a regression test for payment retry fanout under DB pool pressure.",
            "Add alert correlation between DB pool usage and checkout retries.",
            "Review rollback readiness for checkout-api releases.",
            "Add a post-approval verification check for latency and DB pool recovery.",
        ]
        postmortem_response = self.llm_provider.generate(
            LLMRequest(
                task="postmortem",
                prompt=build_postmortem_prompt(
                    incident=incident,
                    evidence=evidence,
                    hypotheses=hypotheses,
                    recommendations=recommendations,
                    approvals=approvals,
                    timeline=timeline,
                ),
            )
        )
        follow_up_lines = "\n".join(f"- {item}" for item in follow_up_actions)
        latest_execution = executions[-1] if executions else None
        latest_recovery = recovery_checks[-1] if recovery_checks else None
        execution_summary = (
            (
                f"{latest_execution.summary}\n\n"
                f"- Before: latency {latest_execution.before_metrics['latency_ms']:.0f}ms, "
                f"errors {latest_execution.before_metrics['error_rate_percent']:.1f}%, "
                f"DB pool {latest_execution.before_metrics['db_pool_usage_percent']:.0f}%\n"
                f"- After: latency {latest_execution.after_metrics['latency_ms']:.0f}ms, "
                f"errors {latest_execution.after_metrics['error_rate_percent']:.1f}%, "
                f"DB pool {latest_execution.after_metrics['db_pool_usage_percent']:.0f}%"
            )
            if latest_execution
            else "Mitigation has been approved but not executed."
        )
        recovery_summary = (
            "\n".join(f"- {item}" for item in latest_recovery.observations)
            if latest_recovery
            else "Recovery monitoring has not been completed."
        )
        report_status = "final" if incident.status == IncidentStatus.CLOSED else "draft"
        markdown = f"""# Incident Postmortem: {incident.title}

**Report status: {report_status.upper()}**

## Summary

{incident.summary}

{postmortem_response.text}

## Alert

- Alert ID: {incident.alert_id}
- Source: {alert.source if alert else "unknown"}
- Service: {incident.affected_service}
- Severity: {incident.severity}
- Metric: {alert.metric_name if alert else "unknown"}
- Threshold: {alert.threshold if alert else "unknown"}
- Observed value: {alert.metric_value if alert else "unknown"}

## Impact

{impact_summary}

## Likely Root Cause

{top_hypothesis.description if top_hypothesis else "The workflow did not collect enough evidence to form a strong root-cause hypothesis."}

## Recommended Mitigation

{mitigation_summary}

## Human Approval

{approval_summary}

## Mitigation Execution

{execution_summary}

## Recovery Verification

{recovery_summary}

## Resolution

{"Incident resolved after recovery verification." if incident.status == IncidentStatus.CLOSED else "Incident remains open. This report is a draft until recovery is verified and a human resolves the incident."}

## Evidence

{evidence_lines or "- No evidence captured."}

## Timeline

{timeline_lines or "- No timeline events captured."}

## Follow-Up Actions

{follow_up_lines}
"""
        return Postmortem(
            id=f"pm-{incident_id}",
            incident_id=incident_id,
            markdown=markdown,
            generated_at=datetime.now(UTC),
            root_cause_summary=root_cause_summary,
            impact_summary=impact_summary,
            follow_up_actions=follow_up_actions,
            status=report_status,
            finalized_at=datetime.now(UTC) if report_status == "final" else None,
        )


store = IncidentStore()
