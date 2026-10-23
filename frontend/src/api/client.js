const API_BASE = window.location.origin;

async function request(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const res = await fetch(`${API_BASE}${url}`, { ...options, headers });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  getHealth: () => request('/health'),
  getCreators: () => request('/creators'),
  getMetrics: (creatorId) => request(`/analytics/performance/${creatorId}`),
  getContentPlan: (creatorId) => request(`/content/plans/${creatorId}`),
  generatePlan: (creatorId, weekNumber = 1) =>
    request('/content/plan', {
      method: 'POST',
      body: JSON.stringify({ creator_id: creatorId, week_number: weekNumber }),
    }),
  getApprovals: (creatorId) => request(`/approvals?creator_id=${creatorId}`),
  decideApproval: (approvalId, decision, feedback) =>
    request(`/approvals/${approvalId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, feedback }),
    }),
  sniffTrends: (niche, limit = 6) =>
    request(`/trends/sniff?niche=${encodeURIComponent(niche)}&limit=${limit}`),
  getExperiments: (creatorId) => request(`/experiments?creator_id=${creatorId}`),
  createExperiment: (payload) =>
    request('/experiments', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  evaluateExperiment: (expId) =>
    request(`/experiments/${expId}/evaluate`, { method: 'POST' }),
  chatAdvisor: (creatorId, message) =>
    request('/advisory/chat', {
      method: 'POST',
      body: JSON.stringify({ creator_id: creatorId, message }),
    }),
  getWeeklyReport: (creatorId) => request(`/reports/weekly/${creatorId}`),
  runOrchestrator: (creatorId) =>
    request('/creator-plan', {
      method: 'POST',
      body: JSON.stringify({ creator_id: creatorId, trigger_event: 'manual' }),
    }),
  submitOnboarding: (creatorId, niche, rawData) =>
    request('/onboarding/initiate', {
      method: 'POST',
      body: JSON.stringify({ creator_id: creatorId, niche, raw_data: rawData }),
    }),
};
