# WiseMint — FinAdvisor

AI-powered financial advisory chatbot for educational guidance. Built with a ReAct agent loop, hybrid RAG retrieval, live market data, and deterministic finance math — all behind a safety layer that filters jailbreaks, detects user distress, and enforces educational disclaimers.

> **Disclaimer:** This tool is for educational purposes only and does not constitute financial advice.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start (UV — local Python environment)](#quick-start-uv--local-python-environment)
- [Quick Start (Docker)](#quick-start-docker)
- [Environment Variables](#environment-variables)
- [Project Layout](#project-layout)
- [Modules](#modules)
  - [Agent Orchestrator](#agent-orchestrator)
  - [Knowledge Base](#knowledge-base)
  - [Market Data](#market-data)
  - [Finance Math Tools](#finance-math-tools)
  - [User Memory & Profiles](#user-memory--profiles)
  - [Safety & Guardrails](#safety--guardrails)
  - [Streamlit UI](#streamlit-ui)
- [Running Tests](#running-tests)
- [Ingesting Knowledge Base Documents](#ingesting-knowledge-base-documents)
- [Development Workflow](#development-workflow)
- [API Keys](#api-keys)

---

## Features

- **Conversational AI** — Chat interface powered by Groq (Llama-3.3-70B) with session history
- **Hybrid RAG** — ChromaDB vector search + BM25 keyword search fused with Reciprocal Rank Fusion (RRF)
- **Live Market Data** — Real-time stock quotes and sector performance via Alpha Vantage, cached for 30 minutes
- **Deterministic Finance Math** — Compound interest, loan amortization, retirement glide path, and portfolio concentration risk — all calculated without LLM involvement
- **User Personalization** — SQLite profiles (age, retirement age, monthly savings) injected as context into every LLM call
- **Safety Sandwich** — Input guard blocks prompt injection and detects user distress; output filter scrubs directives and appends disclaimers
- **Portfolio Visualizer** — Interactive Plotly donut chart from ticker:weight input in the sidebar
- **Experiment Tracking** — MLflow integration for logging and monitoring
- **Fully Dockerized** — Three-service compose stack (app, ChromaDB, MLflow) with persistent volumes

---

## Architecture

```
User Message
     │
     ▼
┌─────────────┐      blocked       ┌──────────────────┐
│ Input Guard │ ─────────────────► │ Safety Response  │
└─────────────┘                    └──────────────────┘
     │ safe
     ▼
┌──────────────────────────────────────────────────┐
│               ReAct Agent Loop                   │
│  Intent Classifier → Tool Selection → Reasoning  │
│                                                  │
│  Tools:                                          │
│  ┌─────────────────┐  ┌──────────────────────┐  │
│  │  retrieve_knowledge│  │  get_market_data   │  │
│  │  (ChromaDB+BM25) │  │  (Alpha Vantage)     │  │
│  └─────────────────┘  └──────────────────────┘  │
│  ┌─────────────────┐  ┌──────────────────────┐  │
│  │  finance_math   │  │  get_user_profile    │  │
│  │  (deterministic)│  │  (SQLite)            │  │
│  └─────────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────────┘
     │
     ▼
┌───────────────┐
│ Output Filter │  (scrubs directives, appends disclaimer)
└───────────────┘
     │
     ▼
  Response
```

**Services (Docker Compose):**

| Service | Port | Purpose |
|---------|------|---------|
| `app` | 8501 | Streamlit UI |
| `chromadb` | 8000 | Vector database (HTTP) |
| `mlflow` | 5000 | Experiment tracking |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| LLM Inference | Groq — Llama-3.3-70B |
| UI | Streamlit |
| Vector DB | ChromaDB |
| Embeddings | BAAI/bge-small-en-v1.5 (sentence-transformers) |
| Sparse Retrieval | rank-bm25 |
| Market Data | Alpha Vantage API |
| Caching | diskcache (30-min TTL) |
| User Profiles | SQLite |
| Charts | Plotly |
| Experiment Tracking | MLflow |
| Data Validation | Pydantic |
| HTTP Client | httpx |
| Containerization | Docker + Compose |
| Testing | pytest |

---

## Quick Start (UV — local Python environment)

[UV](https://github.com/astral-sh/uv) is the fastest way to set up a local dev environment without Docker.

```bash
# 1. Install uv (Windows PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Create a Python 3.12 virtual environment
uv venv --python 3.12

# 3. Activate it
.venv\Scripts\Activate.ps1      # PowerShell
# source .venv/Scripts/activate # Git Bash

# 4. Install the project + all dependencies
uv pip install -e .

# 5. Verify
pytest tests/unit/

# 6. Run the app locally (requires ChromaDB running separately, e.g. via Docker)
streamlit run src/ui/app.py
```

> Step 6 needs a reachable ChromaDB instance (`CHROMA_HOST`/`CHROMA_PORT`). Easiest way: `docker compose up chromadb` in another terminal, then run Streamlit locally for fast iteration.

## Quick Start (Docker)

**Prerequisites:** Docker, Docker Compose, and API keys for Groq and Alpha Vantage.

```bash
# 1. Clone the repo
git clone <repo-url>
cd WiseMint

# 2. Configure environment
cp .env.example .env
# Edit .env and fill in GROQ_API_KEY and ALPHA_VANTAGE_KEY

# 3. Start all services
docker compose up --build

# App:      http://localhost:8501
# ChromaDB: http://localhost:8000
# MLflow:   http://localhost:5000
```

To stop:
```bash
docker compose down
```

To reset all persistent data (profiles, vector DB, MLflow runs):
```bash
docker compose down -v
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in values:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Groq API key for LLM inference |
| `ALPHA_VANTAGE_KEY` | Yes | — | Alpha Vantage key for market data |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model ID |
| `CACHE_TTL_SECONDS` | No | `1800` | Market data cache TTL (seconds) |
| `MAX_AGENT_STEPS` | No | `6` | Max ReAct iterations per query |
| `CHROMA_API_KEY` | No | — | Chroma Cloud API key; if set, uses Chroma Cloud instead of local ChromaDB |
| `CHROMA_TENANT` | No (Yes if `CHROMA_API_KEY` set) | — | Chroma Cloud tenant ID |
| `CHROMA_DATABASE` | No | `fin_adv_kb` | Chroma Cloud database name |
| `CHROMA_HOST` | No | `api.trychroma.com` (cloud) / `localhost` (local) | ChromaDB host |
| `CHROMA_PORT` | No | `8000` | Local ChromaDB port (ignored for Cloud) |

---

## Project Layout

```
WiseMint/
├── src/
│   ├── agent/          # ReAct orchestrator + intent classifier
│   ├── kb/             # ChromaDB + BM25 hybrid retrieval
│   ├── market/         # Alpha Vantage API + disk cache
│   ├── tools/          # Deterministic finance math
│   ├── memory/         # SQLite user profiles
│   ├── safety/         # Input/output guardrails
│   └── ui/             # Streamlit app
├── tests/
│   └── unit/           # Unit tests (finance math, safety, cache)
├── data/
│   ├── knowledge_base/ # Drop .txt docs here for ingestion
│   ├── market_cache/   # Runtime diskcache (auto-created)
│   ├── bm25_index.pkl  # BM25 index (created on ingest)
│   └── profile.db      # SQLite user profiles (auto-created)
├── resources/          # Architecture diagrams and design docs
├── mlruns/             # MLflow experiment artifacts
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## Modules

### Agent Orchestrator

**`src/agent/`**

The core reasoning loop. Implements a ReAct (Reason + Act) pattern: the LLM reasons step-by-step, decides which tool to call, processes the result, and iterates until it has a final answer.

**Entrypoint:** `orchestrator.run(user_message, user_id, history)`

- Builds a system prompt that frames the assistant as an educational financial guide
- Injects the user's profile (age, retirement target, savings) as context
- Runs up to `MAX_AGENT_STEPS` tool-calling iterations
- Returns the filtered assistant response

**Intent Classifier:** `intent_classifier.classify(message, client)`

Zero-shot classification into one of four intents:

| Intent | Description |
|--------|-------------|
| `QA` | General financial questions (answered via KB retrieval) |
| `PORTFOLIO` | Portfolio analysis and allocation questions |
| `PLANNING` | Retirement, savings, or goal planning |
| `GENERAL` | Catch-all for off-topic or ambiguous queries |

---

### Knowledge Base

**`src/kb/`**

Hybrid retrieval pipeline combining dense (semantic) and sparse (keyword) search.

**Ingestion** (`ingest.py`):
- Reads `.txt` files from a directory
- Chunks text at 800 characters with 100-character overlap
- Stores chunks in ChromaDB (with embeddings) and serializes a BM25 index to `data/bm25_index.pkl`

**Embeddings** (`embeddings.py`):
- Model: `BAAI/bge-small-en-v1.5` via sentence-transformers
- Lazy-loaded singleton to avoid re-loading on every call
- Query encoding prepends the BGE instruction prefix for better retrieval accuracy

**Retrieval** (`retrieval.py`): `retrieve(query, top_k=5)`
1. Dense search: query ChromaDB by embedding similarity
2. Sparse search: query BM25 index by tokenized keywords
3. Merge via Reciprocal Rank Fusion (RRF) — a rank-based fusion that rewards documents appearing in both result sets
4. Returns top-k chunks with `{text, source, rrf_score}`

---

### Market Data

**`src/market/`**

Live stock quotes and sector performance from Alpha Vantage, with transparent disk caching.

**`get_quote(ticker)`**
- Checks diskcache first (returns `_cached: True` if hit)
- Falls back to Alpha Vantage `GLOBAL_QUOTE` endpoint
- Returns: `{price, change_percent, volume, trading_day}` or `{error: str}`

**`get_sector_performance()`**
- Fetches Alpha Vantage sector rankings
- Cached with the same 30-minute TTL

Cache is stored in `data/market_cache/` and survives container restarts via a Docker volume.

---

### Finance Math Tools

**`src/tools/`**

Deterministic financial calculations with no LLM or network calls — results are always reproducible and auditable.

**`calculate(operation, params)`** — main dispatcher

| Operation | Inputs | Outputs |
|-----------|--------|---------|
| `compound_interest` | `principal`, `annual_rate`, `years`, `compounds_per_year` (default 12) | `future_value`, `interest_earned` |
| `amortization` | `principal`, `annual_rate`, `term_months` | `monthly_payment`, `total_paid`, `total_interest` |
| `glide_path` | `current_age`, `retirement_age`, `monthly_contribution`, `current_savings`, `annual_return` | `projected_balance`, `recommended_equity_pct`, `years_to_retirement` |
| `portfolio_risk` | `holdings: {ticker: weight}` | `herfindahl_index`, `concentration_risk` (low/medium/high), `largest_position` |

The glide path uses the **110-minus-age** rule to recommend equity/bond allocation at retirement. Portfolio concentration risk uses the **Herfindahl–Hirschman Index (HHI)** as the concentration metric.

All calculation errors (bad inputs, division by zero, missing keys) return `{error: str}` rather than raising exceptions, so the agent can handle them gracefully.

---

### User Memory & Profiles

**`src/memory/`**

Lightweight personalization via SQLite. User profiles persist across sessions.

**Schema:**
```sql
CREATE TABLE profiles (
    user_id  TEXT PRIMARY KEY,
    data     TEXT NOT NULL  -- JSON-serialized dict
)
```

**Functions:**

| Function | Description |
|----------|-------------|
| `get_profile(user_id)` | Returns profile dict, or `{}` if not found |
| `update_profile(user_id, updates)` | Merges updates and upserts |
| `profile_to_context(user_id)` | Formats profile as a plain-text LLM context string |

**Stored fields** (set via the UI sidebar):
- `age` — User's current age
- `retirement_age` — Target retirement age
- `monthly_savings` — Monthly contribution amount

---

### Safety & Guardrails

**`src/safety/`**

A two-stage safety layer wrapping every agent interaction.

**Input Guard** (`input_guard.py`): `check(message) → (is_safe, reason)`

Scans for two threat categories using regex:

| Category | Trigger Phrases | Response |
|----------|----------------|----------|
| Prompt Injection | "ignore previous instructions", "you are now", "act as", "jailbreak", "pretend", "bypass" | Generic refusal |
| User Distress | "suicide", "kill myself", "end my life", "self harm", "hopeless", "no reason to live" | Crisis helpline reference (988) |

**Output Filter** (`output_filter.py`): `filter_output(text) → str`

Post-processes every agent response:
- **Directive scrubbing:** Replaces imperative financial advice (`"you must buy"` → `"consider researching"`, `"immediately sell"` → `"potentially consider"`, `"guaranteed return"` → `"potential return (not guaranteed)"`)
- **Auto-disclaimer:** If the response contains investment-related keywords (`invest`, `buy`, `sell`, `portfolio`, `stock`, `bond`, `fund`, etc.), appends: *"For educational purposes only — not financial advice."*

---

### Streamlit UI

**`src/ui/app.py`**

Single-page chat application with a feature-rich sidebar.

**Chat Panel:**
- Renders conversation history with styled user/assistant bubbles
- Passes the last 6 turns as context to the agent
- Shows a "Thinking…" spinner during agent execution
- Applies the full safety pipeline (input guard → agent → output filter) before display

**Sidebar:**
- **Profile editor** — Age, retirement age, monthly savings sliders → saved to SQLite on "Update profile"
- **Portfolio chart** — Enter `AAPL:60,MSFT:40` style input → interactive Plotly donut chart of allocation

---

## Running Tests

```bash
# Install in editable mode (only needed once)
pip install -e .

# Run all unit tests
pytest tests/unit/

# Run a specific file
pytest tests/unit/test_finance_math.py -v
```

**Test coverage:**

| File | What it tests |
|------|--------------|
| `test_finance_math.py` | Compound interest, amortization, glide path, portfolio risk, error handling |
| `test_safety.py` | Input guard (clean/injection/distress), output filter (disclaimer, scrubbing) |
| `test_cache.py` | Disk cache TTL behavior |

---

## Ingesting Knowledge Base Documents

Place `.txt` files in `data/knowledge_base/`, then run:

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from src.kb.ingest import ingest_directory; n = ingest_directory('data/knowledge_base'); print('chunks ingested:', n)"
```

> `load_dotenv()` is required here — outside of `src/ui/app.py` nothing loads `.env` automatically. Without it, Chroma Cloud vars (`CHROMA_API_KEY`/`CHROMA_TENANT`/`CHROMA_DATABASE`) won't be picked up and ingestion will fall back to a local ChromaDB at `CHROMA_HOST`/`CHROMA_PORT`, which will fail to connect unless one is running (e.g. `docker compose up chromadb`).

This will:
1. Chunk each document at 800 characters with 100-character overlap
2. Embed chunks using `bge-small-en-v1.5`
3. Store embeddings in ChromaDB (Chroma Cloud if `CHROMA_API_KEY` is set, otherwise local)
4. Serialize a BM25 index to `data/bm25_index.pkl`

After ingestion, the agent's `retrieve_knowledge` tool will use these documents to answer user questions.

> **Note:** PDF ingestion requires pre-converting to `.txt`. PDFs are excluded from the repository via `.gitignore`.

---

## Development Workflow

The project follows a layer-by-layer iteration protocol:

```
1. Code one layer (or modify a module)
2. docker compose build
3. Smoke test in the UI (http://localhost:8501)
4. Update resources/FinAdvisor_Architecture_Diagram.html if architecture changed
5. Commit
```

**Useful commands:**

```bash
# Rebuild and restart only the app service (faster than full rebuild)
docker compose up --build app

# Tail app logs
docker compose logs -f app

# Open a shell inside the running container
docker compose exec app bash

# Run tests without Docker
pip install -e . && pytest tests/unit/ -v
```

---

## API Keys

| Key | Where to get it | Free tier |
|-----|----------------|-----------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Yes — generous free tier |
| `ALPHA_VANTAGE_KEY` | [alphavantage.co](https://www.alphavantage.co/support/#api-key) | Yes — 25 requests/day |

> With the default 30-minute cache TTL, the Alpha Vantage free tier is sufficient for development and light usage.
