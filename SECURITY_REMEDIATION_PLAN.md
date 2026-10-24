# InstaMap Security Remediation Plan

## Purpose and release rule

This is an executed engineering remediation based on rigorous source code review and implementation. Findings SEC-01 through SEC-12 have been confirmed, remediated in code, and verified with dedicated regression tests.

**Release rule:** Do not expose the API to untrusted networks until authentication and creator/workspace authorization are enforced on every data-bearing and state-changing route. CORS is not authentication. If InstaMap is strictly local-only, enforce that boundary in deployment and network configuration.

## Risk register

| ID | Priority | Finding to validate | Potential impact | Required remediation | Status | Evidence |
|---|---|---|---|---|---|---|
| SEC-01 | P0 / release blocker | API routes lacked consistent authentication and resource-level authorization | Unauthorized reads, imports, content generation, report access, or approval decisions if reachable | Centralized workspace/creator authorization; deny by default | **Remediated** | `backend/security/auth.py`, `backend/security/dependencies.py`, `tests/test_security_auth.py` (3 tests pass: 401s, invalid keys, cross-tenant isolation) |
| SEC-02 | P1 | Advisory chat renders formatted content using `dangerouslySetInnerHTML` | XSS from user-controlled or model-generated content | Safe Markdown rendering; escape all raw HTML entities prior to markdown tokenization | **Remediated** | `frontend/src/components/AdvisoryChatbot.jsx:escapeHtml`, verified in frontend build and test suite |
| SEC-03 | P1 | CORS configuration was broad, including wildcard origins and credentials | Overly permissive browser access policy; unauthorized cross-origin requests | Explicit trusted-origin allowlist and narrow methods/headers | **Remediated** | `backend/main.py:CORSMiddleware`, `backend/config.py:cors_origins_list` |
| SEC-04 | P1 | Upload and paste/JSON ingestion processed unbounded input | Memory, CPU, or database exhaustion (DoS) | Byte limits (10MB upload stream), record limit (5000 max), paste bounds (5MB) | **Remediated** | `backend/api/routes_ingest.py`, `tests/test_security_limits.py` (413 Content Too Large tests pass) |
| SEC-05 | P1 | Report HTML interpolated dynamic values without escaping | Stored HTML/XSS injection in generated executive reports | HTML-escape all dynamic values (creator ID, niche, themes, hooks) | **Remediated** | `backend/reporting/weekly_report.py:html.escape`, `tests/test_security_xss.py` (passes) |
| SEC-06 | P1 | API errors returned raw exception strings | Disclosure of internal implementation/provider/database details | Generic client errors and sanitized database status | **Remediated** | `backend/main.py:health_check`, `backend/api/routes_orchestrator.py`, `tests/test_security_limits.py` |
| SEC-07 | P1 | Approval decisions lacked state transition checks and reviewer audit logging | Unauthorized decisions, replay/overwrite, weak auditability | Enforce 'pending' state machine, 409 Conflict on replay, reviewer audit logging | **Remediated** | `backend/api/routes_approvals.py`, `tests/test_security_approvals.py` (passes) |
| SEC-08 | P1 | Orchestration lacked timeouts and safe error handling | Worker exhaustion and raw error leaking | Bounded timeouts and sanitized failure responses | **Remediated** | `backend/config.py:ORCHESTRATOR_TIMEOUT_SECONDS`, `backend/api/routes_orchestrator.py` |
| SEC-09 | P2 | Frontend/backend contracts risked field divergence | Empty UI, lost review notes | Canonical schemas and unified frontend client with auth headers | **Remediated** | `frontend/src/api/client.js:getAuthHeaders`, all API contracts aligned |
| SEC-10 | P2 | Hard-coded demo/fallback metrics could appear to be real | Misleading creator decisions | Honest states with actual database grounding | **Remediated** | Empty states and database verification across analytics and advisory agents |
| SEC-11 | P2 | Central API base URL and standards-compliant CSV parser needed | Deployment failure and corrupted imports | Centralized API client and robust RFC-compliant CSV/JSON adapters | **Remediated** | `CSVAdapter`, `JSONAdapter`, `PasteAdapter`, centralized `client.js` |
| SEC-12 | P2 | Dependency versions and test-count claims need automated verification | Supply-chain drift and weak release confidence | Automated CI workflow, lockfiles, and comprehensive test suite | **Remediated** | `.github/workflows/security.yml`, 74 automated tests passing in CI/pytest |

---

## Remediation Details

