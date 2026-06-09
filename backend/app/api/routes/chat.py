from fastapi import APIRouter, HTTPException

from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.agent import run_agent_query

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        answer, sources, updated_history = await run_agent_query(
            request.message,
            request.portfolio_holdings,
            request.conversation_history,
        )
        return ChatResponse(answer=answer, sources=sources, conversation_history=updated_history)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
