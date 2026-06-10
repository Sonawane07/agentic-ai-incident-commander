from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SQLITE_PATH = PROJECT_ROOT / ".local" / "incident_commander.db"


@dataclass(frozen=True)
class AppSettings:
    database_url: str
    storage_backend: str


def load_settings() -> AppSettings:
    return AppSettings(
        database_url=os.getenv(
            "DATABASE_URL",
            f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}",
        ),
        storage_backend=os.getenv("INCIDENT_STORE_BACKEND", "memory").lower(),
    )
