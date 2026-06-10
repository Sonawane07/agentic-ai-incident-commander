# Frontend

Frontend workspace for the Agentic AI Incident Commander dashboard.

The Stitch exports in `../stitch` are the visual reference for the dashboard screens:

- Incident overview
- Investigation detail
- Incident postmortem
- System health
- Incident archive
- Runbook RAG library

Day 5 converted this visual direction into a runnable frontend wired to the backend APIs.
Day 6 added React Router routes and TanStack Query API hooks.

Implemented views:

- Incident overview
- Investigation detail
- System health
- Incident archive
- Runbook RAG library
- Incident postmortem
- Alert simulation hub
- Agent tracing and debugging
- Team and access management

The frontend calls the FastAPI backend for incidents, evidence, hypotheses, recommendations, approvals, postmortems, runbooks, and system health.

Routes:

- `/incidents`
- `/incidents/:id`
- `/simulation`
- `/traces`
- `/health`
- `/archive`
- `/runbooks`
- `/postmortem`
- `/team`

## Run

Install dependencies:

```powershell
npm.cmd install
```

Start the dev server:

```powershell
npm.cmd run dev
```

The frontend expects the FastAPI backend at `http://127.0.0.1:8000`. Override it with `VITE_API_BASE_URL` if needed.
