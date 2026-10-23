# Instagram Growth Engine (InstaMap)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?logo=postgresql)](https://www.postgresql.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-State_Machine-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Tests Passing](https://img.shields.io/badge/tests-57%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An autonomous, data-driven intelligence and content planning system built specifically for creators, agencies, and social media strategists.

---

## The Vision: Zero Meta API Dependency

Traditional social media management tools depend on Meta's official Graph API, which suffers from fragile access tokens, aggressive rate limits, expensive app review processes, and the constant threat of account flags or shadowbans.

**Instagram Growth Engine** is built around an **Offline-First, Zero-API-Dependency Architecture**:
- **Zero API Lock-in**: Ingests data through creator-owned exports (CSV, TSV, JSON, or direct spreadsheet/markdown clipboard paste). Compatible with exports from **Meta Business Suite**, **Metricool**, **Later**, **Hootsuite**, and **Sprout Social**.
- **Deterministic Math & Intelligence**: Metrics, engagement rates, week-over-week trends, z-score anomalies, and statistical significance testing run purely locally via mathematical algorithms without requiring an LLM.
- **Optional LLM Creative Acceleration**: Deep copywriting ideation and creative hypothesis formulations can be accelerated via Groq LLM inference, with seamless deterministic fallback if offline.
- **Manual Publishing Packages**: Produces full creator publishing packages (Hook $\rightarrow$ Body $\rightarrow$ CTA, ranked hashtags, visual camera notes, and audio suggestions) for safe, manual publishing that complies with platform guidelines.

---

## System Architecture

```
     Creator Export (CSV / TSV / JSON / Clipboard)
                           │
                           ▼
           ┌───────────────────────────────┐
           │      Data Readiness Agent     │ (40+ Header Aliases, Quality Scoring,
           └───────────────┬───────────────┘  Deduplication, Timestamp Normalization)
                           │
                           ▼
           ┌───────────────────────────────┐
           │     PostgreSQL (`instaDB`)    │ (8 Relational Tables)
           └───────┬───────────────┬───────┘
                   │               │
                   ▼               ▼
      ┌────────────────────┐   ┌────────────────────────┐
      │ Performance Engine │   │   Experiment Engine    │
      │ • Engagement Rates │   │ • Welch'\''s t-test      │
      │ • WoW Momentum     │   │ • Significance p<0.05  │
      │ • Anomaly Z-scores │   │ • Strategy Feedback    │
      └────────────┬───────┘   └────────────────────────┘
                   │                       ▲
                   ▼                       │
      ┌────────────────────────────────────┴────────────┐
      │           LangGraph Orchestrator Core           │
      │  (fetch_context -> analyze -> decide -> plan)   │
      └────────────────────┬────────────────────────────┘
                           │
                           ▼
      ┌─────────────────────────────────────────────────┐
      │       Strategy & Content Planning Agents        │
      │ • Strategy Agent: 60/30/10 format allocation    │
      │ • Content Planning Agent: 7-day weekly calendar │
      │ • Content Generation Agent: Hook->Body->CTA     │
      └─────────────────────────────────────────────────┘
```

---

## Core Capabilities

### 1. Multi-Source Ingestion & Smart Schema Mapping
- **CSV & TSV Sniffer**: Auto-detects delimiters (commas, tabs, semicolons) and handles diverse character encodings.
- **JSON Envelope Parser**: Ingests unwrapped post lists or nested API payloads.
- **Clipboard Paste**: Parses raw tabular data copied directly from Google Sheets, Microsoft Excel, or GitHub Markdown tables.
- **40+ Header Aliases**: Automatically maps third-party platform column names (`likes`, `Favorite Count`, `Engagements`, `Reach`) into standard schema keys.
- **Data Readiness Quality Scoring**: Computes a $0.0 - 1.0$ quality score, deduplicating posts and validating ISO-8601 timestamps before persisting.

### 2. Performance Intelligence & Trends
- **Deterministic Metrics**: Engagement rate, save rate, share rate, and reach efficiency.
- **Trend Detection**: Week-over-week performance delta percentage, categorizing momentum as `improving`, `declining`, or `stable`.
- **Peak Posting Windows**: Identifies top-performing day-of-week and time-of-day slots.
- **Anomaly Detection**: Flags sudden viral spikes and severe engagement drops using rolling z-scores.
- **Sub-millisecond Dashboard Caching**: In-memory TTL caching on analytical summaries.

### 3. LangGraph Orchestrator Core
- **Multi-Agent State Machine**: Coordinates workflows across dedicated agent nodes:
  $$\text{fetch\_context} \longrightarrow \text{analyze} \longrightarrow \text{decide} \longrightarrow (\text{generate\_plan} \mid \text{report\_only} \mid \text{request\_more\_data})$$
- **Deterministic Decision Engine**: Evaluates post volume (requires $\ge 3$ posts), data staleness (flags inactive creators $> 30$ days), and performance trajectory (triggers full strategic pivot if engagement drops $> 10\%$).

### 4. Strategy & Content Planning Agents
- **Strategy Agent**: Allocates format distribution (e.g. 60% Reels, 30% Carousels, 10% Images), defines 4 core content pillars, and recommends optimal weekly cadence.
- **Content Planning Agent**: Generates a 7-day scheduled calendar (Monday through Sunday) aligned with peak historical engagement windows.
- **Content Generation Agent**: Produces complete manual publishing packages:
  - **Hook**: First 3 seconds / top caption line designed for scroll-stopping retention.
  - **Body Copy**: Tactical value delivery.
  - **Call to Action (CTA)**: Specific save/share prompts.
  - **Hashtags**: Ranked niche hashtags.
  - **Visual Direction**: Camera angles, pacing notes, and on-screen text overlays.
  - **Audio Suggestions**: Recommended audio styles and pacing.

