import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const navItems = [
  { id: "overview", label: "Active Incidents", icon: "dashboard" },
  { id: "investigation", label: "Investigation", icon: "travel_explore" },
  { id: "health", label: "System Health", icon: "monitoring" },
  { id: "archive", label: "Archive", icon: "history" },
  { id: "runbooks", label: "Runbooks", icon: "menu_book" },
  { id: "postmortem", label: "Postmortem", icon: "description" },
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

async function api(path, options) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function Icon({ name, filled = false }) {
  return (
    <span className={`material-symbols-outlined ${filled ? "filled" : ""}`} aria-hidden="true">
      {name}
    </span>
  );
}

export default function App() {
  const [view, setView] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [incidents, setIncidents] = useState([]);
  const [activeIncident, setActiveIncident] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [hypotheses, setHypotheses] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [traces, setTraces] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [postmortem, setPostmortem] = useState(null);
  const [runbooks, setRunbooks] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [decisionBusy, setDecisionBusy] = useState("");

  async function loadDashboard() {
    setError("");
    setLoading(true);
    try {
      const [incidentList, health, runbookList] = await Promise.all([
        api("/incidents"),
        api("/system-health"),
        api("/runbooks"),
      ]);
      const incident = incidentList[0];
      if (!incident) {
        throw new Error("No seeded incidents returned by backend");
      }
      const [
        incidentDetail,
        timelineData,
        evidenceData,
        hypothesisData,
        recommendationData,
        traceData,
        approvalData,
        postmortemData,
      ] = await Promise.all([
        api(`/incidents/${incident.id}`),
        api(`/incidents/${incident.id}/timeline`),
        api(`/incidents/${incident.id}/evidence`),
        api(`/incidents/${incident.id}/hypotheses`),
        api(`/incidents/${incident.id}/recommendations`),
        api(`/incidents/${incident.id}/traces`),
        api(`/incidents/${incident.id}/approvals`),
        api(`/incidents/${incident.id}/postmortem`),
      ]);
      setIncidents(incidentList);
      setActiveIncident(incidentDetail);
      setTimeline(timelineData);
      setEvidence(evidenceData);
      setHypotheses(hypothesisData);
      setRecommendations(recommendationData);
      setTraces(traceData);
      setApprovals(approvalData);
      setPostmortem(postmortemData);
      setRunbooks(runbookList);
      setSystemHealth(health);
    } catch (caught) {
      setError(caught.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  async function rerunInvestigation() {
    if (!activeIncident) return;
    setDecisionBusy("rerun");
    try {
      await api(`/incidents/${activeIncident.id}/investigate`, { method: "POST" });
      await loadDashboard();
    } finally {
      setDecisionBusy("");
    }
  }

  async function submitDecision(decision, recommendationId) {
    if (!activeIncident || !recommendationId) return;
    setDecisionBusy(decision);
    try {
      await api(`/incidents/${activeIncident.id}/approvals`, {
        method: "POST",
        body: JSON.stringify({
          recommendation_id: recommendationId,
          decision,
          decided_by: "on-call-engineer",
          reason:
            decision === "approved"
              ? "Evidence supports this mitigation."
              : decision === "rejected"
                ? "Risk is too high for current evidence."
                : "Need another investigation pass before action.",
        }),
      });
      await loadDashboard();
    } finally {
      setDecisionBusy("");
    }
  }

  const context = {
    activeIncident,
    approvals,
    decisionBusy,
    evidence,
    hypotheses,
    incidents,
    postmortem,
    recommendations,
    rerunInvestigation,
    runbooks,
    setView,
    submitDecision,
    systemHealth,
    timeline,
    traces,
  };

  return (
    <div className="vortex-shell">
      <Sidebar view={view} setView={setView} systemHealth={systemHealth} />
      <main className="vortex-main">
        <TopBar
          activeIncident={activeIncident}
          loadDashboard={loadDashboard}
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
          <ScreenRouter view={view} context={context} />
        )}
      </main>
    </div>
  );
}

function ScreenRouter({ view, context }) {
  if (view === "investigation") return <InvestigationScreen {...context} />;
  if (view === "health") return <HealthScreen {...context} />;
  if (view === "archive") return <ArchiveScreen {...context} />;
  if (view === "runbooks") return <RunbookScreen {...context} />;
  if (view === "postmortem") return <PostmortemScreen {...context} />;
  return <OverviewScreen {...context} />;
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
  decisionBusy,
  evidence,
  hypotheses,
  recommendations,
  submitDecision,
  timeline,
  traces,
}) {
  const topRecommendation = recommendations[0];
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
        <button className="primary-action full" type="button">
          <Icon name="auto_fix_high" />
          AI Deploying
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
          {recommendations.map((item, index) => (
            <article className={`mitigation-card rank-${index}`} key={item.id}>
              <div>
                <strong>{item.title}</strong>
                <span>{pct(item.confidence)}</span>
              </div>
              <p>{item.expected_impact}</p>
              <button
                disabled={Boolean(decisionBusy)}
                onClick={() => submitDecision("approved", item.id)}
                type="button"
              >
                Approve
              </button>
            </article>
          ))}
          <div className="approval-row">
            <button
              disabled={Boolean(decisionBusy)}
              onClick={() => submitDecision("rejected", topRecommendation?.id)}
              type="button"
            >
              Reject
            </button>
            <button
              disabled={Boolean(decisionBusy)}
              onClick={() => submitDecision("more_investigation_required", topRecommendation?.id)}
              type="button"
            >
              More Evidence
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

function PostmortemScreen({ activeIncident, approvals, postmortem }) {
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
              <article key={approval.id}>
                <strong>{pretty(approval.decision)}</strong>
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
