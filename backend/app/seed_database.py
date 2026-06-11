from __future__ import annotations

from alembic import command
from alembic.config import Config

from backend.app.config import PROJECT_ROOT, load_settings
from backend.app.data_loader import load_demo_data
from backend.app.database import build_engine, build_session_factory
from backend.app.repository import DatabaseIncidentRepository
from backend.app.store import IncidentStore


def run_migrations(database_url: str) -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")


def seed_database() -> IncidentStore:
    settings = load_settings()
    run_migrations(settings.database_url)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    repository = DatabaseIncidentRepository(session_factory)
    return IncidentStore(demo_data=load_demo_data(), repository=repository)


def main() -> None:
    store = seed_database()
    print(
        "Incident database ready with "
        f"{len(store.alerts)} alerts, "
        f"{len(store.incidents)} incidents, "
        f"{sum(len(items) for items in store.evidence.values())} evidence items, and "
        f"{len(store.demo_data.runbook_chunks)} runbook chunks."
    )


if __name__ == "__main__":
    main()
