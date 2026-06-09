# Free Deployment-Ready Tech Stack

This project should avoid paid AWS services while still looking deployment-ready and technically credible.

## Recommended Stack

### Frontend

- React
- Vite
- TypeScript
- React Router
- TanStack Query
- Recharts
- Stitch-derived custom CSS

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- Uvicorn

### Agentic AI

- LangGraph
- Stateful graph workflow
- LangGraph checkpointing
- Human-in-the-loop approval nodes
- Agent trace persistence
- Deterministic fallback mode for tests and demos

### LLM

Primary free/local option:

- Ollama

Recommended local models:

- `llama3.1`
- `mistral`
- `qwen2.5`
- `gemma2`

Optional free hosted fallback:

- Groq free tier
- Google Gemini free tier
- OpenRouter free tier where available

### RAG

- Local Markdown runbooks
- SentenceTransformers embeddings
- PostgreSQL + pgvector
- Hybrid keyword plus vector retrieval
- Citation-backed evidence summaries

### Database And Cache

- PostgreSQL
- pgvector
- Redis

### Observability

- Prometheus
- Grafana
- Structured logging
- Request IDs
- Workflow step metrics

### Deployment

- Docker
- Docker Compose
- `.env.example`
- Health checks

### CI/CD

- GitHub Actions
- Backend tests with pytest
- Deterministic eval checks
- Frontend build
- Docker build validation

## What Not To Use Yet

- AWS Bedrock: avoided because the user does not want cloud spend.
- Databricks: not needed for this incident response project unless a real log analytics pipeline is added.
- Kubernetes: useful later, but Docker Compose is enough for a strong portfolio demo.
- Paid vector databases: PostgreSQL + pgvector is enough and free.

## LinkedIn Skills

Top five skills to add:

1. Agentic AI
2. LangGraph
3. FastAPI
4. React.js
5. PostgreSQL

Alternative if LinkedIn does not show Agentic AI:

- Artificial Intelligence (AI)

## Resume Stack Line

LangGraph, FastAPI, React, PostgreSQL/pgvector, Redis, Ollama, Docker Compose, Prometheus/Grafana, GitHub Actions, pytest, SentenceTransformers.

## Resume Bullet

Built a deployment-ready agentic incident response platform using LangGraph, FastAPI, React, PostgreSQL/pgvector, Ollama, Docker Compose, Prometheus/Grafana, runbook RAG, human-in-the-loop approvals, deterministic evals, and automated postmortem generation for e-commerce API incidents.
