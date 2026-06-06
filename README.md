# STK Portfolio Assistant

An AI-powered stock portfolio assistant that answers natural language questions about your holdings using real-time market data, financial news, and a vector-search knowledge base — backed by Claude and LangChain.

**Live demo:** _https://your-app-url.run.app_ _(placeholder — update after deploy)_

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit, Plotly |
| Backend | FastAPI, Uvicorn |
| AI / Agent | LangChain, Claude (Anthropic) |
| Vector store | ChromaDB (local), Pinecone (production) |
| Market data | yfinance |
| News | NewsAPI |
| Observability | LangSmith |
| Database | PostgreSQL (SQLAlchemy 2.0) |
| Containers | Docker, Docker Compose |
| Cloud | GCP Cloud Run, Artifact Registry, Cloud Build |
| Python | 3.11 |

---

## Project Structure

```
stk-portfolio-assistant/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API route handlers
│   │   ├── core/config.py   # Pydantic settings
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic & agent
│   │   └── main.py          # FastAPI app entry point
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py               # Streamlit entry point
│   ├── Dockerfile
│   └── requirements.txt
├── infra/
│   ├── docker/              # Production compose
│   └── gcp/                 # Cloud Build config
├── docs/
│   ├── architecture.md
│   └── adr/                 # Architecture Decision Records
├── docker-compose.yml
├── Makefile
├── .env.example
└── .pre-commit-config.yaml
```

---

## Local Setup

### Prerequisites

- Python 3.11
- Docker & Docker Compose
- A `.env` file — copy from `.env.example` and fill in your keys

```bash
cp .env.example .env
```

### Option A — Docker Compose (recommended)

```bash
docker compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:8501
- API docs: http://localhost:8000/docs

### Option B — Local Python

```bash
make install        # install backend + frontend deps, enable pre-commit hooks
make run-backend    # terminal 1
make run-frontend   # terminal 2
```

---

## Development Commands

```bash
make help           # list all commands
make test           # run pytest
make lint           # ruff check
make format         # ruff format
make type-check     # mypy
make pre-commit     # run all hooks against every file
make clean          # remove caches and build artefacts
```

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key |
| `LANGCHAIN_API_KEY` | LangSmith API key |
| `LANGCHAIN_PROJECT` | LangSmith project name |
| `NEWS_API_KEY` | NewsAPI key |
| `PINECONE_API_KEY` | Pinecone API key |
| `PINECONE_ENVIRONMENT` | Pinecone environment (e.g. `us-east-1-aws`) |
| `DATABASE_URL` | PostgreSQL connection string |
| `APP_ENV` | `development` or `production` |
| `DEBUG` | `true` / `false` |

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system diagram, component breakdown, and GCP infrastructure overview.

---

## Deployment (GCP Cloud Run)

```bash
# Build and push images
gcloud builds submit --config infra/gcp/cloudbuild.yaml

# Or trigger automatically on push to main via Cloud Build trigger
git push origin main
```

---

## Contributing

1. Fork the repo and create a feature branch.
2. Run `make pre-commit` before committing.
3. Open a PR — use the template in `.github/PULL_REQUEST_TEMPLATE.md`.

---

## License

MIT
