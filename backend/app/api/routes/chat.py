from fastapi import APIRouter, HTTPException

from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.rag import run_rag_query

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        answer, sources = await run_rag_query(request.message)
        return ChatResponse(answer=answer, sources=sources)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
