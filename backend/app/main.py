import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.services.data_ingestion import fetch_and_ingest_ticker_data
from app.services.database import init_db
from app.services.vector_store import get_document_count

# Enable LangSmith tracing before any LangChain components are initialised
if settings.langchain_tracing_v2 and settings.langchain_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception as exc:
        logger.warning("Database unavailable at startup (%s) — continuing without it", exc)
    if get_document_count() == 0:
        await fetch_and_ingest_ticker_data()
    yield


app = FastAPI(
    title="STK Portfolio Assistant",
    description="AI-powered stock portfolio analysis and Q&A API.",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["ops"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}
