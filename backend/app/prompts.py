from __future__ import annotations

from backend.app.models import (
    ApprovalDecision,
    Evidence,
    Hypothesis,
    Incident,
    MitigationRecommendation,
    TimelineEvent,
)


def format_evidence(evidence: list[Evidence], limit: int = 8) -> str:
    if not evidence:
        return "- No evidence available."
    return "\n".join(
        (
            f"- {item.id} [{item.source_type} | relevance {item.relevance_score:.2f}]: "
            f"{item.summary}"
        )
        for item in evidence[:limit]
    )


def build_root_cause_prompt(incident: Incident, evidence: list[Evidence]) -> str:
    return f"""You are an SRE incident commander.

Write a concise root-cause synthesis for this production incident.

Incident:
- ID: {incident.id}
- Title: {incident.title}
- Service: {incident.affected_service}
- Severity: {incident.severity}
- Summary: {incident.summary}

Evidence:
{format_evidence(evidence)}

Requirements:
- Cite the strongest signals.
- Mention uncertainty.
- Do not claim an action was taken unless evidence says so.
"""


def build_mitigation_prompt(
    incident: Incident,
    hypotheses: list[Hypothesis],
    evidence: list[Evidence],
) -> str:
    top_hypothesis = hypotheses[0] if hypotheses else None
    return f"""You are recommending safe incident mitigation.

Incident:
- ID: {incident.id}
- Service: {incident.affected_service}
- Current stage: {incident.current_stage}

Leading hypothesis:
{top_hypothesis.title if top_hypothesis else "No leading hypothesis available."}
{top_hypothesis.description if top_hypothesis else ""}

Evidence:
{format_evidence(evidence)}

Requirements:
- Prefer reversible actions first.
- Identify why human approval is needed.
- Keep the explanation under 80 words.
"""


def build_postmortem_prompt(
    incident: Incident,
    evidence: list[Evidence],
    hypotheses: list[Hypothesis],
    recommendations: list[MitigationRecommendation],
    approvals: list[ApprovalDecision],
    timeline: list[TimelineEvent],
) -> str:
    top_hypothesis = hypotheses[0] if hypotheses else None
    top_recommendation = recommendations[0] if recommendations else None
    approval = approvals[-1] if approvals else None
    timeline_text = "\n".join(
        f"- {item.created_at.isoformat()} {item.stage}: {item.message}"
        for item in timeline[:12]
    )
    return f"""You are drafting an incident postmortem summary.

Incident:
- ID: {incident.id}
- Title: {incident.title}
- Service: {incident.affected_service}
- Severity: {incident.severity}
- Summary: {incident.summary}

Likely root cause:
{top_hypothesis.title if top_hypothesis else "Unknown"}
{top_hypothesis.description if top_hypothesis else ""}

Recommended mitigation:
{top_recommendation.title if top_recommendation else "None"}
{top_recommendation.expected_impact if top_recommendation else ""}

Approval:
{approval.decision + " by " + approval.decided_by if approval else "No approval recorded yet."}

Evidence:
{format_evidence(evidence)}

Timeline:
{timeline_text or "- No timeline available."}

Write a concise executive summary for the postmortem. Do not add Markdown headings.
"""
