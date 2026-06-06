# System Architecture — STK Portfolio Assistant

## Overview

STK Portfolio Assistant is a production-grade AI application that enables users to analyse their stock portfolio through natural language queries. The system retrieves real-time market data and financial news, grounds responses in a vector-search knowledge base, and delivers answers via a Claude-powered LangChain agent.

---

## High-Level Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User (Browser)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────┐
│               Streamlit Frontend (GCP Cloud Run)            │
│  - Portfolio dashboard (Plotly charts)                      │
│  - Natural language chat interface                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST / JSON
┌──────────────────────────▼──────────────────────────────────┐
│               FastAPI Backend (GCP Cloud Run)               │
│  - /health                                                  │
│  - /api/v1/portfolio  — CRUD & analytics                   │
│  - /api/v1/chat       — LangChain agent endpoint           │
└───────┬──────────────┬──────────────────┬───────────────────┘
        │              │                  │
  ┌─────▼──────┐ ┌─────▼──────┐  ┌───────▼──────┐
  │ yfinance   │ │  NewsAPI   │  │  PostgreSQL  │
  │ (market    │ │  (news     │  │  (portfolio  │
  │  data)     │ │  feed)     │  │   records)   │
  └─────┬──────┘ └─────┬──────┘  └──────────────┘
        │              │
┌───────▼──────────────▼───────────────────────────────────────┐
│                   LangChain Agent (Claude)                    │
│  - Tool: stock_data  (yfinance wrapper)                      │
│  - Tool: news_search (NewsAPI wrapper)                       │
│  - Tool: vector_search (ChromaDB / Pinecone retriever)       │
└───────────────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────┴──────────────┐
        │                              │
 ┌──────▼──────┐               ┌───────▼──────┐
 │  ChromaDB   │               │   Pinecone   │
 │  (local /   │               │  (cloud      │
 │   Docker)   │               │   vector DB) │
 └─────────────┘               └──────────────┘
                        │
                 ┌───────▼──────┐
                 │  LangSmith   │
                 │ (tracing &   │
                 │  evals)      │
                 └──────────────┘
```

---

## Component Breakdown

### Frontend — Streamlit
- Single-page app with a portfolio summary dashboard and a chat panel.
- Communicates with the backend exclusively through the REST API.
- Visualisations built with Plotly (candlestick charts, sector allocation pie, P&L sparklines).

### Backend — FastAPI
- Async API server; all I/O-bound routes use `async def`.
- Pydantic v2 models for request/response validation and settings management.
- SQLAlchemy 2.0 (async engine) for portfolio persistence in PostgreSQL.
- Mounts the LangChain agent as a streaming endpoint so the frontend can render tokens progressively.

### AI Agent — LangChain + Claude
- `AgentExecutor` with a ReAct-style prompt backed by `claude-sonnet-4-6`.
- Three tools available at runtime:
  | Tool | Source | Purpose |
  |------|--------|---------|
  | `stock_data` | yfinance | OHLCV, fundamentals, dividends |
  | `news_search` | NewsAPI | Recent headlines for a ticker or topic |
  | `vector_search` | ChromaDB / Pinecone | Semantic search over ingested filings & reports |
- LangSmith wraps every run for latency tracking, token counting, and prompt regression testing.

### Vector Store — ChromaDB / Pinecone
- **Local (dev):** ChromaDB persisted to `chroma_db/` volume.
- **Production:** Pinecone serverless index in `us-east-1`.
- Documents ingested: SEC filings, earnings call transcripts, analyst reports.
- Embedding model: `text-embedding-3-small` (OpenAI) or `claude`-compatible embeddings.

### Observability — LangSmith
- All LangChain runs are traced automatically via `LANGCHAIN_API_KEY`.
- Custom evaluators check factual grounding and tool-call correctness.
- Dashboard at `smith.langchain.com` under project `stk-portfolio-assistant`.

---

## Infrastructure (GCP)

| Resource | Service | Notes |
|----------|---------|-------|
| Backend API | Cloud Run | Min 1 instance, 2 vCPU / 2 GB |
| Frontend | Cloud Run | Min 0 instances (cold-start OK) |
| Container registry | Artifact Registry | `us-central1-docker.pkg.dev` |
| CI/CD | Cloud Build | Triggered on push to `main` |
| Secrets | Secret Manager | API keys injected at runtime |
| Database | Cloud SQL (PostgreSQL 15) | Private IP, VPC connector |

### Deployment Flow
```
git push main
    → Cloud Build trigger
    → docker build backend + frontend
    → push to Artifact Registry
    → gcloud run deploy (zero-downtime rolling update)
```

---

## Data Flow — Chat Query

```
User types query
  → POST /api/v1/chat  {query, portfolio_id}
    → LangChain agent receives query + portfolio context
      → selects tools (stock_data, news_search, vector_search)
        → tool results appended to agent scratchpad
          → Claude synthesises final answer
            → streamed back as Server-Sent Events
              → Streamlit renders tokens in real time
```

---

## Security

- All secrets stored in GCP Secret Manager; never in source control.
- Non-root Docker user in both containers.
- CORS restricted to the frontend Cloud Run URL in production.
- Database connections use SSL; credentials injected via Secret Manager at Cloud Run deploy time.

---

## ADRs

- [001 — Use LangChain](adr/001-use-langchain.md)
- [002 — ChromaDB + Pinecone dual vector store](adr/002-use-chromadb-pinecone.md)
- [003 — Deploy on GCP](adr/003-use-gcp.md)
