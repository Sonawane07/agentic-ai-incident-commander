import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function api(path, options) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

export async function fetchDashboardData(incidentId) {
  const [incidentList, health, runbookList] = await Promise.all([
    api("/incidents"),
    api("/system-health"),
    api("/runbooks"),
  ]);
  const selectedIncident =
    incidentList.find((incident) => incident.id === incidentId) || incidentList[0];
  if (!selectedIncident) {
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
    executionData,
    recoveryData,
    postmortemData,
  ] = await Promise.all([
    api(`/incidents/${selectedIncident.id}`),
    api(`/incidents/${selectedIncident.id}/timeline`),
    api(`/incidents/${selectedIncident.id}/evidence`),
    api(`/incidents/${selectedIncident.id}/hypotheses`),
    api(`/incidents/${selectedIncident.id}/recommendations`),
    api(`/incidents/${selectedIncident.id}/traces`),
    api(`/incidents/${selectedIncident.id}/approvals`),
    api(`/incidents/${selectedIncident.id}/executions`),
    api(`/incidents/${selectedIncident.id}/recovery-checks`),
    api(`/incidents/${selectedIncident.id}/postmortem`),
  ]);
  return {
    activeIncident: incidentDetail,
    approvals: approvalData,
    evidence: evidenceData,
    executions: executionData,
    hypotheses: hypothesisData,
    incidents: incidentList,
    postmortem: postmortemData,
    recommendations: recommendationData,
    recoveryChecks: recoveryData,
    runbooks: runbookList,
    systemHealth: health,
    timeline: timelineData,
    traces: traceData,
  };
}

export function useDashboardData(incidentId) {
  return useQuery({
    queryKey: ["dashboard", incidentId || "active"],
    queryFn: () => fetchDashboardData(incidentId),
    refetchOnWindowFocus: false,
  });
}

export function useIncidentActions(activeIncident) {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  const rerunInvestigation = useMutation({
    mutationFn: () => api(`/incidents/${activeIncident.id}/investigate`, { method: "POST" }),
    onSuccess: invalidate,
  });
  const submitDecision = useMutation({
    mutationFn: ({ decision, recommendationId }) =>
      api(`/incidents/${activeIncident.id}/approvals`, {
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
      }),
    onSuccess: invalidate,
  });
  const triggerSimulation = useMutation({
    mutationFn: (scenario) =>
      api("/alerts", {
        method: "POST",
        body: JSON.stringify({
          id: `${scenario.id}-${Date.now()}`,
          source: "prometheus-agent-simulation",
          service: scenario.service,
          severity: scenario.severity,
          metric_name: scenario.metricName,
          metric_value: scenario.metricValue,
          threshold: scenario.threshold,
          started_at: new Date().toISOString(),
          description: scenario.description,
          raw_payload: {
            cluster: "k8s-us-east-1",
            simulation: scenario.title,
            injected_from: "alert-simulation-hub",
          },
        }),
      }),
    onSuccess: invalidate,
  });
  const executeMitigation = useMutation({
    mutationFn: () =>
      api(`/incidents/${activeIncident.id}/execute-mitigation`, { method: "POST" }),
    onSuccess: invalidate,
  });
  const monitorRecovery = useMutation({
    mutationFn: () =>
      api(`/incidents/${activeIncident.id}/monitor-recovery`, { method: "POST" }),
    onSuccess: invalidate,
  });
  const resolveIncident = useMutation({
    mutationFn: () =>
      api(`/incidents/${activeIncident.id}/resolve`, {
        method: "POST",
        body: JSON.stringify({ resolved_by: "on-call-engineer" }),
      }),
    onSuccess: invalidate,
  });
  return {
    executeMitigation,
    monitorRecovery,
    rerunInvestigation,
    resolveIncident,
    submitDecision,
    triggerSimulation,
  };
}
