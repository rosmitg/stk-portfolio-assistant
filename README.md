# stk-portfolio-assistant

A conversational portfolio assistant — ask questions about your holdings, get live prices and news, and let an LLM-backed agent figure out which tool to use.

**Live demo:** https://stk-frontend-512165788990.australia-southeast1.run.app
_(requires sign-up via Supabase auth — email/password, no OAuth)_

---

## What it does

You add your stock holdings (via Alpaca paper trading sync, CSV upload, or manual entry), then chat with an agent that can look up live prices, pull recent news, run portfolio calculations, and search ingested research documents. The agent uses LangChain's tool-calling loop with Claude as the backbone, so it decides which tool to hit based on what you actually asked — you don't have to tell it.

---

## Features

- **Chat interface** — ask about individual tickers, your overall portfolio, or general market questions
- **Agent tool dispatch** — live price lookup (Alpaca → yfinance fallback), news search via NewsAPI, portfolio maths (P&L, allocation, sector breakdown), RAG search over ingested documents
- **Portfolio ingestion** — sync from Alpaca paper trading account, upload a CSV, or add positions manually
- **Live prices** — Alpaca's market data API with a yfinance fallback
- **Charts** — allocation pie and P&L line charts via Recharts
- **Auth** — Supabase email/password with JWT verification on the backend

---

## Tech stack

| Layer | What |
|---|---|
| Frontend | React 18, TypeScript, Tailwind CSS, Recharts, Vite |
| Backend | FastAPI, Python 3.11, SQLAlchemy (async), asyncpg |
| Agent / LLM | LangChain, Claude API (claude-sonnet-4-5) |
| RAG | ChromaDB, Voyage AI embeddings |
| Observability | LangSmith (tracing + evals) |
| Auth | Supabase (email/password, JWKS JWT verification) |
| Data | Alpaca Markets API, yfinance, NewsAPI |
| Infra | GCP Cloud Run, Cloud SQL (Postgres), Artifact Registry, Secret Manager, Cloud Build |

---

## Architecture

```
User
 │
 ▼
React (Vite SPA)
 │  REST + streaming
 ▼
FastAPI
 │
 ▼
LangChain Agent (tool-calling loop)
 │
 ├── ticker_info    → Alpaca / yfinance
 ├── news_search    → NewsAPI
 ├── portfolio_calc → Cloud SQL (user's holdings)
 └── rag_search     → ChromaDB (Voyage AI embeddings)
 │
 ▼
Claude (claude-sonnet-4-5)
```

The agent runs a standard ReAct loop — Claude decides which tools to call, the executor runs them, results go back into context, and Claude produces a final answer. Streaming is handled via FastAPI `StreamingResponse`, so the frontend gets tokens as they arrive.

---

## Evaluation

Evals run via LangSmith using a 10-question set covering price lookups, portfolio questions, and general market queries. Current results:

- **Relevance score: ~0.81** (LLM-as-judge on a 0–1 scale)
- **17 passing tests** across agent tools and API routes

The main failure modes are the agent over-fetching tools when a simpler answer would do, and the RAG search returning low-signal chunks when the ingested corpus is sparse.

---

## Running locally

### Prerequisites

- Python 3.11+
- Node 20+
- Docker (for Postgres) or a local Postgres instance

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in: ANTHROPIC_API_KEY, VOYAGE_API_KEY, NEWS_API_KEY,
#          ALPACA_API_KEY, ALPACA_SECRET_KEY, DATABASE_URL,
#          SUPABASE_URL, SUPABASE_SERVICE_KEY

uvicorn app.main:app --reload --port 8000
```

Postgres via Docker if you don't have one running:

```bash
docker run -d \
  --name stk-postgres \
  -e POSTGRES_DB=stk_portfolio \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15
```

### Frontend

```bash
cd frontend-react
cp .env.example .env
# VITE_BACKEND_URL=http://localhost:8000
# VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY from your Supabase project dashboard

npm install
npm run dev
```

### Tests

```bash
cd backend && pytest tests/ -v
```

---

## Project structure

```
stk-portfolio-assistant/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # chat, portfolio, ingest, evaluate endpoints
│   │   ├── core/              # config, Supabase JWT auth
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── services/
│   │       ├── agent.py       # LangChain agent + tool definitions
│   │       ├── alpaca_service.py
│   │       ├── database.py
│   │       ├── evaluator.py   # LangSmith eval runner
│   │       ├── rag.py         # ChromaDB query
│   │       └── vector_store.py
│   ├── prompts/               # YAML system prompts
│   └── tests/
├── frontend-react/
│   └── src/
│       ├── api/               # Axios client
│       ├── components/        # Auth, Chat, Holdings, Charts, Onboarding
│       ├── hooks/             # useAuth
│       └── lib/               # Supabase client
├── infra/
│   └── gcp/
│       ├── deploy.sh          # build → push → Cloud Run deploy
│       ├── cloudbuild.yaml
│       ├── setup_database.sh
│       └── setup_secrets.sh
└── docker-compose.yml
```

---

## What's next

- **Risk analysis** — portfolio beta, volatility, correlation heatmap across holdings
- **Earnings calendar** — surface upcoming earnings dates for held tickers and feed them into agent context
- **Real broker integration** — currently paper trading only via Alpaca; a read-only brokerage API (IBKR, Schwab) would make this actually useful day-to-day
- **Better RAG** — the current corpus is thin; proper document ingestion (10-Ks, analyst reports) would improve the research tool substantially
- **Streaming tool results** — individual tool calls don't surface incrementally in the UI yet, only the final answer streams
