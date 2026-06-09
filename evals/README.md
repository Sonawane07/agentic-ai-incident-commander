# Demo Evaluation Harness

This folder contains deterministic evaluation checks for the local MVP. The goal is not to evaluate an LLM benchmark; it is to verify that the agentic incident workflow produces the expected evidence-backed behavior for the portfolio demo.

## Run

```powershell
python -m evals.evaluate_demo
```

## What It Checks

- The graph runs all 9 expected agent steps.
- The incident uses multiple evidence sources: metrics, logs, deployments, GitHub commits, and runbooks.
- The top root-cause hypothesis reaches at least 80 percent confidence.
- The top mitigation is approval-gated.
- The generated postmortem includes alert, impact, root cause, mitigation, approval, evidence, timeline, and follow-up sections.

These checks are intentionally deterministic so the demo remains stable during interviews.
