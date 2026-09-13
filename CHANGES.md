# Changes Log — Instagram Growth Engine

## Summary of Changes (Phase 1 Finalization & Phase 2 Implementation)

This log documents all new modules, configurations, tests, and updates introduced to establish the production backend service, complete Phase 1 ingestion, and implement Phase 2 Performance Intelligence.

---

### 1. Configuration & Project Architecture

- **`backend/` Directory Structure**:
  Organized the project into a modular architecture:
  - `backend/config.py`: Environment variable loading using `python-dotenv` and settings for database URLs, LLM providers (Groq and Anthropic), API keys, and server port.
  - `.env.example`: Template with default configuration variables (`DATABASE_URL`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, `IG_ACCESS_TOKEN`, `IG_USER_ID`, etc.).
  - `backend/main.py`: FastAPI application entrypoint with automatic SQLite/PostgreSQL table initialization during lifespan startup, CORS middleware, `GET /health` endpoint, and router integration.

---

### 2. Database Layer (`backend/database/`)

- **`backend/database/models.py`**:
  - `Creator`: Stores creator profiles, niches, target audiences, and preferences.
  - `Post`: Stores normalized post metrics (`likes_count`, `comments_count`, `shares_count`, `saves_count`, `reach`, `impressions`, `watch_time_avg`, `engagement_rate`, `caption_text`, `hashtags`, etc.).
  - `IngestionLog`: Audit log tracking data readiness results, quality score, duplicate count, invalid timestamp count, and persisted record counts.
- **`backend/database/session.py`**:
  - Engine configuration with thread safety for SQLite and support for PostgreSQL.
  - `init_db()`: Automatically creates tables on application startup.
  - `get_db()`: Dependency yielding database sessions for FastAPI routes.
  - `get_session_factory()`: Utility for obtaining standalone session makers for background scripts and pipelines.

---

### 3. Data & Ingestion Layer (`backend/data/`)

- **`backend/data/schema_mapper.py`**:
  - Alias resolution across data sources (`postId`, `media_id`, `date`, `num_likes`, `unique_views`, etc.).
  - Content type normalization (`reel`, `carousel`, `image`, `story`).
  - Unmapped key preservation with `extra_<field_name>`.
  - Feature availability and missing-field detection (`detect_available_and_missing`).
- **`backend/data/adapters/`**:
  - `base_adapter.py`: Abstract base class defining `fetch()` and `load()`.
  - `csv_adapter.py`: Reads CSV files from file paths or in-memory text streams (supports direct file uploads).
  - `instagram_graph_adapter.py`: Read-only adapter for Meta Graph API media and post insights.
- **`backend/data/ingestion/`**:
  - `data_readiness_agent.py`: Agent 1 implementation for deduplication, timestamp validation, numeric coercion, feature coverage, and weighted quality scoring (`[0, 1]`).
  - `ingest.py`: End-to-end pipeline connecting adapters, readiness validation, and database upserts.

---

### 4. API Endpoints (`backend/api/`)

- **`backend/api/routes_ingest.py`**:
  - `POST /data-readiness`: Evaluates data quality, missing features, and readiness flag without persisting to the database. Supports both raw JSON payloads and multipart CSV file uploads.
  - `POST /data/ingest`: Executes the full pipeline (readiness verification, database upserts to `posts`, and logging to `ingestion_logs`). Supports both JSON payloads and multipart CSV file uploads.
- **`backend/api/routes_analytics.py`**:
  - `POST /analyze-performance`: Runs quantitative calculations on ingested posts, updates `engagement_rate` on post records in the database, and invokes the Performance Analyst Agent.
  - `GET /analytics/summary`: Fast, dashboard-facing summary endpoint returning total posts, average ER, top content type, and current trend.

---

### 5. Phase 2 Performance Intelligence (`backend/analytics/` & `backend/agents/`)

- **`backend/analytics/metrics.py`**:
  - `calculate_post_engagement_rate()`: Deterministic engagement calculation `(likes + comments + shares + saves) / reach`.
  - `calculate_post_metrics()`: Save rate, share rate, and reach efficiency (`reach / impressions`).
  - `calculate_aggregate_metrics()`: Aggregates across all posts, groups by content type (`reel`, `carousel`, `image`, `story`), determines `top_content_type`, and extracts top posts.
- **`backend/analytics/trends.py`**:
  - `detect_trends()`: Chronological sorting, sliding rolling average engagement rates, and week-over-week deltas with trend classification (`improving`, `declining`, `stable`).
  - `find_best_posting_window()`: Aggregates engagement by weekday and 3-hour time blocks (e.g. `Wednesday 18:00 - 21:00 UTC`).
- **`backend/analytics/anomalies.py`**:
  - `detect_anomalies()`: Detects performance spikes and sudden drops relative to historical baseline mean, standard deviation, and ratio thresholds.
- **`backend/agents/llm_client.py`**:
  - Pluggable LLM interface supporting Groq (`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`) and Anthropic Claude (`claude-3-5-sonnet-20241022`).
- **`backend/agents/analyst_agent.py`**:
  - Translates quantitative metrics into strategic `recommended_action` and executive `analysis_summary` with deterministic heuristic fallback.

---

### 6. Automated Test Suite (`tests/`)

- **`tests/conftest.py`**: Pytest fixtures for in-memory SQLite database isolation and FastAPI `TestClient`.
- **`tests/test_schema_mapper.py`**: 4 unit tests verifying field mapping, extra columns, normalization, and missing features.
- **`tests/test_data_readiness.py`**: 5 unit tests verifying deduplication, malformed timestamps, numeric coercion, and quality score edge cases.
- **`tests/test_api_ingest.py`**: 5 integration tests verifying `/health`, `/data-readiness` (JSON & CSV), and `/data/ingest` (JSON & CSV).
- **`tests/test_analytics.py`**: 7 unit and integration tests verifying metrics, trends, posting windows, anomaly detection, `/analyze-performance`, and `/analytics/summary`.
- **Status**: **21 tests passing**.

---

### 7. Roadmap Updates

- **`PLAN_OF_ACTION.md`**:
  - Checked off all completed tasks in **Phase 1** (API endpoints, tests).
  - Checked off all completed tasks in **Phase 2** (metrics, trends, anomalies, analyst agent, endpoints, tests).
  - Updated **Immediate Next Actions** to prioritize **Phase 3 — Orchestrator Core** (LangGraph state machine and `POST /creator-plan`).