### 5. Experiment Engine & Statistical Evaluator
- **Welch'\''s Two-Sample t-Test**: Compares metric distributions between Variant A and Variant B without assuming equal variance.
- **Pure-Python Significance**: Computes two-tailed $p$-values via the Abramowitz & Stegun approximation with `math.erfc` in standard Python (zero dependency on heavy libraries like `scipy`).
- **Sample Size Threshold**: Enforces $N \ge 3$ posts per variant to prevent premature conclusions.
- **Strategy Memory Feedback Loop**: When an A/B test reaches statistical significance ($p < 0.05$), the winning insight is automatically prepended to the creator'\''s active `Strategy.strategic_priorities`.

---

## Database Schema (PostgreSQL `instaDB`)

The PostgreSQL database houses 8 core relational tables:

| Table | Purpose |
| :--- | :--- |
| `creators` | Creator profile registry and niche definitions |
| `posts` | Ingested post performance metrics with unique `(creator_id, post_id)` |
| `ingestion_logs` | Audit trail of upload attempts and readiness scores |
| `orchestrator_runs` | LangGraph workflow execution records, state dumps, and traces |
| `strategies` | High-level pillar, cadence, and format allocations |
| `content_plans` | Weekly 7-day scheduled calendar items |
| `content_drafts` | Drafted publishing packages with review status (`draft`, `approved`, `published`) |
| `experiments` | A/B hypothesis tests, variant assignments, and statistical results |
| `trending_signals` | Multi-source rising topics, velocity scores, and Instagram viral hooks |
| `approval_queue` | Human-in-the-loop review queue for drafts, strategy pivots, and experiments |

---

## Quick Start & Installation

### Prerequisites
- Python 3.10+
- PostgreSQL running locally or in Docker

### 1. Clone the Repository
```bash
git clone https://github.com/sarthaknagelia1-prog/instamap.git
cd instamap
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql://postgres:YourPassword@localhost:5432/instaDB
GROQ_API_KEY=your_groq_api_key_here  # Optional: For LLM acceleration
```

### 5. Start the Server
```bash
uvicorn backend.main:app --reload --port 8000
```
Interactive API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Running the Automated Test Suite

Run the full test suite with `pytest`:
```bash
pytest tests/ -v
```
All **46 tests** across all modules run in **~1.1s** with a 100% pass rate.

---

## REST API Reference

### Data & Ingestion
- `GET /data/sources` — List supported third-party platforms & formats
- `GET /data/csv-template` — Download standard CSV template
- `POST /data-readiness` — Validate dataset quality without saving
- `POST /data/ingest` — Ingest CSV or JSON post history
- `POST /data/ingest/paste` — Ingest copied spreadsheet/markdown text

### Analytics & Creators
- `GET /creators` — List registered creators
- `GET /creators/{id}` — Creator details and post counts
- `GET /creators/{id}/posts` — Paginated, sortable, filterable post history
- `POST /analyze-performance` — Full performance intelligence analysis
- `GET /analytics/summary` — Fast cached summary of creator metrics
- `GET /analytics/time-series` — Historical timeline for charts

### Multi-Agent Orchestration
- `POST /creator-plan` — Trigger LangGraph multi-agent analysis & workflow
- `GET /creator-plan/{job_id}` — View workflow run results and trace
- `GET /creator-plan/history/{creator_id}` — View past runs for a creator

### Strategy & Content
- `POST /strategy/generate` — Generate strategic pillars and format mix
- `GET /strategy/{creator_id}` — Retrieve active strategy
- `POST /content/plan` — Generate 7-day scheduled calendar
- `POST /content/generate` — Generate complete publishing drafts
- `GET /content/drafts` — Filter and view drafted content
- `GET /content/drafts/{id}` — Detailed view of a single draft
- `PATCH /content/drafts/{id}/status` — Update draft status (`draft`, `approved`, `published`)
- `POST /content/drafts/{id}/mark-published` — Mark draft as published on Instagram with external post ID

### Experiment Engine
- `POST /experiments/propose` — Propose an A/B experiment from metrics
- `POST /experiments` — Create custom experiment
- `GET /experiments` — List experiments for a creator
- `GET /experiments/{id}` — View a single experiment
- `POST /experiments/{id}/assign-posts` — Assign post IDs to Variant A and B
- `POST /experiments/{id}/evaluate` — Evaluate Welch'\''s t-test and trigger feedback loop

### Trend Sniffing & Viral Radar
- `GET /trends/niches` — List supported niches and community radars
- `GET /trends/sniff` — Live multi-source trend sniffing with velocity scoring & hook synthesis
- `POST /trends/sniff/custom` — Sniff custom subreddits or keywords
- `GET /trends/cached` — Retrieve active unexpired signals from PostgreSQL

### Approval & Review Layer
- `GET /approvals` — List queue items with creator and status filtering
- `GET /approvals/{id}` — Full payload snapshot of an approval item
- `POST /approvals/{id}/decision` — Submit decision (approve, reject, request revision)
- `GET /approvals/stats/{creator_id}` — Summary metrics on approval queue velocity and approval rate

---

## License

This project is licensed under the MIT License.