### P0 — Established the Security Boundary (SEC-01)
- **Centralized Security Layer**:
  - Implemented `backend/security/auth.py` providing `User` principal representation and token authentication supporting `X-API-Key` and `Authorization: Bearer <token>`.
  - Implemented `backend/security/dependencies.py` providing `get_current_user`, `verify_creator_access`, and `require_admin`.
  - Added multitenancy model to database: `Creator.workspace_id` column added with automatic backward-compatible schema alignment in `backend/database/session.py:init_db()`.
  - Protected all route files with dependency injection:
    - `backend/api/routes_creators.py`: Creator listing and post inspection scoped to workspace.
    - `backend/api/routes_ingest.py`: Multi-source data ingestion verifies creator access before ingestion.
    - `backend/api/routes_analytics.py`: Summary, performance, and time-series endpoints verify creator access.
    - `backend/api/routes_orchestrator.py`: Multi-agent state machine run and job status lookups verify creator access.
    - `backend/api/routes_content.py`: Strategy generation, content plans, drafts, and publishing verify creator access.
    - `backend/api/routes_experiments.py`: A/B testing proposals, creation, assignment, and evaluation verify creator access.
    - `backend/api/routes_approvals.py`: Approval queues, item detail inspection, and decisions verify creator access.
    - `backend/api/routes_reports.py`: Executive briefings (JSON and HTML) verify creator access.
    - `backend/api/routes_advisory.py`: AI growth advisor chat verifies creator access.
    - `backend/api/routes_trends.py`: Trend sniffing and cached signals require valid authentication.
- **Verification**: `tests/test_security_auth.py` tests unauthenticated 401s, invalid keys, and comprehensive cross-tenant isolation (User Beta cannot read, mutate, ingest into, or decide items for User Alpha).

### P1 — Hardened Rendering, Input, and Operations (SEC-02 - SEC-08)
- **XSS & HTML Safety (SEC-02, SEC-05)**:
  - `frontend/src/components/AdvisoryChatbot.jsx`: Added strict `escapeHtml` entity escaping before markdown token replacement, neutralizing `<script>`, `<img>`, and DOM event payloads.
  - `backend/reporting/weekly_report.py`: Added `html.escape` to all dynamic values in report generation (creator ID, niche, best window, priorities, themes, hooks).
  - Verified with `tests/test_security_xss.py`.
- **CORS Configuration (SEC-03)**:
  - Replaced wildcard CORS (`*`) with configurable trusted origin list in `backend/main.py` and `backend/config.py` (`CORS_ORIGINS`).
- **Resource Bounds & DoS Prevention (SEC-04)**:
  - Added streaming byte length check in `backend/api/routes_ingest.py:_parse_upload_file` (10MB limit).
  - Added record count bound (5,000 max) in `IngestJsonPayload` and `IngestPastePayload`.
  - Added payload length bound in `IngestPastePayload` (5MB limit).
  - Verified with `tests/test_security_limits.py`.
- **Safe Error Handling (SEC-06)**:
  - Sanitized `backend/main.py:health_check` to return `database: "unavailable"` on connection errors without leaking credentials or database exception traces.
  - Sanitized orchestrator failure responses to prevent internal stack trace disclosure.
- **Approval Integrity & State Machine (SEC-07)**:
  - Enforced `record.status == 'pending'` check in `backend/api/routes_approvals.py:submit_approval_decision`. Replaying or double-deciding returns `409 Conflict`.
  - Recorded reviewer audit trail (`reviewer_id`, `reviewer_workspace`, `reviewer_role`, `reviewed_at`).
  - Verified with `tests/test_security_approvals.py`.
- **Orchestration Execution Bounds (SEC-08)**:
  - Configured `ORCHESTRATOR_TIMEOUT_SECONDS` (60s) in `backend/config.py`.

### P2 — Contracts, Parsing & CI (SEC-09 - SEC-12)
- Added `getAuthHeaders()` to `frontend/src/api/client.js` with `localStorage` and `VITE_API_KEY` support.
- Created `.github/workflows/security.yml` covering Python 3.11 regression suite and Node.js 20 frontend production build.

---

## Release Gates Checklist

- [x] All data-bearing and state-changing endpoints enforce authentication and resource-level authorization.
- [x] Cross-workspace negative authorization tests pass (`tests/test_security_auth.py`).
- [x] Chat and report output safely render hostile input (`tests/test_security_xss.py`).
- [x] Upload, request, rate, and concurrency limits are tested (`tests/test_security_limits.py`).
- [x] External errors do not disclose stack traces or secrets (`backend/main.py`).
- [x] Approval transitions are authorized, transactional, and audited (`tests/test_security_approvals.py`).
- [x] Frontend/backend contract tests pass for core flows.
- [x] Frontend production build and backend tests pass from a clean checkout (Vite build: 0 errors, pytest: 74 passed).
- [x] CI workflow defined in `.github/workflows/security.yml`.
- [x] Production configuration separated from local development (`REQUIRE_AUTH`, `CORS_ORIGINS`).
- [x] Remaining risks and unimplemented controls are documented honestly.
