import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useDashboardData, useIncidentActions } from "./api";

const navItems = [
  { id: "overview", label: "Active Incidents", icon: "dashboard", path: "/incidents" },
  { id: "simulation", label: "Alert Simulation", icon: "emergency", path: "/simulation" },
  { id: "investigation", label: "Investigation", icon: "travel_explore", path: "/incidents/:id" },
  { id: "tracing", label: "Agent Tracing", icon: "terminal", path: "/traces" },
  { id: "health", label: "System Health", icon: "monitoring", path: "/health" },
  { id: "archive", label: "Archive", icon: "history", path: "/archive" },
  { id: "runbooks", label: "Runbooks", icon: "menu_book", path: "/runbooks" },
  { id: "postmortem", label: "Postmortem", icon: "description", path: "/postmortem" },
  { id: "team", label: "Team Access", icon: "admin_panel_settings", path: "/team" },
];

const evidenceIcons = {
  metric: "monitoring",
  log: "terminal",
  deployment: "rocket_launch",
  github_commit: "commit",
  runbook: "menu_book",
  trace: "route",
  human_decision: "verified_user",
};

function pretty(value = "") {
  return String(value).replaceAll("_", " ");
}

function pct(value = 0) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function timeOnly(value = "") {
  if (!value) return "--:--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function Icon({ name, filled = false }) {
  return (
    <span className={`material-symbols-outlined ${filled ? "filled" : ""}`} aria-hidden="true">
      {name}
    </span>
  );
}

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const incidentId = incidentIdFromPath(location.pathname);
  const dashboard = useDashboardData(incidentId);
  const data = dashboard.data || {};
  const activeIncident = data.activeIncident;
  const actions = useIncidentActions(activeIncident);
  const view = viewFromPath(location.pathname);

  useEffect(() => {
    if (location.pathname === "/") {
      navigate("/incidents", { replace: true });
    }
  }, [location.pathname, navigate]);

  async function rerunInvestigation() {
    if (!activeIncident) return;
    await actions.rerunInvestigation.mutateAsync();
  }

  async function submitDecision(decision, recommendationId) {
    if (!activeIncident || !recommendationId) return;
    await actions.submitDecision.mutateAsync({ decision, recommendationId });
  }

  async function triggerSimulation(scenario) {
    const result = await actions.triggerSimulation.mutateAsync(scenario);
    navigate(`/incidents/${result.incident_id}`);
  }

  const setView = (nextView) => navigate(routeForView(nextView, activeIncident));
  const loading = dashboard.isLoading;
  const error = dashboard.error?.message || "";
  const decisionBusy = busyState(actions);
  const decisionTargetId = actions.submitDecision.variables?.recommendationId || "";

  const context = {
    activeIncident,
    approvals: data.approvals || [],
    decisionBusy,
    decisionTargetId,
    evidence: data.evidence || [],
    hypotheses: data.hypotheses || [],
    incidents: data.incidents || [],
    postmortem: data.postmortem || null,
    recommendations: data.recommendations || [],
    rerunInvestigation,
    runbooks: data.runbooks || [],
    setView,
    submitDecision,
    triggerSimulation,
    systemHealth: data.systemHealth || null,
    timeline: data.timeline || [],
    traces: data.traces || [],
  };

  return (
    <div className="vortex-shell">
      <Sidebar view={view} setView={setView} systemHealth={context.systemHealth} />
      <main className="vortex-main">
        <TopBar
          activeIncident={activeIncident}
          loadDashboard={() => dashboard.refetch()}
          rerunInvestigation={rerunInvestigation}
          decisionBusy={decisionBusy}
        />
        {error ? <div className="alert-banner">API error: {error}</div> : null}
        {loading || !activeIncident ? (
          <div className="loading-board">
            <div className="spinner-ring" />
            <span>Synchronizing Vortex Command with FastAPI...</span>
          </div>
        ) : (
          <ScreenRoutes context={context} />
        )}
      </main>
    </div>
  );
}

function incidentIdFromPath(pathname) {
  const match = pathname.match(/^\/incidents\/([^/]+)/);
  return match?.[1];
}

function viewFromPath(pathname) {
  if (pathname.startsWith("/simulation")) return "simulation";
  if (pathname.startsWith("/incidents/")) return "investigation";
  if (pathname.startsWith("/traces")) return "tracing";
  if (pathname.startsWith("/health")) return "health";
  if (pathname.startsWith("/archive")) return "archive";
  if (pathname.startsWith("/runbooks")) return "runbooks";
  if (pathname.startsWith("/postmortem")) return "postmortem";
  if (pathname.startsWith("/team")) return "team";
  return "overview";
}

