from __future__ import annotations

import json
from pathlib import Path

from backend.app.models import (
    Alert,
    DemoData,
    DeploymentRecord,
    GitHubCommit,
    Incident,
    LogEntry,
    MetricSeries,
    RunbookChunk,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
FIXTURES_DIR = DATA_DIR / "fixtures"
RUNBOOKS_DIR = DATA_DIR / "runbooks"


def read_json_fixture(name: str) -> object:
    path = FIXTURES_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def load_runbook_chunks() -> list[RunbookChunk]:
    chunks: list[RunbookChunk] = []
    for path in sorted(RUNBOOKS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("-", " ").title()
        service = "checkout-api"
        tags = [part for part in path.stem.split("-") if part not in {"runbook"}]
        sections = [section.strip() for section in text.split("\n## ") if section.strip()]
        for index, section in enumerate(sections):
            lines = section.splitlines()
            if index == 0 and lines[0].startswith("# "):
                section_title = lines[0].removeprefix("# ").strip()
                content = "\n".join(lines[1:]).strip()
            else:
                section_title = lines[0].strip()
                content = "\n".join(lines[1:]).strip()
            chunks.append(
                RunbookChunk(
                    id=f"rb-{path.stem}-{index + 1}",
                    runbook_title=title,
                    section_title=section_title,
                    content=content,
                    tags=tags,
                    service=service,
                    updated_at="2026-06-01T12:00:00Z",
                )
            )
    return chunks


def load_demo_data() -> DemoData:
    return DemoData(
        alerts=[Alert.model_validate(item) for item in read_json_fixture("alerts.json")],
        incidents=[Incident.model_validate(item) for item in read_json_fixture("incidents.json")],
        metrics=[MetricSeries.model_validate(item) for item in read_json_fixture("metrics.json")],
        logs=[LogEntry.model_validate(item) for item in read_json_fixture("logs.json")],
        deployments=[
            DeploymentRecord.model_validate(item)
            for item in read_json_fixture("deployments.json")
        ],
        github_commits=[
            GitHubCommit.model_validate(item)
            for item in read_json_fixture("github_commits.json")
        ],
        runbook_chunks=load_runbook_chunks(),
    )


def summarize_demo_data(data: DemoData) -> dict[str, int]:
    return {
        "alerts": len(data.alerts),
        "incidents": len(data.incidents),
        "metric_series": len(data.metrics),
        "log_entries": len(data.logs),
        "deployments": len(data.deployments),
        "github_commits": len(data.github_commits),
        "runbook_chunks": len(data.runbook_chunks),
    }


def main() -> None:
    data = load_demo_data()
    summary = summarize_demo_data(data)
    print("Loaded Agentic AI Incident Commander demo data:")
    for key, value in summary.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
