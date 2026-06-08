from fastapi import APIRouter, HTTPException

from app.services.evaluator import run_evaluation

router = APIRouter(tags=["ops"])


@router.post("/evaluate", status_code=200)
async def trigger_evaluation() -> dict:
    try:
        return await run_evaluation()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