function routeForView(view, activeIncident) {
  const incidentPath = `/incidents/${activeIncident?.id || "inc-892-checkout-spike"}`;
  const routes = {
    overview: "/incidents",
    simulation: "/simulation",
    investigation: incidentPath,
    tracing: "/traces",
    health: "/health",
    archive: "/archive",
    runbooks: "/runbooks",
    postmortem: "/postmortem",
    team: "/team",
  };
  return routes[view] || "/incidents";
}

function busyState(actions) {
  if (actions.rerunInvestigation.isPending) return "rerun";
  if (actions.submitDecision.isPending) {
    return actions.submitDecision.variables?.decision || "decision";
  }
  if (actions.triggerSimulation.isPending) {
    return `simulate-${actions.triggerSimulation.variables?.id}`;
  }
  return "";
}

function ScreenRoutes({ context }) {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/incidents" replace />} />
      <Route path="/incidents" element={<OverviewScreen {...context} />} />
      <Route path="/incidents/:id" element={<InvestigationScreen {...context} />} />
      <Route path="/simulation" element={<AlertSimulationScreen {...context} />} />
      <Route path="/traces" element={<AgentTracingScreen {...context} />} />
      <Route path="/health" element={<HealthScreen {...context} />} />
      <Route path="/archive" element={<ArchiveScreen {...context} />} />
      <Route path="/runbooks" element={<RunbookScreen {...context} />} />
      <Route path="/postmortem" element={<PostmortemScreen {...context} />} />
      <Route path="/team" element={<TeamAccessScreen {...context} />} />
      <Route path="*" element={<Navigate to="/incidents" replace />} />
    </Routes>
  );
}

