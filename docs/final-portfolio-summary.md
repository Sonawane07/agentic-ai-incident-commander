# Final Portfolio Summary

## Project

Agentic AI Incident Commander is a deployment-ready incident response platform for an e-commerce checkout API outage. It investigates production incidents by correlating alerts, logs, metrics, deployments, GitHub commit risk notes, and runbooks before recommending a human-approved mitigation and generating a postmortem.

## Problem Statement

During incidents, engineers lose time switching across observability tools, commit history, deployment records, runbooks, and communication threads. The project solves that correlation problem by turning the investigation into a stateful agent workflow with evidence-backed decisions.

## Why It Is Agentic

- Uses real LangGraph state graph orchestration.
- Runs 9 specialist investigation agents.
- Uses tool-like data sources: alert fixtures, metrics, logs, deployments, GitHub commits, runbooks, database persistence, and LLM providers.
- Maintains shared incident state across graph nodes.
- Performs retrieval, ranking, hypothesis generation, mitigation planning, and human approval gating.
- Produces an automated postmortem from the actual evidence and timeline.

## Final Stack

- Frontend: React, Vite, React Router, TanStack Query
- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic, Uvicorn
- Agent orchestration: LangGraph
- RAG: PostgreSQL/pgvector-ready schema, hybrid keyword/vector retrieval, deterministic embeddings, optional SentenceTransformers
- LLM: deterministic local provider, optional Ollama
- Persistence: PostgreSQL/pgvector through Docker Compose, SQLite fallback for local tests
- Observability: request IDs, structured JSON logs, Prometheus metrics, Grafana dashboard
- Deployment: Docker Compose
- CI: GitHub Actions for backend tests, evals, frontend build, Compose validation, and Docker image builds

## Demo Scenario

The seeded incident is a checkout API latency spike caused by likely database connection pool saturation after a payment retry deployment. The system gathers evidence from:

- p95 latency and DB pool metrics
- checkout and payment logs
- recent checkout deployment
- GitHub commit risk notes
- runbook RAG chunks

It ranks database pool saturation as the leading hypothesis and recommends an approval-gated rollback to checkout-api `v1.41.9`.

## Validation

- 38 automated tests
- Deterministic eval score: `0.976`
- 9 API-connected dashboard views
- 9 LangGraph agent nodes
- 16 runbook chunks ingested with 384-dimensional deterministic embeddings
- Docker Compose stack validates with `docker compose config`

## Resume Version

Built a deployment-ready agentic incident response platform using LangGraph, FastAPI, React, PostgreSQL/pgvector, Ollama, Docker Compose, Prometheus/Grafana, hybrid runbook RAG, human-in-the-loop approvals, deterministic evals, and automated postmortem generation for e-commerce API incidents.
