# Plan of Action — Instagram Growth Engine

*Implementation plan for the Agentic Management System. Structured as sequential phases, each with concrete tasks, deliverables, and acceptance criteria so it can be handed to an agentic coding tool (e.g. Google Antigravity) and executed/checked off step by step.*

---

## Phase 0 — Project Scaffolding

**Goal:** Repo, environments, and skeleton services exist and run.

- [ ] Initialize monorepo structure: `frontend/`, `backend/`, `data/`, `database/`, `agents/`
- [ ] Set up Python env (FastAPI, SQLAlchemy, Pydantic v2, Celery, Anthropic SDK)
- [ ] Set up Next.js frontend skeleton with Tailwind + shadcn/ui
- [ ] Docker Compose: Postgres, Redis, API, worker
- [ ] `.env.example` with all required secrets (DB URL, `ANTHROPIC_API_KEY`, `IG_ACCESS_TOKEN`, `IG_USER_ID`)
- [ ] CI pipeline (GitHub Actions): lint, type-check, test on push

**Acceptance criteria:** `docker-compose up` boots API + DB + Redis; `GET /health` returns 200.

---

## Phase 1 — Data Foundation

**Goal:** Get creator data in, validated, and stored reliably.

- [x] `data/schema_mapper.py` — canonical field mapping across sources
- [x] `data/ingestion/data_readiness_agent.py` — dedupe, timestamp validation, quality scoring
- [x] `data/adapters/csv_adapter.py` — CSV export ingestion
- [x] `data/adapters/instagram_graph_adapter.py` — Graph API ingestion (read-only)
- [x] `database/models.py` — `Creator`, `Post`, `IngestionLog` tables
- [x] `data/ingestion/ingest.py` — full pipeline: adapter → readiness agent → persistence
- [x] Wire `POST /data-readiness` and `POST /data/ingest` API endpoints to this pipeline
- [ ] Add Meta OAuth flow (Instagram Login or Graph API via Facebook Page) — see Phase 6 note on account access tiers
- [x] Unit tests: dedupe, bad timestamps, missing-field detection, quality score edge cases

**Acceptance criteria:** Uploading a CSV or connecting an IG account results in normalized rows in `posts` table with a logged `IngestionLog` entry.

---

## Phase 2 — Performance Intelligence

**Goal:** Turn stored post data into actionable metrics.

- [x] `analytics/metrics.py` — engagement rate, save rate, reach efficiency, per-content-type breakdowns
- [x] `analytics/trends.py` — trend detection (rolling averages, week-over-week deltas), best posting windows
- [x] `analytics/anomalies.py` — flag sudden drops/spikes vs. rolling baseline
- [x] Performance Analyst Agent (pluggable Groq / Claude tool-use wrapper calling the above functions)
- [x] `POST /analyze-performance` endpoint
- [x] `GET /analytics/summary` endpoint (cached, dashboard-facing)
- [x] Tests against synthetic post-history fixtures with known expected outputs

**Acceptance criteria:** Given a creator's ingested history, `/analyze-performance` returns `top_content_type`, `average_engagement_rate`, `best_posting_window`, `recent_trend`, `recommended_action` matching the schema in the design doc.

---

## Phase 3 — Orchestrator Core

**Goal:** A state machine that routes between agents and enforces the decision tree.

- [ ] Define agent message schema (Pydantic) — shared contract for all agent I/O
- [ ] Implement LangGraph state machine: `ingest → analyze → decide → (plan | report-only)`
- [ ] Decision thresholds (engagement drop %, trend duration, data staleness) as configurable rules
- [ ] `POST /creator-plan` — synchronous or Celery-queued orchestrator run
- [ ] `GET /creator-plan/{job_id}` — polling for async runs
- [ ] Logging/tracing via Langfuse for every agent hop (prompt, tokens, latency)
- [ ] Tests: orchestrator picks correct path for each of the 3–4 defined trigger scenarios

**Acceptance criteria:** Triggering `/creator-plan` on a test creator produces a full trace showing which agents ran and why, ending in either a report or a strategy/content/experiment bundle.

---

## Phase 4 — Strategy & Content Agents

**Goal:** Generate a growth strategy and drafted content from analysis output.