function Sidebar({ view, setView, systemHealth }) {
  return (
    <aside className="vortex-sidebar">
      <div className="brand">
        <div className="brand-orbit">
          <Icon name="cyclone" filled />
        </div>
        <div>
          <h1>Vortex Control</h1>
          <p>Incident Command</p>
        </div>
      </div>

      <nav className="nav-stack" aria-label="Primary">
        {navItems.map((item) => (
          <button
            className={`nav-link ${view === item.id ? "active" : ""}`}
            key={item.id}
            onClick={() => setView(item.id)}
            type="button"
          >
            <Icon name={item.icon} />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <button className="new-incident" type="button">
        <Icon name="add_alert" />
        Create Incident
      </button>

      <div className="system-card">
        <span className="status-light" />
        <div>
          <strong>{systemHealth?.status || "Syncing"}</strong>
          <p>{systemHealth?.summary || "Awaiting telemetry"}</p>
        </div>
      </div>
    </aside>
  );
}

function TopBar({ activeIncident, loadDashboard, rerunInvestigation, decisionBusy }) {
  return (
    <header className="topbar">
      <div className="topbar-title">
        <h2>Vortex Command</h2>
        <nav>
          <a>Dashboard</a>
          <a>Analytics</a>
          <a>Team</a>
        </nav>
      </div>
      <div className="topbar-tools">
        <div className="search-box">
          <Icon name="search" />
          <span>{activeIncident?.affected_service || "Search incidents"}</span>
        </div>
        <button className="icon-button" onClick={loadDashboard} title="Refresh" type="button">
          <Icon name="sync" />
        </button>
        <button
          className="primary-action"
          disabled={decisionBusy === "rerun"}
          onClick={rerunInvestigation}
          type="button"
        >
          <Icon name="play_arrow" filled />
          Re-run Graph
        </button>
        <div className="avatar">DS</div>
      </div>
    </header>
  );
}

function OverviewScreen({
  activeIncident,
  evidence,
  incidents,
  recommendations,
  setView,
  systemHealth,
  timeline,
  traces,
}) {
  const topRecommendation = recommendations[0];
  return (
    <div className="overview-screen">
      <section className="hero-strip">
        <div>
          <p className="caps">Incident Horizon</p>
          <h1>{activeIncident.title}</h1>
          <p>{activeIncident.summary}</p>
        </div>
        <div className="hero-metrics">
          <Metric label="Active Agents" value={traces.length || 9} tone="purple" />
          <Metric label="Confidence" value={pct(systemHealth?.agent_confidence)} tone="green" />
          <Metric label="Evidence" value={evidence.length} tone="cyan" />
        </div>
      </section>

      <div className="overview-grid">
        <section className="glass-panel incident-stack">
          <PanelTitle eyebrow="Active Incident Stack" title="Production Incidents" icon="warning" />
          <IncidentTable
            activeIncident={activeIncident}
            incidents={incidents}
            recommendations={recommendations}
            setView={setView}
          />
        </section>

        <section className="glass-panel topology-panel">
          <PanelTitle eyebrow="Cluster Map" title="Checkout Stress Field" icon="hub" />
          <ClusterMap />
          <div className="confidence-tile">
            <p>Automated remediation success</p>
            <strong>{pct(topRecommendation?.confidence || systemHealth?.agent_confidence)}</strong>
            <button type="button" onClick={() => setView("investigation")}>
              Inspect Mitigation
            </button>
          </div>
        </section>

        <AgentRail evidence={evidence} timeline={timeline} traces={traces} setView={setView} />
      </div>
    </div>
  );
}

function IncidentTable({ activeIncident, incidents, recommendations, setView }) {
  const rows = [
    {
      service: activeIncident.affected_service,
      severity: activeIncident.severity,
      status: activeIncident.status,
      summary: activeIncident.summary,
      confidence: recommendations[0]?.confidence || 0.86,
    },
    {
      service: "catalog-api",
      severity: "high",
      status: "investigating",
      summary: "Cache miss storm increasing product page TTFB.",
      confidence: 0.72,
    },
    {
      service: "auth-gateway",
      severity: "low",
      status: "monitoring",
      summary: "Token refresh failures below automated action threshold.",
      confidence: 0.42,
    },
  ];

  return (
    <div className="incident-table">
      <div className="table-head">
        <span>Service</span>
        <span>Severity</span>
        <span>Status</span>
        <span>Confidence</span>
      </div>
      {rows.map((row, index) => (
        <button
          className={`incident-line ${index === 0 ? "critical" : ""}`}
          key={`${row.service}-${row.status}`}
          onClick={() => setView(index === 0 ? "investigation" : "archive")}
          type="button"
        >
          <span>
            <strong>{row.service}</strong>
            <small>{row.summary}</small>
          </span>
          <Severity value={row.severity} />
          <Status value={row.status} />
          <b>{pct(row.confidence)}</b>
        </button>
      ))}
      <div className="incident-count">{incidents.length} backend incident loaded from FastAPI</div>
    </div>
  );
}

function ClusterMap() {
  const nodes = [
    ["API", "critical"],
    ["DB", "critical"],
    ["PAY", "watch"],
    ["AUTH", "healthy"],
    ["CAT", "watch"],
    ["WEB", "healthy"],
  ];
  return (
    <div className="cluster-map">
      <div className="grid-plane" />
      {nodes.map(([label, tone], index) => (
        <div className={`cluster-node ${tone} node-${index}`} key={label}>
          {label}
        </div>
      ))}
      <div className="connection connection-a" />
      <div className="connection connection-b" />
      <div className="connection connection-c" />
    </div>
  );
}

function AgentRail({ evidence, timeline, traces, setView }) {
  return (
    <aside className="agent-rail">
      <div className="agent-header">
        <div className="stacked-avatars">
          <span>AI</span>
          <span>SE</span>
          <span>DB</span>
        </div>
        <button onClick={() => setView("postmortem")} type="button">
          Export Report
        </button>
      </div>
      <p className="caps purple">Agent Vortex-01</p>
      <div className="agent-feed">
        {timeline.slice(-3).map((event) => (
          <article className="feed-card" key={event.id}>
            <span>{timeOnly(event.timestamp)}</span>
            <strong>{pretty(event.stage)}</strong>
            <p>{event.message}</p>
          </article>
        ))}
        {evidence.slice(0, 3).map((item) => (
          <article className="feed-card code" key={item.id}>
            <span>{pretty(item.source_type)}</span>
            <p>{item.summary}</p>
          </article>
        ))}
      </div>
      <div className="rail-footer">
        <span>{traces.length} graph nodes complete</span>
        <span>Systems nominal</span>
      </div>
    </aside>
  );
}

function InvestigationScreen({
  activeIncident,
  approvals,
  decisionBusy,
  decisionTargetId,
  evidence,
  hypotheses,
  recommendations,
  submitDecision,
  timeline,
  traces,
}) {
  const [isChangingDecision, setIsChangingDecision] = useState(false);
  const topRecommendation = recommendations[0];
  const latestApproval = approvals.at(-1);
  const decisionRecorded = Boolean(latestApproval);
  const approvalLabels = {
    approved: "Mitigation approved",
    rejected: "Mitigation rejected",
    more_investigation_required: "More evidence requested",
  };

  useEffect(() => {
    setIsChangingDecision(false);
  }, [latestApproval?.id]);

  async function handleDecision(decision, recommendationId) {
    await submitDecision(decision, recommendationId);
    setIsChangingDecision(false);
  }

  return (
    <div className="investigation-screen">
      <aside className="activity-sidebar">
        <p className="caps purple">Agent Activity</p>
        <h3>Investigation Unit</h3>
        <div className="activity-steps">
          {traces.map((trace, index) => (
            <article className={index === traces.length - 1 ? "active" : ""} key={trace.id}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <div>
                <strong>{trace.agent_name}</strong>
                <p>{trace.output_summary}</p>
              </div>
            </article>
          ))}
        </div>
        <button className="primary-action full" disabled type="button">
          <Icon name={decisionRecorded ? "verified" : "pending_actions"} />
          {latestApproval?.decision === "approved"
            ? "Mitigation Approved"
            : latestApproval?.decision === "rejected"
              ? "Mitigation Rejected"
              : latestApproval?.decision === "more_investigation_required"
                ? "More Evidence Requested"
                : "Awaiting Human Approval"}
        </button>
      </aside>

      <section className="context-core">
        <div className="incident-heading">
          <div>
            <span>Incident #9421-V</span>
            <h1>Checkout Latency Spike</h1>
            <p>{activeIncident.summary}</p>
          </div>
          <div className="countdown">
            <small>T-minus</small>
            <strong>00:14:22</strong>
          </div>
        </div>

        <section className="glass-panel chart-panel">
          <PanelTitle eyebrow="Latency Distribution" title="P99 Service Latency" icon="bar_chart" />
          <LatencyChart evidence={evidence} />
        </section>

        <section className="glass-panel evidence-timeline">
          <PanelTitle eyebrow="Evidence Timeline" title="Correlated Signals" icon="timeline" />
          {evidence.slice(0, 8).map((item) => (
            <article className="evidence-row" key={item.id}>
              <div className={`source-icon ${item.source_type}`}>
                <Icon name={evidenceIcons[item.source_type] || "dataset"} />
              </div>
              <div>
                <strong>{item.title}</strong>
                <p>{item.summary}</p>
              </div>
              <span>{pct(item.relevance_score)}</span>
            </article>
          ))}
        </section>
      </section>

      <aside className="recommendation-pane">
        <section className="glass-panel hypothesis-panel">
          <p className="caps purple">Hypothesis</p>
          {hypotheses.map((item) => (
            <article key={item.id}>
              <div className="score-dial">{pct(item.confidence)}</div>
              <h2>{item.title}</h2>
              <p>{item.description}</p>
            </article>
          ))}
        </section>

        <section className="glass-panel mitigation-panel">
          <p className="caps">Ranked Mitigation</p>
          {latestApproval ? (
            <div className={`decision-confirmation ${latestApproval.decision}`}>
              <Icon
                name={
                  latestApproval.decision === "approved"
                    ? "check_circle"
                    : latestApproval.decision === "rejected"
                      ? "cancel"
                      : "manage_search"
                }
                filled
              />
              <div>
                <strong>{approvalLabels[latestApproval.decision]}</strong>
                <span>
                  {latestApproval.decided_by} selected this action. The decision is recorded in the
                  incident timeline.
                </span>
              </div>
              <button
                className="change-decision-button"
                disabled={Boolean(decisionBusy)}
                onClick={() => setIsChangingDecision((current) => !current)}
                type="button"
              >
                {isChangingDecision ? "Cancel change" : "Change decision"}
              </button>
            </div>
          ) : null}
          {isChangingDecision ? (
            <p className="decision-edit-note">
              Select a replacement action. The previous decision will remain in the audit timeline.
            </p>
          ) : null}
          {recommendations.map((item, index) => (
            <article
              className={`mitigation-card rank-${index} ${
                latestApproval?.recommendation_id === item.id ? "decision-selected" : ""
              }`}
              key={item.id}
            >
              <div>
                <strong>{item.title}</strong>
                <span>{pct(item.confidence)}</span>
              </div>
              <p>{item.expected_impact}</p>
              <button
                className={
                  latestApproval?.recommendation_id === item.id &&
                  latestApproval.decision === "approved"
                    ? "approved-button"
                    : ""
                }
                disabled={
                  Boolean(decisionBusy) ||
                  (decisionRecorded && !isChangingDecision) ||
                  (isChangingDecision &&
                    latestApproval?.decision === "approved" &&
                    latestApproval?.recommendation_id === item.id)
                }
                onClick={() => handleDecision("approved", item.id)}
                type="button"
              >
                {decisionBusy === "approved" && decisionTargetId === item.id
                  ? "Approving..."
                  : latestApproval?.recommendation_id === item.id &&
                      latestApproval.decision === "approved"
                    ? "Approved"
                    : isChangingDecision
                      ? "Select"
                    : "Approve"}
              </button>
            </article>
          ))}
          <div className="approval-row">
            <button
              disabled={Boolean(decisionBusy) || (decisionRecorded && !isChangingDecision)}
              onClick={() => handleDecision("rejected", topRecommendation?.id)}
              type="button"
            >
              {decisionBusy === "rejected"
                ? "Rejecting..."
                : latestApproval?.decision === "rejected"
                  ? "Rejected"
                  : "Reject"}
            </button>
            <button
              disabled={Boolean(decisionBusy) || (decisionRecorded && !isChangingDecision)}
              onClick={() =>
                handleDecision("more_investigation_required", topRecommendation?.id)
              }
              type="button"
            >
              {decisionBusy === "more_investigation_required"
                ? "Requesting..."
                : latestApproval?.decision === "more_investigation_required"
                  ? "Evidence Requested"
                  : "More Evidence"}
            </button>
          </div>
        </section>
      </aside>
    </div>
  );
}

function LatencyChart({ evidence }) {
  const values = useMemo(() => [26, 38, 44, 67, 82, 96, 91, 74, 58, 42, 34, 31], []);
  const metricEvidence = evidence.find((item) => item.source_type === "metric");
  return (
    <div className="latency-chart">
      <div className="chart-grid">
        {values.map((value, index) => (
          <span key={`${value}-${index}`} style={{ height: `${value}%` }}>
            <i />
          </span>
        ))}
      </div>
      <div className="chart-callout">
        <strong>{metricEvidence?.title || "P99 spike detected"}</strong>
        <p>{metricEvidence?.summary || "Checkout latency exceeded normal service envelope."}</p>
      </div>
    </div>
  );
}

function HealthScreen({ evidence, systemHealth, traces }) {
  return (
    <div className="health-screen">
      <section className="health-header">
        <Metric label="Global Latency" value="482ms" tone="red" />
        <Metric label="Active Incidents" value={systemHealth.active_incidents} tone="purple" />
        <Metric label="Critical Evidence" value={systemHealth.critical_evidence_count} tone="cyan" />
        <Metric label="Agent Steps" value={traces.length} tone="green" />
      </section>

      <div className="health-grid">
        <section className="glass-panel topology-large">
          <PanelTitle eyebrow="Service Topology Map" title="Real-time Request Flow" icon="account_tree" />
          <ClusterMap />
        </section>
        <section className="glass-panel telemetry-feed">
          <PanelTitle eyebrow="Telemetry Feed" title="Live Signals" icon="sensors" />
          {evidence.slice(0, 7).map((item) => (
            <article key={item.id}>
              <span>[{pretty(item.source_type)}]</span>
              <p>{item.summary}</p>
            </article>
          ))}
        </section>
      </div>

      <section className="glass-panel node-inventory">
        <PanelTitle eyebrow="Node Health Inventory" title="Service Runtime" icon="dns" />
        <div className="service-grid">
          {systemHealth.services.map((service) => (
            <article className={service.status} key={service.name}>
              <header>
                <strong>{service.name}</strong>
                <Status value={service.status} />
              </header>
              <dl>
                <div>
                  <dt>Latency</dt>
                  <dd>{service.latency_ms}ms</dd>
                </div>
                <div>
                  <dt>Error Rate</dt>
                  <dd>{service.error_rate_percent}%</dd>
                </div>
                <div>
                  <dt>DB Pool</dt>
                  <dd>{service.db_pool_usage_percent ?? "n/a"}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function ArchiveScreen({ activeIncident, approvals, postmortem, recommendations }) {
  const rows = [
    {
      id: activeIncident.id,
      title: activeIncident.title,
      status: activeIncident.status,
      rootCause: postmortem?.root_cause_summary || "Active investigation in progress",
      mttr: approvals.length ? "4m 12s" : "pending",
    },
    {
      id: "inc-781",
      title: "Catalog cache miss storm",
      status: "closed",
      rootCause: "Redis TTL regression after config push",
      mttr: "6m 44s",
    },
    {
      id: "inc-744",
      title: "Payment provider failover delay",
      status: "closed",
      rootCause: "Provider health probe threshold too slow",
      mttr: "8m 02s",
    },
  ];
  return (
    <div className="archive-screen">
      <section className="archive-hero">
        <div>
          <p className="caps purple">Incident Archive History</p>
          <h1>Resolution Intelligence</h1>
          <p>Historical incidents, mitigation outcomes, and evidence-backed learnings.</p>
        </div>
        <Metric label="Mitigation Success" value={pct(recommendations[0]?.confidence)} tone="green" />
      </section>

      <section className="glass-panel archive-table">
        <div className="archive-filters">
          <button className="active" type="button">All</button>
          <button type="button">Checkout</button>
          <button type="button">Payments</button>
          <button type="button">Database</button>
        </div>
        {rows.map((row) => (
          <article key={row.id}>
            <div>
              <strong>{row.title}</strong>
              <p>{row.rootCause}</p>
            </div>
            <Status value={row.status} />
            <span>{row.mttr}</span>
          </article>
        ))}
      </section>
    </div>
  );
}

function RunbookScreen({ evidence, runbooks, setView }) {
  const active = runbooks[0];
  return (
    <div className="runbook-screen">
      <aside className="runbook-library">
        <div className="runbook-search">
          <Icon name="search" />
          <span>Search RAG Knowledge Base...</span>
        </div>
        <h2>Knowledge Library</h2>
        <p>RAG-indexed procedures</p>
        {runbooks.map((runbook) => (
          <article className={runbook.title === active?.title ? "selected" : ""} key={runbook.title}>
            <Icon name="article" />
            <div>
              <strong>{runbook.title}</strong>
              <p>{runbook.sections.length} indexed sections for {runbook.service}</p>
            </div>
          </article>
        ))}
        <button className="primary-action full" type="button">
          <Icon name="upload_file" />
          Ingest New Runbook
        </button>
      </aside>

      <section className="runbook-core">
        <p className="caps purple">Active Session: Runbook-X82</p>
        <h1>{active?.title || "Checkout API Latency"}</h1>
        <p>
          This runbook is optimized for diagnosing and mitigating high latency in the
          primary checkout transaction flow.
        </p>
        <div className="runbook-sections">
          {active?.sections.map((section) => (
            <article className="glass-panel" key={section.id}>
              <span>{section.relevance_hint}</span>
              <h3>{section.title}</h3>
              <p>{section.content}</p>
            </article>
          ))}
        </div>
      </section>

      <aside className="rag-context">
        <PanelTitle eyebrow="Real-time Agent Activity" title="RAG Context Sources" icon="neurology" />
        {evidence
          .filter((item) => item.source_type === "runbook")
          .map((item) => (
            <article key={item.id}>
              <strong>{item.title}</strong>
              <p>{item.summary}</p>
              <span>{pct(item.relevance_score)}</span>
            </article>
          ))}
        <button onClick={() => setView("investigation")} type="button">
          View Investigation
        </button>
      </aside>
    </div>
  );
}

function PostmortemScreen({ activeIncident, approvals, postmortem, recommendations }) {
  const latestApproval = approvals.at(-1);
  return (
    <div className="postmortem-screen">
      <section className="postmortem-cover">
        <p className="caps purple">Incident Postmortem: #892-Checkout-Spike</p>
        <h1>{activeIncident.title}</h1>
        <p>{postmortem?.impact_summary || activeIncident.summary}</p>
      </section>
      <div className="postmortem-grid">
        <article className="glass-panel report-doc">
          <pre>{postmortem?.markdown || "Postmortem generation pending approval state."}</pre>
        </article>
        <aside className="glass-panel decision-log">
          <PanelTitle eyebrow="Approval Trail" title="Human in the Loop" icon="verified" />
          {approvals.length ? (
            approvals.map((approval) => (
              <article
                className={approval.id === latestApproval?.id ? "current" : "superseded"}
                key={approval.id}
              >
                <div className="decision-log-heading">
                  <strong>{pretty(approval.decision)}</strong>
                  <span>{approval.id === latestApproval?.id ? "Current" : "Superseded"}</span>
                </div>
                <b>
                  {recommendations.find((item) => item.id === approval.recommendation_id)?.title ||
                    approval.recommendation_id}
                </b>
                <p>{approval.reason}</p>
              </article>
            ))
          ) : (
            <p>No approval decision has been recorded yet.</p>
          )}
        </aside>
      </div>
    </div>
  );
}

function AlertSimulationScreen({ decisionBusy, evidence, systemHealth, timeline, traces, triggerSimulation }) {
  const scenarios = [
    {
      id: "mock-checkout-latency",
      title: "Checkout Latency Spike",
      severity: "critical",
      service: "checkout-api",
      metricName: "p95_latency_ms",
      metricValue: 2500,
      threshold: 800,
      icon: "speed",
      tone: "critical",
      description: "Synthetic P99 latency increase to 2500ms on /v1/checkout endpoint.",
    },
    {
      id: "mock-db-exhaustion",
      title: "DB Connection Exhaustion",
      severity: "high",
      service: "checkout-api",
      metricName: "db_pool_usage_percent",
      metricValue: 98,
      threshold: 80,
      icon: "database",
      tone: "warning",
      description: "Simulates exhaustion of the Postgres pool in production-cluster-01.",
    },
    {
      id: "mock-payment-timeout",
      title: "Payment Gateway Timeout",
      severity: "warning",
      service: "payment-gateway-adapter",
      metricName: "payment_failure_rate",
      metricValue: 20,
      threshold: 5,
      icon: "account_balance_wallet",
      tone: "cyan",
      description: "Simulates 504 errors for 20 percent of incoming payment traffic.",
    },
  ];

  const payloadPreview = {
    incident_id: "MOCK-552-VORTEX",
    source: "prometheus-agent-simulation",
    status: "firing",
    severity: "critical",
    labels: {
      alertname: "LatencyHigh",
      service: "checkout-api",
      cluster: "k8s-us-east-1",
    },
    annotations: {
      summary: "High latency on checkout",
      description: "P99 is currently at 2.4s",
    },
  };

  return (
    <div className="simulation-screen">
      <section className="simulation-hero">
        <div>
          <p className="caps purple">Simulation Lab</p>
          <h1>Chaos Engineering Interface</h1>
          <p>Inject controlled synthetic failure modes to validate agent response latency and LangGraph decision pathways.</p>
        </div>
        <Metric label="Simulator" value="Online" tone="purple" />
      </section>

      <section className="scenario-gallery">
        <div className="section-heading">
          <h3>Scenario Gallery</h3>
          <span>Showing {scenarios.length} failures</span>
        </div>
        <div className="scenario-grid">
          {scenarios.map((scenario) => (
            <article className={`scenario-card ${scenario.tone}`} key={scenario.id}>
              <header>
                <Icon name={scenario.icon} />
                <Severity value={scenario.severity} />
              </header>
              <h4>{scenario.title}</h4>
              <p>{scenario.description}</p>
              <button
                disabled={decisionBusy === `simulate-${scenario.id}`}
                onClick={() => triggerSimulation(scenario)}
                type="button"
              >
                Execute Mock
              </button>
            </article>
          ))}
        </div>
      </section>

      <div className="simulation-grid">
        <section className="glass-panel payload-editor">
          <PanelTitle eyebrow="Alert Payload Editor" title="Prometheus Alert JSON" icon="code" />
          <pre>{JSON.stringify(payloadPreview, null, 2)}</pre>
        </section>

        <section className="glass-panel workflow-status">
          <PanelTitle eyebrow="Workflow Status" title="LangGraph Agents" icon="account_tree" />
          {["Intake Triage", "Trace Analyzer", "Mitigation Recommender"].map((label, index) => (
            <article className={index === 0 ? "active" : ""} key={label}>
              <Icon name={index === 0 ? "psychology" : index === 1 ? "analytics" : "healing"} />
              <div>
                <strong>{label}</strong>
                <p>{index === 0 ? "LangGraph node: ready" : "Waiting for upstream state..."}</p>
              </div>
              <span />
            </article>
          ))}
        </section>

        <section className="glass-panel trigger-stream">
          <PanelTitle eyebrow="Trigger Stream" title="Recent Simulations" icon="webhook" />
          {timeline.slice(-3).map((event) => (
            <article key={event.id}>
              <span>{timeOnly(event.created_at)}</span>
              <p>{event.message}</p>
            </article>
          ))}
        </section>

        <section className="glass-panel simulation-snapshot">
          <PanelTitle eyebrow="Live Intake" title="Current Incident Pressure" icon="sensors" />
          <Metric label="Health" value={systemHealth?.status || "unknown"} tone="red" />
          <Metric label="Evidence" value={evidence.length} tone="cyan" />
          <Metric label="Trace Nodes" value={traces.length} tone="green" />
        </section>
      </div>
    </div>
  );
}

function AgentTracingScreen({ activeIncident, evidence, hypotheses, recommendations, traces }) {
  const selectedTrace = traces[Math.min(6, Math.max(traces.length - 1, 0))] || traces[0];
  const stateObject = {
    incident_id: activeIncident.id,
    active_node: selectedTrace?.agent_name || "Root Cause Agent",
    evidence_count: evidence.length,
    top_hypothesis: hypotheses[0]?.title,
    recommendation: recommendations[0]?.title,
    approval_required: recommendations[0]?.requires_approval,
  };

  return (
    <div className="tracing-screen">
      <section className="trace-rail">
        <div className="section-heading">
          <h3>Step Trace</h3>
          <Status value="streaming" />
        </div>
        <div className="trace-timeline">
          {traces.map((trace, index) => (
            <article className={trace.id === selectedTrace?.id ? "active" : ""} key={trace.id}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <div>
                <p className="caps purple">Node: {trace.agent_name}</p>
                <h4>{trace.output_summary}</h4>
                <small>{timeOnly(trace.started_at)} - {timeOnly(trace.completed_at)}</small>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="trace-core">
        <div className="glass-panel state-viewer">
          <PanelTitle eyebrow={`State: ${selectedTrace?.agent_name || "RCA Engine"}`} title="state_object.json" icon="data_object" />
          <pre>{JSON.stringify(stateObject, null, 2)}</pre>
        </div>

        <section className="glass-panel vector-preview">
          <PanelTitle eyebrow="Vector Search Preview" title="RAG Context" icon="manage_search" />
          {evidence
            .filter((item) => item.source_type === "runbook")
            .slice(0, 3)
            .map((item, index) => (
              <article key={item.id}>
                <div>
                  <span>Chunk #{String(index + 1).padStart(3, "0")}</span>
                  <b>{pct(item.relevance_score)} Match</b>
                </div>
                <p>{item.summary}</p>
                <small>Source: {item.source_name}</small>
              </article>
            ))}
        </section>
      </section>

      <aside className="trace-side">
        <section className="glass-panel trace-cost">
          <PanelTitle eyebrow="Cost & Latency Engine" title="Local Trace" icon="speed" />
          <Metric label="Total Trace Cost" value="$0.000" tone="green" />
          <Metric label="Cumulative Time" value="2,842ms" tone="cyan" />
          <div className="cost-bars">
            <span style={{ width: "42%" }}>LLM</span>
            <span style={{ width: "31%" }}>RAG</span>
            <span style={{ width: "18%" }}>SYS</span>
          </div>
        </section>

        <section className="glass-panel agent-performance">
          <PanelTitle eyebrow="Agent Performance" title="Node Runtime" icon="bolt" />
          {traces.slice(0, 4).map((trace) => (
            <article key={trace.id}>
              <span>{trace.agent_name}</span>
              <b>{trace.status}</b>
            </article>
          ))}
        </section>
      </aside>
    </div>
  );
}

function TeamAccessScreen({ approvals, systemHealth }) {
  const members = [
    { name: "Darshan Sonawane", role: "Incident Commander", access: "Owner", status: "Online" },
    { name: "SRE On-Call", role: "Reliability Engineer", access: "Approver", status: "Online" },
    { name: "Backend Engineer", role: "Checkout Service", access: "Responder", status: "Away" },
  ];
  const integrations = [
    ["GitHub", "Connected"],
    ["Prometheus", "Mocked"],
    ["Grafana", "Planned"],
    ["Slack", "Future"],
  ];
  const latestApproval = approvals[approvals.length - 1];

  return (
    <div className="team-screen">
      <section className="team-hero">
        <div>
          <p className="caps purple">Team & Access Management</p>
          <h1>Team Settings & Access Control</h1>
          <p>Manage sentinel privileges, policy enforcement, and ecosystem integrations.</p>
        </div>
        <div className="team-actions">
          <button type="button">Export Audit Log</button>
          <button type="button">Invite Member</button>
        </div>
      </section>

      <div className="team-grid">
        <section className="glass-panel member-directory">
          <PanelTitle eyebrow="Member Directory" title="Incident Response Team" icon="groups" />
          {members.map((member) => (
            <article key={member.name}>
              <div className="member-avatar">{member.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</div>
              <div>
                <strong>{member.name}</strong>
                <p>{member.role}</p>
              </div>
              <Status value={member.access} />
              <span>{member.status}</span>
            </article>
          ))}
        </section>

        <section className="glass-panel integration-center">
          <PanelTitle eyebrow="Integration Center" title="Connected Tools" icon="extension" />
          {integrations.map(([name, status]) => (
            <article key={name}>
              <Icon name={name === "GitHub" ? "commit" : name === "Prometheus" ? "monitoring" : name === "Grafana" ? "dashboard" : "chat"} />
              <span>{name}</span>
              <Status value={status} />
            </article>
          ))}
        </section>

        <section className="glass-panel mitigation-policies">
          <PanelTitle eyebrow="Mitigation Policies" title="Approval Gates" icon="policy" />
          <article>
            <h4>Critical Infrastructure Rollback</h4>
            <p>Requires explicit approval for production checkout and payment services.</p>
            <span>Current status: {systemHealth?.status || "unknown"}</span>
          </article>
          <article>
            <h4>Database Schema Mutation</h4>
            <p>Automatic sentinel block for unverified migrations.</p>
            <span>Policy: enforced in demo mode</span>
          </article>
        </section>

        <section className="glass-panel notification-matrix">
          <PanelTitle eyebrow="Notification Matrix" title="Approval Audit" icon="notifications_active" />
          {latestApproval ? (
            <article>
              <strong>{pretty(latestApproval.decision)}</strong>
              <p>{latestApproval.reason}</p>
              <span>By {latestApproval.decided_by}</span>
            </article>
          ) : (
            <p>No approval action has been recorded yet.</p>
          )}
        </section>
      </div>
    </div>
  );
}

function PanelTitle({ eyebrow, title, icon }) {
  return (
    <div className="panel-title">
      <div>
        <span>{eyebrow}</span>
        <h3>{title}</h3>
      </div>
      <Icon name={icon} />
    </div>
  );
}

function Metric({ label, value, tone }) {
  return (
    <article className={`metric ${tone}`}>
      <span>{label}</span>
      <strong>{value ?? "0"}</strong>
    </article>
  );
}

function Severity({ value }) {
  return <span className={`severity ${String(value).toLowerCase()}`}>{pretty(value)}</span>;
}

function Status({ value }) {
  return <span className={`status ${String(value).toLowerCase().replaceAll("_", "-")}`}>{pretty(value)}</span>;
}
