# InstaMap UI Building Guide

> **Project:** InstaMap — Instagram Growth Engine  
> **Frontend:** React 18, Vite, Tailwind CSS 3, Lucide React  
> **Backend:** FastAPI, PostgreSQL, LangGraph

## 1. Product goal

Build a creator-management workspace for importing post history, understanding performance, planning content, reviewing drafts, tracking experiments, and monitoring trends. This is not a guaranteed virality predictor. The core workflow should not require Meta account access or automatic publishing.

Principles:
- **Data first:** show data freshness, coverage, quality, and metric definitions.
- **Human in control:** generated plans and drafts remain reviewable suggestions; publishing is manual.
- **Honest UI:** never present fabricated analytics as real data. Clearly label demo fixtures.
- **Offline-friendly:** core metrics should remain usable without an LLM key; label optional LLM-assisted features.
- **Action-oriented:** prioritize useful next steps over decorative metrics.

## 2. Navigation

Use a persistent sidebar on desktop and a drawer or compact navigation on mobile.

- **Overview:** creator snapshot, data freshness, performance highlights, alerts, next actions.
- **Creators:** creator list, niche, post count, latest import.
- **Data & Imports:** upload CSV/TSV/JSON, paste tabular data, preview, readiness report, import history, CSV template.
- **Analytics:** metrics, time series, content-format comparisons, peak posting windows, momentum, anomalies.
- **Strategy:** active pillars, format mix, cadence, priorities.
- **Content Calendar:** 7-day plan and linked draft statuses.
- **Draft Studio:** hook, body, CTA, hashtags, visual direction, audio suggestions, review state.
- **Experiments:** hypothesis, variants, sample sizes, metrics, evaluation.
- **Trend Radar:** topic signals, source, freshness, velocity, suggested hooks.
- **Approvals:** review queue for drafts, strategy changes, and experiments.
- **Workflow Runs:** status, result, and trace details when available.
- **Settings:** workspace preferences and configuration status; never expose secrets.

## 3. Page layouts

### Overview

Show a creator selector, date filter where supported, and a prominent Import data action. Add metric cards for posts analyzed, engagement rate, reach/impressions if available, and data readiness/last update. Below, show a performance time series, momentum, top posts, peak posting windows, data-quality warnings, pending approvals, and recent workflow runs. Hide unavailable metrics rather than inventing values.

### Data & Imports

Use a guided flow: (1) choose CSV, TSV, JSON, or paste, (2) preview columns and sample rows, (3) run readiness validation, (4) review warnings and confirm, (5) show the confirmed import result. Surface mapped columns, quality score, missing fields, duplicates, invalid timestamps, accepted/rejected rows, and actionable warnings when returned by the API. Include a CSV template download. Do not imply a direct Instagram connection.

### Analytics

Put creator/date filters above charts. Every chart needs a title, metric, unit, date range, legend, and accessible tabular alternative. Explain derived metrics such as engagement rate. Flag low sample sizes and missing data. Separate descriptive patterns from causal claims. For anomalies, show date, metric, observed value, and reason when available.

### Strategy and calendar

Show content pillars, format allocation, cadence, posting windows, and strategic priorities. Keep percentages faithful to the backend and validate that allocations total 100%. The calendar should support week and list views; each item shows date/time, format, pillar, status, and linked draft. Do not make items draggable unless rescheduling is implemented and persisted through a documented API.

### Draft Studio

Display Hook, Body Copy, CTA, Hashtags, Visual Direction, Audio Suggestions, linked calendar slot, pillar, status, and timestamps. Support copying sections, editing, and saving only through supported backend operations. Make approval/revision/rejection states explicit. Mark a post as published only after the creator has manually published it and supplied any required external post ID.

### Experiments

Show hypothesis, primary metric, variant definitions, dates, post counts, results, p-value/significance, and conclusion. Explain that statistical significance does not guarantee business impact. Show why evaluation is unavailable when sample-size requirements are unmet.

### Trend Radar

Each signal should show topic, source/link if available, detection time, velocity/relevance scale, niche, and suggested angle when returned. Show freshness and handle unavailable sources gracefully. Do not call a topic viral based only on its presence in a result.

### Approvals and workflow runs

Filter approvals by creator, type, and status. Open details before consequential decisions and display server-confirmed results. For workflows, distinguish queued/running/completed/failed only when supported by backend status. Poll only if the API supports a status endpoint; stop at terminal states and handle timeouts. Never expose secrets or unnecessary internal traces.

## 4. Design system

Aim for a calm, data-dense SaaS workspace with clear hierarchy and restrained color.

- **Primary:** indigo/violet for primary actions and active navigation.
- **Background:** light neutral; **surface:** white; **text:** near-black with muted secondary text; **border:** subtle neutral.
- **Semantic states:** green success, amber warning, red error, blue information.
- Never rely on color alone; pair status colors with text/icons.
- Use a readable system font stack. Page titles 24–30px desktop; section titles 16–20px; body 14–16px; helper text comfortably readable.
- Use a consistent 4px spacing scale, clear focus states, consistent corner radii, and restrained shadows.
- Use Lucide React consistently. Icon-only buttons need accessible names.

Build reusable components: AppShell, Sidebar, MobileNavigation, TopBar, PageHeader, CreatorSelector, DateRangeFilter, MetricCard, StatusBadge, EmptyState, ErrorState, Skeleton, DataTable, Pagination, FilterBar, ChartPanel, ChartDataTable, FileDropzone, ImportPreview, ReadinessReport, CalendarItem, DraftSection, ApprovalCard, ConfirmDialog, Toast, InlineAlert, LoadingButton, FormField, and AccessibleTooltip.

