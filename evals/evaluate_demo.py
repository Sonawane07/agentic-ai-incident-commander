from __future__ import annotations

import json
from dataclasses import dataclass, asdict

from backend.app.store import store


INCIDENT_ID = "inc-892-checkout-spike"


@dataclass
class EvalResult:
    name: str
    passed: bool
    score: float
    detail: str


def evaluate_demo_incident() -> list[EvalResult]:
    store.reset()
    evidence = store.get_evidence(INCIDENT_ID)
    hypotheses = store.get_hypotheses(INCIDENT_ID)
    recommendations = store.get_recommendations(INCIDENT_ID)
    traces = store.get_traces(INCIDENT_ID)
    postmortem = store.get_postmortem(INCIDENT_ID)

    source_types = {item.source_type.value for item in evidence}
    postmortem_sections = [
        "## Alert",
        "## Impact",
        "## Likely Root Cause",
        "## Recommended Mitigation",
        "## Human Approval",
        "## Evidence",
        "## Timeline",
        "## Follow-Up Actions",
    ]

    results = [
        EvalResult(
            name="agent_graph_completeness",
            passed=len(traces) == 9,
            score=len(traces) / 9,
            detail=f"Observed {len(traces)} of 9 expected workflow steps.",
        ),
        EvalResult(
            name="evidence_source_coverage",
            passed={"metric", "log", "deployment", "github_commit", "runbook"} <= source_types,
            score=len(source_types & {"metric", "log", "deployment", "github_commit", "runbook"}) / 5,
            detail=f"Covered evidence sources: {sorted(source_types)}.",
        ),
        EvalResult(
            name="root_cause_confidence",
            passed=bool(hypotheses) and hypotheses[0].confidence >= 0.8,
            score=hypotheses[0].confidence if hypotheses else 0,
            detail=hypotheses[0].title if hypotheses else "No hypothesis generated.",
        ),
        EvalResult(
            name="human_approval_gate",
            passed=bool(recommendations) and recommendations[0].requires_approval,
            score=1.0 if recommendations and recommendations[0].requires_approval else 0.0,
            detail=recommendations[0].title if recommendations else "No recommendation generated.",
        ),
        EvalResult(
            name="postmortem_section_coverage",
            passed=all(section in postmortem.markdown for section in postmortem_sections),
            score=sum(section in postmortem.markdown for section in postmortem_sections)
            / len(postmortem_sections),
            detail="Postmortem includes alert, impact, root cause, mitigation, approval, evidence, timeline, and follow-ups.",
        ),
    ]
    return results


def main() -> None:
    results = evaluate_demo_incident()
    payload = {
        "incident_id": INCIDENT_ID,
        "overall_score": round(sum(item.score for item in results) / len(results), 3),
        "passed": all(item.passed for item in results),
        "results": [asdict(item) for item in results],
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
