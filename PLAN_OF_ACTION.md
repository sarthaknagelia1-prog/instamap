# Plan of Action — Instagram Growth Engine (No Meta API)

*Implementation plan for the Agentic Management System. Structured as sequential phases, each with concrete tasks, deliverables, and acceptance criteria so it can be handed to an agentic coding tool (e.g. Google Antigravity) and executed/checked off step by step.*

*This version is designed to operate entirely without the Meta / Instagram Graph API. Data enters the system via CSV uploads, manual JSON input, or third-party analytics exports (e.g. Iconosquare, Later, Metricool, Hootsuite). Content output is presented as drafts for the creator to manually publish.*

---

## Phase 0 — Project Scaffolding

**Goal:** Repo, environments, and skeleton services exist and run.

- [x] Initialize project structure: `backend/`, `tests/`
- [x] Set up Python env (FastAPI, SQLAlchemy, Pydantic v2, Uvicorn)
- [ ] Set up Next.js frontend skeleton with Tailwind + shadcn/ui
- [ ] Docker Compose: Postgres, Redis, API, worker
- [x] `.env.example` with all required secrets (`DATABASE_URL`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`)
- [ ] CI pipeline (GitHub Actions): lint, type-check, test on push
- [ ] Add Celery + Redis for background task queue

**Acceptance criteria:** `docker-compose up` boots API + DB + Redis; `GET /health` returns 200.

---

## Phase 1 — Data Foundation

**Goal:** Get creator data in, validated, and stored reliably.

- [x] `data/schema_mapper.py` — canonical field mapping across sources (CSV columns, third-party export formats)
- [x] `data/ingestion/data_readiness_agent.py` — dedupe, timestamp validation, quality scoring
- [x] `data/adapters/csv_adapter.py` — CSV export ingestion (file upload or in-memory text)
- [x] `database/models.py` — `Creator`, `Post`, `IngestionLog` tables
- [x] `data/ingestion/ingest.py` — full pipeline: adapter → readiness agent → persistence
- [x] Wire `POST /data-readiness` and `POST /data/ingest` API endpoints to this pipeline
- [x] Unit tests: dedupe, bad timestamps, missing-field detection, quality score edge cases
- [x] `data/adapters/json_adapter.py` — manual JSON payload ingestion (for frontend form-based entry)
- [x] `GET /creators` — list all creators in the system
- [x] `GET /creators/{id}/posts` — list ingested posts for a creator (paginated)
- [x] `GET /creators/{id}/ingestion-logs` — ingestion history and quality scores over time
- [x] CSV template download endpoint (`GET /data/csv-template`) — pre-formatted CSV with correct headers the creator can fill in


**Data input methods (no Meta API required):**
1. **CSV upload** — creator exports data from Instagram Insights (Professional Dashboard) or any third-party tool (Iconosquare, Later, Metricool, Hootsuite) and uploads the CSV file
2. **JSON payload** — frontend form where creator manually enters post metrics
3. **Bulk paste** — creator pastes a table of data (parsed server-side)

**Acceptance criteria:** Uploading a CSV results in normalized rows in `posts` table with a logged `IngestionLog` entry. A creator can view their ingestion history via API.

---

## Phase 2 — Performance Intelligence

**Goal:** Turn stored post data into actionable metrics.

- [x] `analytics/metrics.py` — engagement rate, save rate, reach efficiency, per-content-type breakdowns
- [x] `analytics/trends.py` — trend detection (rolling averages, week-over-week deltas), best posting windows
- [x] `analytics/anomalies.py` — flag sudden drops/spikes vs. rolling baseline
- [x] Performance Analyst Agent (pluggable Groq / Claude wrapper calling the above functions)
- [x] `POST /analyze-performance` endpoint
- [x] `GET /analytics/summary` endpoint (cached, dashboard-facing)
- [x] Tests against synthetic post-history fixtures with known expected outputs

**Acceptance criteria:** Given a creator's ingested history, `/analyze-performance` returns `top_content_type`, `average_engagement_rate`, `best_posting_window`, `recent_trend`, `recommended_action`.

---

## Phase 3 — Orchestrator Core

**Goal:** A state machine that routes between agents and enforces the decision tree.

- [x] Define agent message schema (Pydantic) — shared contract for all agent I/O (`backend/agents/schemas.py`)
- [x] Implement LangGraph state machine: `ingest → analyze → decide → (plan | report-only | request_more_data)`
- [x] Decision thresholds (engagement drop %, trend duration, data staleness) as configurable rules (`decision_engine.py`)
- [x] `POST /creator-plan` — orchestrator execution endpoint with database run persistence
- [x] `GET /creator-plan/{job_id}` — polling endpoint for run results and execution traces
- [x] `GET /creator-plan/history/{creator_id}` — history of all plan executions for a creator
- [ ] Logging/tracing via Langfuse for every agent hop (prompt, tokens, latency)
- [x] Tests: orchestrator picks correct path for each defined trigger scenario (35/35 passing)


**Acceptance criteria:** Triggering `/creator-plan` on a test creator produces a full trace showing which agents ran and why, ending in either a report or a strategy/content/experiment bundle.

---

## Phase 4 — Strategy & Content Agents

**Goal:** Generate a growth strategy and drafted content from analysis output.

- [x] `agents/strategy_agent.py` — reads analysis + creator context, returns structured strategy & format allocation
- [x] `agents/content_planning_agent.py` — turns strategy into a weekly 7-day content plan
- [x] `agents/content_generation_agent.py` — drafts hook/structure/CTA/hashtags per planned item (status: `draft`)
- [x] Strategy memory persistence (Postgres `strategies`, `content_plans`, `content_drafts` tables)
- [x] `POST /strategy/generate`, `POST /content/plan`, `POST /content/generate` endpoints
- [x] `GET /content/drafts` — list all drafted content items for review with filtering
- [x] `GET /content/drafts/{id}` — view a single draft with full copy, hashtags, and posting instructions
- [x] `PATCH /content/drafts/{id}/status` — update draft status (approved / published)
- [ ] Prompt versioning set up in Langfuse/PromptLayer
- [x] Tests: schema validation on all three agents' structured outputs (40/40 passing)


**Content output format (manual publishing):**
Each drafted content item includes everything the creator needs to manually publish:
- Caption text (hook → body → CTA)
- Hashtag set (ranked by relevance)
- Suggested content type (reel / carousel / image / story)
- Recommended posting time (from trend analysis)
- Visual direction notes (what to film/photograph)
- Audio/music suggestions (for reels)

**Acceptance criteria:** End-to-end run from an analysis object produces a strategy, a weekly plan, and at least one drafted content item, all persisted and retrievable via API.

---

## Phase 5 — Experiment Engine

**Goal:** Structured hypothesis testing with statistically sound evaluation.

- [x] `experiments/models.py` (and `database/models.py`) — hypothesis, variants, controlled variables, metric, status
- [x] `agents/experiment_agent.py` — proposes experiments from strategy/analysis gaps
- [x] `experiments/evaluator.py` — significance testing (Welch's two-sample t-test with Abramowitz & Stegun p-value approximation)
- [x] `POST /experiments/propose`, `POST /experiments`, `GET /experiments`, `GET /experiments/{id}`, `POST /experiments/{id}/assign-posts`, `POST /experiments/{id}/evaluate` endpoints
- [x] On conclusive result: write outcome back to strategy memory (feedback loop)
- [x] Tests: evaluator correctness against known-significant/known-insignificant synthetic datasets (46/46 passing)

**Experiment workflow (manual execution):**
1. System proposes an experiment (e.g. "Post reels at 6 PM vs 9 PM for 2 weeks")
2. Creator executes the experiment manually by following the instructions
3. Creator re-uploads updated metrics via CSV after the experiment period
4. System evaluates results and determines if the outcome is statistically significant

**Acceptance criteria:** A completed experiment returns a winner, confidence score, and updates strategy memory only when the result is statistically conclusive.

---

## Phase 6 — Approval & Review Layer

**Goal:** Safe review flow for all agent-generated strategies and content drafts.

- [x] Action classifier: auto-approve (reports, analysis) vs. review-required (strategy pivots, content drafts)
- [x] `approval_queue` table + `GET /approvals`, `POST /approvals/{id}/decision`, `GET /approvals/stats/{creator_id}` endpoints
- [ ] Frontend approval queue UI with realtime updates (WebSocket/SSE)
- [ ] Celery Beat / Temporal schedules for weekly review cycles
- [x] Event bus wiring: `data.uploaded`, `performance.drop_detected`, `experiment.completed`, `schedule.weekly_review`
- [x] `POST /content/drafts/{id}/mark-published` — creator marks a draft as published after posting it manually, linking back the actual post metrics when re-ingested
- [x] Tests: classifier routes correctly; rejected items are archived, not deleted (57/57 passing)

**Acceptance criteria:** A content draft created by the Content Agent cannot be marked as final without an explicit approval action, and audit log records who approved what and when.

---

## Phase 7 — Reporting & Polish

**Goal:** Creator-facing visibility into what the system is doing and why.

- [ ] Weekly auto-generated report (markdown/HTML) summarizing performance, strategy changes, experiment outcomes
- [ ] Dashboard: engagement trend charts, content calendar, experiment history, approval queue
- [ ] Error monitoring (Sentry) + metrics dashboard (Prometheus/Grafana)
- [ ] Cost/token usage dashboard (Langfuse) per creator
- [ ] Onboarding flow: upload first CSV → first analysis → first strategy generated
- [ ] "What to post this week" summary view — the primary creator-facing output

**Acceptance criteria:** A new creator can go from zero to a first strategy + report within one onboarding session by uploading a single CSV export.

---

## Cross-Cutting Concerns (apply throughout)

- **No Meta API dependency:** the system never calls Instagram's API directly. All data enters via creator-uploaded CSVs or manual input. All content output is presented as drafts for the creator to publish themselves.
- **Data integrity:** the Data Readiness Agent never fabricates missing values — always report as missing.
- **Human-in-the-loop:** strategy pivots and content drafts are always review-gated. The creator decides what to publish and when.
- **Security:** encrypt LLM API keys at rest; never log full keys. Creator data is isolated per creator ID.
- **Future Meta API integration:** the adapter pattern (`BaseAdapter`) means a Graph API adapter can be plugged in later without changing any other code. The system is designed to be API-ready but does not require it.

---

## Immediate Next Actions

1. Complete Phase 3 — Orchestrator Core: Define agent message schemas (`Pydantic`) and implement LangGraph state machine (`ingest → analyze → decide → (plan | report)`).
2. Wire `POST /creator-plan` to run orchestrator workflows (synchronous or Celery-queued).
3. Connect tracing via Langfuse for agent hop monitoring (tokens, latency, prompts).
4. Implement Phase 4 Strategy & Content Generation Agents (`strategy_agent.py`, `content_planning_agent.py`, `content_generation_agent.py`).
