# WiseMint — FinAdvisor

Financial AI assistant. Python 3.12, Streamlit UI, Groq (Llama-3.3-70B), ChromaDB, Docker.

## Run locally (Docker)
```
cp .env.example .env   # fill in API keys
docker compose up --build
# App: http://localhost:8501
# ChromaDB: http://localhost:8000
# MLflow: http://localhost:5000
```

## Run tests
```
pip install -e .
pytest tests/unit/
```

## Ingest knowledge base docs
```
# Place .txt files in data/knowledge_base/
python -c "from src.kb.ingest import ingest_directory; ingest_directory('data/knowledge_base')"
```

## Project layout
- `src/agent/` — ReAct orchestrator + intent classifier
- `src/kb/` — ChromaDB + BM25 hybrid retrieval
- `src/market/` — Alpha Vantage API + disk cache
- `src/tools/` — deterministic finance math
- `src/memory/` — SQLite user profiles
- `src/safety/` — input/output guardrails
- `src/ui/` — Streamlit app
- `resources/` — design docs and architecture HTML (do not move)

## Iteration protocol
Code one layer → `docker compose build` → smoke test → update HTML if needed → commit.

## Required env vars
- `GROQ_API_KEY` — Groq inference
- `ALPHA_VANTAGE_KEY` — live market data