## 5. Responsive behavior

- **Desktop (1024px+):** sidebar, multi-column metric cards, side-by-side charts when readable.
- **Tablet (768–1023px):** collapsible navigation and fewer columns.
- **Mobile (<768px):** single-column layout, drawer/compact navigation, full-width primary actions, touch-friendly controls, and horizontally scrollable tables.
- Prevent page-level horizontal overflow. Dialogs must fit the viewport and remain usable with the on-screen keyboard.

## 6. Accessibility

Use semantic landmarks and ordered headings. All actions must work with a keyboard and have visible focus. Associate inputs with labels and validation errors. Announce important asynchronous results to assistive technology. Give charts accessible names and data-table alternatives. Respect reduced-motion preferences. Dialogs must manage focus and return it to the triggering control.

## 7. API integration

Configure the backend URL through a Vite environment variable, for example:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Do not put database credentials, Groq keys, or other secrets in Vite variables; client-side variables are exposed in the browser. Centralize requests in a shared API client for base URL handling, JSON/multipart requests, error parsing, cancellation/timeouts, and consistent non-2xx behavior. Keep API calls out of presentational components.

The README documents these routes. Confirm request/response schemas in FastAPI /docs or /openapi.json before implementing; the table is a route map, not a substitute for schema verification.

| UI capability | Endpoint |
|---|---|
| Creators | GET /creators; GET /creators/{id}; GET /creators/{id}/posts |
| Data sources/template | GET /data/sources; GET /data/csv-template |
| Readiness/import | POST /data-readiness; POST /data/ingest; POST /data/ingest/paste |
| Analytics | GET /analytics/summary; GET /analytics/time-series; POST /analyze-performance |
| Orchestration | POST /creator-plan; GET /creator-plan/{job_id}; GET /creator-plan/history/{creator_id} |
| Strategy | POST /strategy/generate; GET /strategy/{creator_id} |
| Content | POST /content/plan; POST /content/generate; GET /content/drafts; GET /content/drafts/{id}; PATCH /content/drafts/{id}/status; POST /content/drafts/{id}/mark-published |
| Experiments | /experiments endpoints; verify exact operations in API docs |
| Trends | /trends/* endpoints; verify exact operations in API docs |
| Approvals | /approvals endpoints; verify exact operations in API docs |

Every data-driven page needs loading, success, empty, and recoverable error states, plus retry and stale-data messaging when relevant. Do not replace failed requests with fake values. For long-running jobs, distinguish “request accepted” from “workflow completed.” Configure FastAPI CORS for the actual frontend origin; do not disable security checks as a production workaround.

## 8. Suggested structure

Adapt this to the current repository and avoid duplicating existing patterns.

```text
frontend/
  src/
    app/              # app shell and routes
    components/
      layout/
      common/
      data/
      analytics/
      content/
    pages/            # overview, creators, imports, analytics, strategy,
                      # calendar, drafts, experiments, trends, approvals
    lib/              # api client and formatters
    hooks/
    styles/
    test/
    main.jsx
```

Add a routing library or validation dependency only when needed. Use page-level hooks or a small data layer for consistent loading, error, and refresh behavior.

## 9. Implementation milestones

1. **Audit and foundation:** inspect current frontend, verify API schemas, build app shell, navigation, tokens, API configuration. Done when the app builds and shell works on desktop/mobile.
2. **Data onboarding:** upload/paste, preview, readiness report, confirmation, result, template download. Done when users understand data quality before saving and receive a truthful result.
3. **Overview and analytics:** connect creator selection, summary cards, charts, post table, filters, definitions, freshness, and empty states. Done when displayed metrics are backend-backed or explicitly demo-labelled.
4. **Strategy and content:** implement strategy, calendar, draft studio, manual publishing state, and approval actions. Done when a user can move from history to reviewable content without implying auto-publishing.
5. **Experiments, trends, approvals, workflow history:** integrate confirmed schemas and handle freshness, sample-size caveats, long-running jobs, and recovery.
6. **Quality pass:** production build, configured lint/tests, responsive checks, keyboard tests, slow network, empty database, and backend-down scenarios. Update setup instructions to match the actual app.

## 10. Testing checklist

- [ ] Navigation reaches the correct page and active state is clear.
- [ ] Creator selection refreshes dependent views.
- [ ] Invalid uploads show useful errors; readiness appears before import confirmation.
- [ ] API failures show retryable errors; empty responses are not treated as failures.
- [ ] Filters and pagination match backend behavior.
- [ ] Draft/approval status reflects server-confirmed state.
- [ ] Experiments show sample size and evaluation caveats.
- [ ] Workflow polling stops on completion/failure and handles timeouts.
- [ ] No mobile page overflow; tables have usable horizontal scrolling.
- [ ] Loading, empty, warning, and error states are consistent.
- [ ] Keyboard focus and form labels are usable.
- [ ] No secrets are shipped to the browser or exposed in error messages.
- [ ] No real-looking fabricated analytics; no implied automatic publishing.

## 11. Acceptance criteria

The first release is ready when a user can import creator-owned history and understand readiness; view backend-backed analytics with definitions and freshness; inspect a strategy, weekly plan, and complete publishing draft; review and approve outputs; understand experiment sample sizes and trend sources; and complete core flows on mobile and by keyboard. The production build must succeed and setup instructions must be reproducible.

## 12. Developer handoff

Before building each screen, inspect the existing frontend and backend route schemas. If an endpoint is missing or a response shape is uncertain, mark the feature pending integration rather than fabricating data. Keep this guide aligned with implementation as routes and product scope evolve.
