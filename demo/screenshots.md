# Screenshot References

The downloaded Stitch design references are available in:

- `stitch/vortex-control-incident-overview.png`
- `stitch/investigation-checkout-api-latency.png`
- `stitch/incident-postmortem-892-checkout-spike.png`
- `stitch/vortex-sentinel-system-health.png`
- `stitch/incident-archive-history.png`
- `stitch/runbook-rag-library.png`
- `stitch/alert-simulation-hub.png`
- `stitch/agent-tracing-debugging.png`
- `stitch/team-access-management.png`

The React implementation in `frontend/src/App.jsx` recreates these screens as API-connected views. For a final GitHub portfolio README, capture fresh screenshots from the running Vite app after starting:

```powershell
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
cd frontend
npm.cmd run dev
```

Open `http://127.0.0.1:5173` and capture:

- Incident Overview
- Investigation Detail
- System Health
- Runbook RAG Library
- Incident Archive
- Postmortem
- Alert Simulation Hub
- Agent Tracing & Debugging
- Team & Access Management
