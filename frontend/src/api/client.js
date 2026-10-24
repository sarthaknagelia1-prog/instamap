/**
 * Centralized API Client for InstaMap
 * Communicates with FastAPI backend, supporting environment variable overrides,
 * Bearer/API Key authentication, error handling, timeouts, and JSON/Multipart uploads.
 */

const API_BASE = import.meta.env?.VITE_API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000');

function getAuthHeaders() {
  const headers = {};
  const token = typeof window !== 'undefined'
    ? (localStorage.getItem('instamap_token') || localStorage.getItem('instamap_api_key') || import.meta.env?.VITE_API_KEY)
    : null;

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
    headers['X-API-Key'] = token;
  }
  return headers;
}

async function handleResponse(res) {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const body = await res.json();
      if (body.detail) {
        errorDetail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch (_) {}
    const error = new Error(errorDetail);
    error.status = res.status;
    throw error;
  }
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return res.json();
  }
  return res.text();
}

async function get(path, params = {}) {
  const url = new URL(path, API_BASE);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') {
      url.searchParams.append(k, v);
    }
  });
  const res = await fetch(url.toString(), {
    method: 'GET',
    headers: { 'Accept': 'application/json', ...getAuthHeaders() },
  });
  return handleResponse(res);
}

async function post(path, body, isFormData = false) {
  const url = new URL(path, API_BASE);
  const options = {
    method: 'POST',
    headers: { 'Accept': 'application/json', ...getAuthHeaders() },
  };
  if (isFormData) {
    options.body = body;
  } else {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }
  const res = await fetch(url.toString(), options);
  return handleResponse(res);
}

async function patch(path, body) {
  const url = new URL(path, API_BASE);
  const res = await fetch(url.toString(), {
    method: 'PATCH',
    headers: { 'Accept': 'application/json', 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export const api = {
  // Authentication & Session
  login: (payload) => post('/auth/login', payload),
  logout: () => post('/auth/logout', {}),
  getMe: () => get('/auth/me'),

  // System Health
  getHealth: () => get('/health'),

  // Creators
  getCreators: () => get('/creators'),
  getCreator: (id) => get(`/creators/${encodeURIComponent(id)}`),
  getCreatorPosts: (id, params = {}) => get(`/creators/${encodeURIComponent(id)}/posts`, params),
  getCreatorIngestionLogs: (id) => get(`/creators/${encodeURIComponent(id)}/ingestion-logs`),

  // Data & Ingestion
  getCsvTemplateUrl: () => `${API_BASE}/data/csv-template`,
  getSupportedSources: () => get('/data/sources'),
  checkDataReadiness: (formDataOrJson, isFormData = false) => post('/data-readiness', formDataOrJson, isFormData),
  ingestData: (formDataOrJson, isFormData = false) => post('/data/ingest', formDataOrJson, isFormData),
  ingestPaste: (payload) => post('/data/ingest/paste', payload),
  ingestMetaAccount: (payload) => post('/data/ingest/meta-account', payload),

  // Analytics, Virality ML & Simulation
  getAnalyticsSummary: (creatorId) => get('/analytics/summary', { creator_id: creatorId }),
  getAnalyticsPerformance: (creatorId) => get(`/analytics/performance/${encodeURIComponent(creatorId)}`),
  getAnalyticsTimeSeries: (creatorId, limit = 50) => get('/analytics/time-series', { creator_id: creatorId, limit }),
  analyzePerformance: (creatorId, limit = 100) => post('/analyze-performance', { creator_id: creatorId, limit }),
  predictVirality: (payload) => post('/analytics/predict-virality', payload),
  simulateGrowth: (payload) => post('/analytics/simulation/growth', payload),
  simulatePost: (payload) => post('/analytics/simulation/post', payload),

  // Multi-Agent Orchestrator
  runOrchestrator: (creatorId, trigger = 'manual') => post('/creator-plan', { creator_id: creatorId, trigger_event: trigger }),
  getOrchestratorRun: (jobId) => get(`/creator-plan/${encodeURIComponent(jobId)}`),
  getOrchestratorHistory: (creatorId) => get(`/creator-plan/history/${encodeURIComponent(creatorId)}`),

  // Strategy & Content
  getStrategy: (creatorId) => get(`/strategy/${encodeURIComponent(creatorId)}`),
  generateStrategy: (payload) => post('/strategy/generate', payload),
  getContentPlan: (creatorId) => get(`/content/plans/${encodeURIComponent(creatorId)}`),
  generateContentPlan: (creatorId, weekNumber = 1) => post('/content/plan', { creator_id: creatorId, week_number: weekNumber }),
  listContentDrafts: (params = {}) => get('/content/drafts', params),
  getContentDraft: (draftId) => get(`/content/drafts/${encodeURIComponent(draftId)}`),
  updateDraftStatus: (draftId, status) => patch(`/content/drafts/${encodeURIComponent(draftId)}/status`, { status }),
  markDraftPublished: (draftId, publishedPostId) => post(`/content/drafts/${encodeURIComponent(draftId)}/mark-published`, { published_post_id: publishedPostId }),

  // Experiments
  listExperiments: (creatorId) => get('/experiments', { creator_id: creatorId }),
  proposeExperiment: (creatorId, niche) => post('/experiments/propose', { creator_id: creatorId, niche }),
  createExperiment: (payload) => post('/experiments', payload),
  evaluateExperiment: (expId) => post(`/experiments/${encodeURIComponent(expId)}/evaluate`),

  // Trend Sniffer
  listNiches: () => get('/trends/niches'),
  sniffTrends: (niche, limit = 6) => get('/trends/sniff', { niche, limit }),

  // Approvals & Review Queue
  listApprovals: (params = {}) => get('/approvals', params),
  getApproval: (id) => get(`/approvals/${encodeURIComponent(id)}`),
  decideApproval: (id, decision, notes = '', rejectionReason = '') =>
    post(`/approvals/${encodeURIComponent(id)}/decision`, {
      decision,
      notes: notes || undefined,
      rejection_reason: rejectionReason || undefined,
    }),
  getApprovalStats: (creatorId) => get(`/approvals/stats/${encodeURIComponent(creatorId)}`),

  // Reporting & Executive Briefing
  getWeeklyReport: (creatorId) => get(`/reports/weekly/${encodeURIComponent(creatorId)}`),
  getWeeklyReportHtmlUrl: (creatorId) => `${API_BASE}/reports/weekly/${encodeURIComponent(creatorId)}/html`,

  // AI Growth Advisor
  chatAdvisor: (creatorId, message) => post('/advisory/chat', { creator_id: creatorId, message }),
};
