from fastapi import APIRouter, HTTPException

from app.services.data_ingestion import fetch_and_ingest_ticker_data

router = APIRouter(tags=["ops"])


@router.post("/ingest", status_code=200)
async def trigger_ingestion() -> dict[str, object]:
    try:
        count = await fetch_and_ingest_ticker_data()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "ok", "documents_ingested": count}
