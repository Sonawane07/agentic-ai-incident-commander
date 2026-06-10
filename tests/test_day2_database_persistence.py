from __future__ import annotations

from backend.app.data_loader import load_demo_data
from backend.app.database import Base, build_engine, build_session_factory
from backend.app.models import ApprovalDecisionValue
from backend.app.repository import DatabaseIncidentRepository
from backend.app.store import IncidentStore


def build_temp_repository(tmp_path) -> DatabaseIncidentRepository:
    engine = build_engine(f"sqlite:///{tmp_path / 'incident_commander_test.db'}")
    Base.metadata.create_all(engine)
    return DatabaseIncidentRepository(build_session_factory(engine))


def test_database_repository_persists_seeded_investigation_state(tmp_path) -> None:
    repository = build_temp_repository(tmp_path)
    demo_data = load_demo_data()

    seeded_store = IncidentStore(demo_data=demo_data, repository=repository)
    loaded_store = IncidentStore(demo_data=demo_data, repository=repository)

    incident = loaded_store.get_incident("inc-892-checkout-spike")
    assert incident.status == "waiting_for_approval"
    assert len(loaded_store.get_evidence(incident.id)) >= 6
    assert len(loaded_store.get_hypotheses(incident.id)) >= 2
    assert len(loaded_store.get_recommendations(incident.id)) >= 3
    assert len(loaded_store.get_traces(incident.id)) == 9
    assert seeded_store.repository is repository


def test_database_repository_persists_human_approval_and_postmortem(tmp_path) -> None:
    repository = build_temp_repository(tmp_path)
    demo_data = load_demo_data()
    store = IncidentStore(demo_data=demo_data, repository=repository)

    store.record_approval(
        incident_id="inc-892-checkout-spike",
        recommendation_id="rec-rollback-v1419",
        decision=ApprovalDecisionValue.APPROVED,
        decided_by="darshan",
        reason="Rollback is evidence-backed.",
    )
    postmortem = store.get_postmortem("inc-892-checkout-spike")

    loaded_store = IncidentStore(demo_data=demo_data, repository=repository)

    assert loaded_store.get_incident("inc-892-checkout-spike").status == "mitigation_recorded"
    assert loaded_store.get_approvals("inc-892-checkout-spike")[0].decided_by == "darshan"
    assert loaded_store.get_postmortem("inc-892-checkout-spike").id == postmortem.id
