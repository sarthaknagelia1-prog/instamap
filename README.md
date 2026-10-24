# Instagram Growth Engine (InstaMap)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18.3-61dafb.svg?logo=react)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646cff.svg?logo=vite)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38bdf8.svg?logo=tailwindcss)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?logo=postgresql)](https://www.postgresql.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-State_Machine-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Tests Passing](https://img.shields.io/badge/tests-87%20passed-brightgreen.svg)]()
[![Security Hardened](https://img.shields.io/badge/security-hardened-success.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An autonomous, data-driven creator intelligence, predictive virality modeling, growth simulation, and content planning platform built for modern creators, agencies, and social media strategists.

---

## Table of Contents

- [The Vision: Zero Meta API Dependency](#the-vision-zero-meta-api-dependency)
- [System Architecture](#system-architecture)
- [Key Features](#key-features)
  - [1. Multi-Source Ingestion & Meta Account Adapter](#1-multi-source-ingestion--meta-account-adapter)
  - [2. Virality ML & Predictive Analytics Layer](#2-virality-ml--predictive-analytics-layer)
  - [3. Growth & Content Simulation Studio (Monte Carlo)](#3-growth--content-simulation-studio-monte-carlo)
  - [4. Deterministic Performance Intelligence](#4-deterministic-performance-intelligence)
  - [5. Autonomous Strategy & Planning (LangGraph)](#5-autonomous-strategy--planning-langgraph)
  - [6. Welch's t-Test Experiment Engine](#6-welchs-t-test-experiment-engine)
  - [7. Viral Trend Radar & Signal Sniffer](#7-viral-trend-radar--signal-sniffer)
  - [8. Human-in-the-Loop Review & Approval Queue](#8-human-in-the-loop-review--approval-queue)
  - [9. Interactive Advisory Engine (Chatbot)](#9-interactive-advisory-engine-chatbot)
  - [10. Modern React Dynamic SaaS Interface](#10-modern-react-dynamic-saas-interface)
- [Enterprise Security & Multitenancy](#enterprise-security--multitenancy)
- [Database Schema (PostgreSQL `instaDB`)](#database-schema-postgresql-instadb)
- [Project Directory Layout](#project-directory-layout)
- [Quick Start & Installation](#quick-start--installation)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#1-backend-setup)
  - [Frontend Setup & Build](#2-frontend-setup--build)
  - [Single-Command Unified Server](#3-single-command-unified-server)
  - [Environment Configuration (`.env`)](#4-environment-configuration-env)
- [Automated Testing Suite](#automated-testing-suite)
- [Complete REST API Reference](#complete-rest-api-reference)
- [License](#license)

---

## The Vision: Zero Meta API Dependency

Traditional creator analytics and management tools rely directly on fragile token management and unvetted third-party integrations, resulting in token expiration outages, quota throttling, and account shadowbans.

**Instagram Growth Engine (InstaMap)** operates on a flexible, creator-first architecture:
- **Direct Meta Account Sync**: Creators can safely connect their own Instagram account using their personal User/Page Access Token via `MetaAdapter` to pull real media posts and insights (reach, impressions, saves, shares).
- **Creator-Owned Data Ingestion**: Seamlessly ingest data from exports provided by **Meta Business Suite**, **Instagram Privacy Download Archives** (`posts_1.json`, `content.json`), **Metricool**, **Later**, **Hootsuite**, and **Sprout Social** in CSV, TSV, JSON, or direct clipboard copy/paste.
- **Deterministic Local Intelligence & Virality ML**: Predictive scoring, engagement rates, week-over-week momentum, z-score anomaly detection, and statistical significance testing execute locally without external API dependencies.
- **Monte Carlo Growth Simulation**: Project future 30, 60, and 90-day audience and reach trajectories under Baseline, Recommended, and Aggressive scenarios with realistic stochastic variance.
- **Complete Manual Publishing Packages**: Generates rich creator-ready publishing specifications (Hook $\rightarrow$ Body $\rightarrow$ CTA, hashtag strategy, visual pacing notes, audio recommendations) for compliant manual publishing.

---

## System Architecture

```
        Direct Meta Graph API  OR  Creator Export (CSV / JSON / Clipboard)
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                 Data Readiness & Meta Adapter               │
        │   • Meta Graph API Sync        • Official Meta JSON/CSV     │
        │   • 40+ Header Aliases         • ISO-8601 Timestamp Normal  │
        │   • Quality Scoring (0.0-1.0)   • Deduplication & Sanitizing │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                  PostgreSQL (`instaDB`)                     │
        │   • Creators (Tenants)         • Ingestion Logs             │
        │   • Posts & Metrics            • Strategies & Plans         │
        │   • Content Drafts             • Experiments                │
        │   • Trending Signals           • Approval Queue             │
        └───────┬──────────────────────────────┬──────────────────────┘
                │                              │
                ▼                              ▼
   ┌─────────────────────────┐   ┌────────────────────────────────────┐
   │     Virality ML Layer   │   │     Monte Carlo Simulation Studio  │
   │ • 5-Factor Score (0-100)│   │ • 30/60/90-Day Growth Scenarios    │
   │ • Hook Strength Triggers│   │ • 500-Draw Single-Post Distributions│
   │ • Reach Multiplier Range│   │ • Breakout Probability Confidence  │
   └────────────┬────────────┘   └────────────────────────────────────┘
                │                                  ▲
                ▼                                  │
   ┌───────────────────────────────────────────────┴──────────────────┐
   │               LangGraph Orchestrator Core Workflow               │
   │      fetch_context  ───►  analyze  ───►  decide  ───►  plan      │
   └───────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │                Strategy & Content Planning Agents                │
   │ • Strategy Agent: 60/30/10 format allocation (Reels/Carousels)   │
   │ • Content Planning Agent: 7-day scheduled calendar grid          │
   │ • Content Generation Agent: Hook -> Body -> CTA publishing kit   │
   └───────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │               Human-in-the-Loop Review & Approval                │
   │   • Concurrency-safe status updates (Draft / Approved / Rejected) │
   │   • Reviewer audit trails           • Safe manual publishing     │
   └───────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │           Interactive React 18 + Tailwind SaaS Frontend          │
   │   • Unified Dashboard • Analytics Workspace • Content Calendar   │
   │   • Virality ML Studio• Simulation Studio   • Trend Radar        │
   │   • Draft Studio      • Experiments Lab     • Approval Queue     │
   └──────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Multi-Source Ingestion & Meta Account Adapter
- **Direct Meta Account Sync**: Enables creators to provide their Meta User/Page Access Token to auto-discover their connected Instagram Business/Creator account and ingest historical media posts with insights (`reach`, `impressions`, `saves`, `shares`, `likes`, `comments`).
- **Official Meta Export Parsers**: Natively detects and ingests Meta Business Suite CSV files and Instagram "Download Your Information" JSON packages (`posts_1.json`, `content.json`).
- **Sniffer & Delimiter Detection**: Dynamically parses commas, tabs, semicolons, and diverse character encodings.
- **Unstructured Clipboard Paste**: Parses raw spreadsheets copied directly from Google Sheets, Microsoft Excel, or GitHub Markdown tables.
- **Data Readiness Quality Scoring**: Computes a deterministic $0.0 - 1.0$ data readiness score, identifying duplicate post IDs, missing metrics, and malformed timestamps before persisting.

### 2. Virality ML & Predictive Analytics Layer
Evaluates candidate posts across 5 deterministic analytical dimensions:
1. **Hook Strength & Cognitive Triggers (0–25 pts)**: Word count sweet spot (5–11 words), psychological curiosity gap ("secret", "why most", "stop making"), numerical structure ("3 mistakes", "5 tools"), and high-arousal verbs ("scale", "transform", "skyrocket").
2. **Format Discovery Affinity (0–20 pts)**: Rewards formats with high organic discovery (Reels) and repeat retention (Carousels) weighted against the creator's historical benchmark.
3. **Peak Timing Match (0–20 pts)**: Compares planned posting time against the creator's historical peak engagement window.
4. **Saveability & Shareability (0–20 pts)**: Analyzes caption value density, listicle formatting, and explicit Save/Share call-to-actions.
5. **Trend Radar Overlap (0–15 pts)**: Calculates keyword overlap with active rising viral signals.
- **Outputs**: Score (0–100), Tier (`Breakout Potential 🚀`, `High Potential 🔥`, `Moderate 📈`, `Niche ⚠️`), Predicted Reach Multiplier ($0.6\times$ to $3.5\times$), estimated reach range grounded in actual creator history, and top actionable recommendations.

### 3. Growth & Content Simulation Studio (Monte Carlo)
- **30/60/90-Day Trajectory Modeling**:
  - Compares **Baseline** (current cadence and format mix), **Recommended** (60/30/10 format allocation, peak timing, optimized hooks), and **Aggressive** (1.8x cadence, viral trend sprint).
  - Runs 100 stochastic iterations with realistic log-normal variance to generate 10th (conservative), 50th (median expected), and 90th (breakout upside) confidence intervals.
  - Generates daily milestone timelines, projected cumulative reach, and estimated net follower conversions.
- **Single-Post What-If Reach Simulator**:
  - Simulates 500 draws based on creator reach variance shifted by the Virality ML score.
  - Generates percentile distributions ($p_{10}, p_{25}, p_{50}, p_{75}, p_{90}, p_{99}$), breakout probabilities, and stochastic frequency histogram bins.

### 4. Deterministic Performance Intelligence
- **Core Engagement Metrics**: Calculates engagement rates, save rates, share rates, and reach efficiency.
- **Week-over-Week Momentum**: Computes percentage deltas and classifies velocity as `improving`, `declining`, or `stable`.
- **Peak Posting Windows**: Analyzes historical interactions to determine the top day-of-week and time-of-day slots.
- **Z-Score Anomaly Detection**: Flags viral breakout posts and unexpected performance dips using rolling statistical z-scores.
- **Sub-Millisecond Dashboard Caching**: In-memory TTL caching on analytical summaries for instant UI responsiveness.

### 5. Autonomous Strategy & Planning (LangGraph)
- **Multi-Agent State Machine**: Deterministically orchestrates state transitions:
  $$\text{fetch\_context} \longrightarrow \text{analyze} \longrightarrow \text{decide} \longrightarrow (\text{generate\_plan} \mid \text{report\_only} \mid \text{request\_more\_data})$$
- **Adaptive Strategy Allocation**: Recommends format ratios (60% Reels, 30% Carousels, 10% Static Posts) and defines 4 strategic content pillars.
- **7-Day Scheduled Calendar**: Generates scheduling slots aligned with historical peak interaction windows.
- **Publishing Package Studio**: Produces complete publishing packages (Hook, Body Copy, CTA, Ranked Hashtags, Visual & Audio Direction).

### 6. Welch's t-Test Experiment Engine
- **Unequal Variance Testing**: Compares metric distributions between Variant A and Variant B without assuming equal variance.
- **Pure-Python Significance**: Evaluates two-tailed $p$-values via the Abramowitz & Stegun approximation with `math.erfc` in standard Python.
- **Sample Size Safeguards**: Enforces $N \ge 3$ posts per variant to prevent premature conclusions.
- **Strategy Feedback Loop**: When an A/B test reaches statistical significance ($p < 0.05$), the winning hypothesis is automatically incorporated into the creator's active `Strategy.strategic_priorities`.

### 7. Viral Trend Radar & Signal Sniffer
- **Multi-Source Trend Discovery**: Scans community discussions, viral topics, and rising signals.
- **Velocity & Relevance Scoring**: Ranks signals based on freshness and niche relevance.
- **Instagram Viral Hook Synthesis**: Converts raw trending signals into ready-to-use hooks for Reels and Carousels.

### 8. Human-in-the-Loop Review & Approval Queue
- **State Transition Enforcement**: Strict lifecycle progression (`draft` $\rightarrow$ `approved` $\rightarrow$ `published` or `rejected` / `revision_requested`).
- **Concurrency & Re-decision Protection**: Prevents duplicate decisions and race conditions via HTTP 409 Conflict safeguards.
- **Audit Logging**: Captures reviewer identity, timestamps, and feedback notes for full operational governance.

### 9. Interactive Advisory Engine (Chatbot)
- **Contextual Growth Advisor**: Floating, responsive slide-out drawer accessible across all views.
- **Actionable Advice**: Provides instant guidance on content hooks, format selection, posting times, and strategy adjustments.
- **Safe Rendering**: All assistant and user messages are strictly sanitized against XSS before DOM insertion.

### 10. Modern React Dynamic SaaS Interface
- **Modern Clean Design**: Data-dense, professional dashboard built with React 18, Vite, and Tailwind CSS.
- **Multi-View Navigation**:
  - `Overview`: High-level metrics, peak windows, performance trends, recent drafts, fast data readiness preview.
  - `Creators`: Multi-creator workspace registry and switcher with tenant scoping.
  - `Data Import`: File dropzone, Direct Meta Account Sync, clipboard paste tab, and CSV template download.
  - `Analytics`: Engagement time-series charts, WoW momentum, anomaly callouts, and sortable post history.
  - `Virality ML Predictor`: Interactive 5-factor virality score gauge, reach multiplier, and actionable recommendations.
  - `Simulation Studio`: 30-90 day Monte Carlo growth forecasting and What-If post reach distributions.
  - `Strategy`: Content pillar cards, format breakdown meters, and cadence goals.
  - `Calendar`: Weekly scheduled content planner with status badges.
  - `Draft Studio`: Publishing package viewer with 1-click clipboard copy and manual publishing flow.
  - `Experiments`: Hypothesis creation, post assignment, and live Welch's t-test evaluation cards.
  - `Trend Radar`: Signal cards with velocity scores and synthesized hooks.
  - `Approvals`: Centralized decision queue with instant approve/reject actions.

---

## Enterprise Security & Multitenancy

The platform incorporates comprehensive security controls (audited and verified under `SECURITY_REMEDIATION_PLAN.md`):

| Control ID | Vulnerability Category | Mitigation Applied |
| :--- | :--- | :--- |
| **SEC-01 / SEC-02** | Multitenancy & Authorization | Every creator is scoped to a `workspace_id`. All endpoints validate creator workspace ownership via `verify_creator_access` dependency. |
| **SEC-03** | Authentication & RBAC | JWT Bearer token authentication via `get_current_user` with support for `creator`, `editor`, and `admin` roles, and safe development fallback. |
| **SEC-04 / SEC-05** | Resource Exhaustion (DoS) | Strict file upload limit (`10 MB`), row count ceiling (`5,000` posts), and clipboard paste size limit (`5 MB`). |
| **SEC-06** | Cross-Site Scripting (XSS) | User-supplied content, HTML reports, and chat messages strictly sanitized via `html.escape` and client-side HTML encoding. |
| **SEC-07** | Approval Queue Integrity | Server-enforced state transitions; conflicting re-decisions blocked with `409 Conflict`; reviewer audit logging recorded. |
| **SEC-08** | Information Disclosure | Database connection failures and internal server errors in health checks sanitized to `"unavailable"` without leaking credentials. |
| **SEC-09** | CORS Origin Security | Strict origin whitelisting in `config.py` avoiding wildcard `*` with credentials enabled. |
| **SEC-10** | Continuous Security CI | Automated GitHub Actions workflow (`.github/workflows/security.yml`) executing all security test suites on push/PR. |

---

## Database Schema (PostgreSQL `instaDB`)

The system uses 9 core relational tables in PostgreSQL:

| Table | Primary Key | Key Columns / Foreign Keys | Description |
| :--- | :--- | :--- | :--- |
| `creators` | `id` (VARCHAR) | `handle`, `niche`, `workspace_id`, `created_at` | Creator registry with workspace tenancy scoping |
| `posts` | `id` (INT) | `creator_id` (FK), `post_id`, `likes`, `comments`, `shares`, `saves`, `reach`, `posted_at` | Individual post performance metrics with unique `(creator_id, post_id)` |
| `ingestion_logs` | `id` (INT) | `creator_id` (FK), `source`, `record_count`, `readiness_score`, `timestamp` | Historical audit of data imports |
| `orchestrator_runs` | `id` (VARCHAR) | `creator_id` (FK), `status`, `current_state`, `state_dump`, `trace_log` | LangGraph workflow execution state and trace logs |
| `strategies` | `id` (INT) | `creator_id` (FK), `content_pillars`, `format_allocation`, `posting_cadence` | Active high-level content strategy |
| `content_plans` | `id` (INT) | `creator_id` (FK), `week_start`, `scheduled_posts` | 7-day scheduled content calendar items |
| `content_drafts` | `id` (INT) | `creator_id` (FK), `hook`, `body`, `cta`, `hashtags`, `status`, `external_post_id` | Publishing draft packages and approval lifecycle |
| `experiments` | `id` (INT) | `creator_id` (FK), `hypothesis`, `variant_a_posts`, `variant_b_posts`, `p_value`, `status` | A/B testing records and Welch's t-test evaluations |
| `trending_signals` | `id` (INT) | `topic`, `source`, `velocity_score`, `relevance_score`, `suggested_hooks` | Multi-source trending topics and viral signals |
| `approval_queue` | `id` (INT) | `creator_id` (FK), `item_type`, `item_id`, `status`, `decision_by`, `decision_note` | Human-in-the-loop governance queue |

---

## Project Directory Layout

```
instagram-growth-engine/
├── .github/
│   └── workflows/
│       └── security.yml               # Automated CI test suite on push/PR
├── backend/
│   ├── agents/                        # Autonomous AI & heuristic agents
│   │   ├── advisory_agent.py          # Real-time advisory & recommendation logic
│   │   ├── content_generation_agent.py# Hook -> Body -> CTA generator
│   │   ├── content_planning_agent.py  # 7-day calendar scheduler
│   │   ├── data_readiness_agent.py    # Quality scorer & header alias resolver
│   │   └── strategy_agent.py          # 60/30/10 format & pillar generator
│   ├── analytics/                     # Deterministic metrics, Virality ML & Simulation
│   │   ├── anomalies.py               # Rolling z-score anomaly detector
│   │   ├── metrics.py                 # Engagement, save, and share math
│   │   ├── simulation.py              # Monte Carlo growth & post reach simulator
│   │   ├── trends.py                  # Rolling trends & optimal posting windows
│   │   └── virality.py                # 5-factor Virality ML predictive scoring engine
│   ├── api/                           # FastAPI route handlers
│   │   ├── routes_advisory.py         # Advisory chatbot endpoints
│   │   ├── routes_analytics.py        # Summary, time series, virality ML, simulation
│   │   ├── routes_approvals.py        # Review & approval queue operations
│   │   ├── routes_content.py          # Strategy, calendar, and draft routes
│   │   ├── routes_creators.py         # Creator profile & post history
│   │   ├── routes_experiments.py      # A/B test proposal & evaluation
│   │   ├── routes_ingest.py           # File upload, paste, and Meta account sync
│   │   ├── routes_orchestrator.py     # LangGraph workflow triggering
│   │   ├── routes_reports.py          # HTML/JSON weekly report generation
│   │   └── routes_trends.py           # Trend sniffing & cached signals
│   ├── data/                          # Ingestion & normalization adapters
│   │   ├── adapters/                  # Meta Graph & Export, CSV, JSON, Paste parsers
│   │   └── ingestion/                 # Sniffer & data readiness validation pipeline
│   ├── database/                      # SQLAlchemy models & database sessions
│   │   ├── models.py                  # PostgreSQL tables
│   │   └── session.py                 # Engine, session factory & connection pooling
│   ├── experiments/                   # Statistical evaluation engine
│   │   └── evaluator.py               # Pure-Python Welch's t-test (p < 0.05)
│   ├── orchestrator/                  # Multi-agent workflow coordination
│   │   └── langgraph_core.py          # LangGraph state machine workflow
│   ├── reporting/                     # Report generation & formatting
│   │   └── weekly_report.py           # Sanitized HTML/Markdown reports
│   ├── security/                      # Enterprise security & authorization
│   │   ├── auth.py                    # JWT token parser & user roles
│   │   └── dependencies.py            # Multitenant creator access validation
│   ├── config.py                      # Application configuration & env vars
│   └── main.py                        # FastAPI entrypoint & SPA static asset mount
├── frontend/
│   ├── dist/                          # Production Vite bundle (served by FastAPI)
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js              # Centralized Axios API client
│   │   ├── components/
│   │   │   ├── shell/                 # App frame components (Sidebar, TopNav, Toasts)
│   │   │   ├── views/                 # Core view components
│   │   │   │   ├── AdvisoryDrawer.jsx # Slide-out AI advisory drawer
│   │   │   │   ├── AnalyticsView.jsx  # Charts, WoW trends, anomalies
│   │   │   │   ├── ApprovalsView.jsx  # Approval queue with decision actions
│   │   │   │   ├── CalendarView.jsx   # 7-day scheduled calendar grid
│   │   │   │   ├── CreatorsView.jsx   # Creator registry & workspace switcher
│   │   │   │   ├── DataImportView.jsx # File upload, Meta account sync, clipboard paste
│   │   │   │   ├── DraftStudioView.jsx# Publishing packages & manual publisher
│   │   │   │   ├── ExperimentsView.jsx# A/B tests & statistical evaluators
│   │   │   │   ├── OverviewDashboard.jsx # High-level KPI summary cards
│   │   │   │   ├── SimulationStudioView.jsx # Monte Carlo simulation studio
│   │   │   │   ├── TrendRadarView.jsx # Viral trend signals & hooks
│   │   │   │   └── ViralityPredictorView.jsx # 5-factor virality score gauge & optimizer
│   │   │   ├── AdvisoryChatbot.jsx    # Sanitized chat component
│   │   │   ├── AppHeader.jsx          # Top navigation & creator selector
│   │   │   └── Sidebar.jsx            # Desktop & responsive mobile sidebar
│   │   ├── App.jsx                    # Main application layout & router
│   │   ├── index.css                  # Tailwind CSS root stylesheet
│   │   └── main.jsx                   # React 18 DOM mount point
│   ├── package.json                   # Frontend dependencies
│   ├── tailwind.config.js             # Tailwind CSS configuration
│   └── vite.config.js                 # Vite bundler configuration
├── tests/                             # Comprehensive test suite (87 tests)
│   ├── test_advisory.py
│   ├── test_analytics.py
│   ├── test_api_ingest.py
│   ├── test_approvals.py
│   ├── test_creators_and_analytics.py
│   ├── test_data_readiness.py
│   ├── test_experiments.py
│   ├── test_meta_adapter.py           # Meta Graph & export archive tests
│   ├── test_multi_source_adapters.py
│   ├── test_orchestrator.py
│   ├── test_reporting_and_ui.py
│   ├── test_schema_mapper.py
│   ├── test_security_approvals.py
│   ├── test_security_auth.py
│   ├── test_security_limits.py
│   ├── test_security_xss.py
│   ├── test_simulation.py             # Growth & post simulation tests
│   ├── test_strategy_and_content.py
│   ├── test_trend_sniffer.py
│   └── test_virality.py               # Virality ML predictive scoring tests
├── requirements.txt                   # Backend Python dependencies
├── SECURITY_REMEDIATION_PLAN.md       # Complete security audit & verification log
└── README.md                          # Comprehensive project documentation
```

---

## Quick Start & Installation

### Prerequisites
- **Python**: Version 3.10 or higher
- **Node.js**: Version 18 or higher (with npm)
- **PostgreSQL**: Version 14 or higher running locally or via Docker

---

### 1. Backend Setup

```bash
# 1. Clone repository
git clone https://github.com/sarthaknagelia1-prog/instamap.git
cd instamap

# 2. Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt
```

---

### 2. Frontend Setup & Build

```bash
cd frontend

# Install frontend dependencies
npm install

# Build production assets (outputs to frontend/dist)
npm run build
cd ..
```

---

### 3. Single-Command Unified Server

The FastAPI backend natively mounts and serves the production React frontend bundle located in `frontend/dist`. Running a single command boots both the API and the web interface:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running:
- **Interactive Web App**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) or [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### 4. Environment Configuration (`.env`)

Create a `.env` file in the project root:

```env
# Database Connection (PostgreSQL)
DATABASE_URL=postgresql://postgres:YourPassword@localhost:5432/instaDB

# App Configuration
ENVIRONMENT=development
API_BASE_URL=http://127.0.0.1:8000

# Security & CORS
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000
JWT_SECRET=your_super_secret_jwt_key_here

# Optional: Groq LLM Inference (Falls back to deterministic algorithms when unset)
GROQ_API_KEY=your_groq_api_key_here
```

---

## Automated Testing Suite

The repository includes **87 comprehensive automated tests** validating data ingestion, Meta account adapters, mathematical models, Virality ML scoring, Monte Carlo growth simulations, LangGraph orchestration, statistical evaluation, security authorization, and approval workflows.

To run the full test suite:
```bash
pytest tests/ -v
```

Expected output:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.6.0
collected 87 items

tests/test_advisory.py ....                                              [  4%]
tests/test_analytics.py .......                                          [ 12%]
tests/test_api_ingest.py .....                                           [ 18%]
tests/test_approvals.py ......                                           [ 25%]
tests/test_creators_and_analytics.py ..                                  [ 27%]
tests/test_data_readiness.py .....                                       [ 33%]
tests/test_experiments.py ......                                         [ 40%]
tests/test_meta_adapter.py ....                                          [ 44%]
tests/test_multi_source_adapters.py .......                              [ 52%]
tests/test_orchestrator.py .....                                         [ 58%]
tests/test_reporting_and_ui.py ....                                      [ 63%]
tests/test_schema_mapper.py ....                                         [ 67%]
tests/test_security_approvals.py ..                                      [ 70%]
tests/test_security_auth.py ...                                          [ 73%]
tests/test_security_limits.py ...                                        [ 77%]
tests/test_security_xss.py .                                             [ 78%]
tests/test_simulation.py ...                                             [ 81%]
tests/test_strategy_and_content.py .....                                 [ 87%]
tests/test_trend_sniffer.py .....                                        [ 93%]
tests/test_virality.py ......                                            [100%]

============================= 87 passed in 10.11s =============================
```

---

## Complete REST API Reference

### Health & System
- `GET /health` — Check system health and database connectivity (sanitized against information leakage).

### Data & Ingestion
- `GET /data/sources` — List supported platforms (`meta_graph_api`, `meta_export`, `metricool`, `later`, `hootsuite`, `sprout_social`).
- `GET /data/csv-template` — Download the standard CSV ingestion template.
- `POST /data-readiness` — Preview and calculate dataset readiness score ($0.0 - 1.0$) without saving.
- `POST /data/ingest` — Ingest CSV, TSV, or JSON file export (with 10MB limit and 5,000 row cap).
- `POST /data/ingest/paste` — Ingest raw tabular text from clipboard (with 5MB limit).
- `POST /data/ingest/meta-account` — Ingest live account posts & insights directly from Meta Graph API using creator User/Page token.

### Creators, Analytics, Virality ML & Simulation
- `GET /creators` — List registered creators in current workspace.
- `POST /creators` — Register a new creator profile.
- `GET /creators/{creator_id}` — Get creator metadata, post counts, and active workspace.
- `GET /creators/{creator_id}/posts` — Retrieve paginated, sortable, and filterable post history.
- `POST /analyze-performance` — Run full analytical evaluation (rates, velocity, anomalies).
- `GET /analytics/summary` — Fast cached summary of engagement and momentum.
- `GET /analytics/time-series` — Historical time-series metrics formatted for charting.
- `POST /analytics/predict-virality` — Compute 5-factor virality score (0-100), tier, reach multiplier, and recommendations.
- `POST /analytics/simulation/growth` — Run 30/60/90-day Monte Carlo growth trajectory simulations across scenarios.
- `POST /analytics/simulation/post` — Run 500 stochastic draws to project single-post reach distribution and breakout odds.

### Strategy & Content Workflow
- `POST /strategy/generate` — Generate strategic pillars and format allocation (60/30/10).
- `GET /strategy/{creator_id}` — Retrieve active strategy and strategic priorities.
- `POST /content/plan` — Generate 7-day scheduled content calendar.
- `GET /content/plan/{creator_id}` — Retrieve active weekly calendar items.
- `POST /content/generate` — Generate complete publishing drafts (Hook $\rightarrow$ Body $\rightarrow$ CTA).
- `GET /content/drafts` — List and filter drafted content.
- `GET /content/drafts/{id}` — Get single publishing package details.
- `PATCH /content/drafts/{id}/status` — Transition draft status (`draft`, `approved`, `published`, `rejected`).
- `POST /content/drafts/{id}/mark-published` — Record manual publication with external Instagram post ID.

### Multi-Agent Orchestrator (LangGraph)
- `POST /creator-plan` — Trigger end-to-end LangGraph state machine workflow.
- `GET /creator-plan/{job_id}` — Inspect execution state, step outcomes, and trace logs.
- `GET /creator-plan/history/{creator_id}` — View previous orchestrator runs.

### Experimentation & Welch's t-Test
- `POST /experiments/propose` — Suggest an A/B test based on current creator performance.
- `POST /experiments` — Create an A/B test hypothesis.
- `GET /experiments` — List experiments for a creator.
- `GET /experiments/{id}` — Retrieve experiment details.
- `POST /experiments/{id}/assign-posts` — Assign historical post IDs to Variant A and Variant B.
- `POST /experiments/{id}/evaluate` — Execute Welch's t-test ($p < 0.05$) and trigger strategy feedback loop.

### Viral Trend Radar
- `GET /trends/niches` — List supported niches and community radars.
- `GET /trends/sniff` — Live multi-source trend sniffing with velocity scoring & hook synthesis.
- `POST /trends/sniff/custom` — Sniff custom keywords or community topics.
- `GET /trends/cached` — Retrieve active, unexpired trending signals.

### Human-in-the-Loop Approval Queue
- `GET /approvals` — List pending approvals filtered by creator and status.
- `GET /approvals/{id}` — View full payload snapshot of an approval item.
- `POST /approvals/{id}/decision` — Submit decision (`approved`, `rejected`, `revision_requested`) with reviewer notes.
- `GET /approvals/stats/{creator_id}` — Queue velocity, pending count, and approval rates.

### Advisory & Reports
- `POST /advisory/chat` — Real-time contextual growth advice and copywriting feedback.
- `GET /reports/weekly/{creator_id}` — Generate sanitized weekly summary report (JSON or HTML).

---

## License

This project is licensed under the [MIT License](LICENSE).