- [ ] `agents/strategy_agent.py` — Claude tool-use call, reads analysis + creator/strategy memory, returns structured strategy
- [ ] `agents/content_planning_agent.py` — turns strategy into a weekly content plan
- [ ] `agents/content_generation_agent.py` — drafts hook/structure/CTA/hashtags per planned item (status: `draft`)
- [ ] Strategy memory persistence (Postgres table + optional pgvector embedding for semantic recall)
- [ ] `POST /strategy/generate`, `POST /content/plan`, `POST /content/generate` endpoints
- [ ] Prompt versioning set up in Langfuse/PromptLayer
- [ ] Tests: schema validation on all three agents' structured outputs

**Acceptance criteria:** End-to-end run from an analysis object produces a strategy, a weekly plan, and at least one drafted content item, all persisted and retrievable via API.

---

## Phase 5 — Experiment Engine

**Goal:** Structured hypothesis testing with statistically sound evaluation.

- [ ] `experiments/models.py` — hypothesis, variants, controlled variables, metric, status
- [ ] `agents/experiment_agent.py` — proposes experiments from strategy/analysis gaps
- [ ] `experiments/evaluator.py` — significance testing (e.g. two-proportion z-test or bootstrap, depending on metric type)
- [ ] `POST /experiments`, `GET /experiments/{id}`, `POST /experiments/{id}/evaluate` endpoints
- [ ] On conclusive result: write outcome back to strategy memory (feedback loop)
- [ ] Tests: evaluator correctness against known-significant/known-insignificant synthetic datasets

**Acceptance criteria:** A completed experiment returns a winner, confidence score, and updates strategy memory only when the result is statistically conclusive.

---

## Phase 6 — Automation & Approval Layer

**Goal:** Safe, human-approved execution of agent decisions.

- [ ] Action classifier: auto-execute vs. approval-required (publishing, spend, account changes)
- [ ] `approval_queue` table + `GET /approvals`, `POST /approvals/{id}/decision` endpoints
- [ ] Frontend approval queue UI with realtime updates (WebSocket/SSE)
- [ ] Celery Beat / Temporal schedules for weekly review cycles
- [ ] Event bus wiring: `data.uploaded`, `performance.drop_detected`, `experiment.completed`, `schedule.weekly_review`
- [ ] **Instagram Graph API account-access plan (see note below):**
  - [ ] Standard Access: publish to your own connected account via Instagram Tester role (no App Review needed)
  - [ ] For serving other creators' accounts: submit Meta App Review for Advanced Access (requires Business verification, live-mode app, screencast) — budget 4–8 weeks
  - [ ] Interim: allow manual "approve and I'll post myself" fallback for accounts not yet Advanced-Access-approved
- [ ] Tests: classifier routes correctly; rejected actions never execute

**Acceptance criteria:** A draft post created by the Content Agent cannot be published without an explicit approval action, and audit log records who approved what and when.

---

## Phase 7 — Reporting & Polish

**Goal:** Creator-facing visibility into what the system is doing and why.

- [ ] Weekly auto-generated report (markdown/HTML) summarizing performance, strategy changes, experiment outcomes
- [ ] Dashboard: engagement trend charts, content calendar, experiment history, approval queue
- [ ] Error monitoring (Sentry) + metrics dashboard (Prometheus/Grafana)
- [ ] Cost/token usage dashboard (Langfuse) per creator
- [ ] Onboarding flow: connect account → initial data pull → first strategy generated

**Acceptance criteria:** A new creator can go from zero to a first strategy + report within one onboarding session, without touching the database directly.

---

## Cross-Cutting Concerns (apply throughout)

- **Security:** never log full access tokens; encrypt tokens at rest; scope IG permissions to minimum needed.
- **Rate limits:** respect Graph API's Business Use Case limits (~200 calls/user/hour); cache aggressively.
- **Data integrity:** the Data Readiness Agent never fabricates missing values — always report as missing.
- **Human-in-the-loop:** publishing and strategy pivots are always approval-gated until trust is established; auto-execution is an explicit, later opt-in per creator.

---

## Immediate Next Actions
 
1. Complete Phase 3 — Orchestrator Core: Define agent message schemas (`Pydantic`) and implement LangGraph state machine (`ingest → analyze → decide → (plan | report)`).
2. Wire `POST /creator-plan` to run orchestrator workflows (synchronous or Celery-queued).
3. Connect tracing via Langfuse for agent hop monitoring (tokens, latency, prompts).
4. Implement Phase 4 Strategy & Content Generation Agents (`strategy_agent.py`, `content_planning_agent.py`, `content_generation_agent.py`).
