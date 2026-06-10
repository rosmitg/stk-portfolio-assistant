import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.auth import CurrentUser
from app.schemas.schemas import ChatRequest
from app.services.agent import stream_agent_query

router = APIRouter(tags=["chat"])

_AGENT_TIMEOUT = 90


@router.post("/chat")
async def chat(request: ChatRequest, user_id: CurrentUser) -> StreamingResponse:
    async def event_stream():
        try:
            async with asyncio.timeout(_AGENT_TIMEOUT):
                async for event in stream_agent_query(request.message, request.portfolio_holdings):
                    yield f"data: {json.dumps(event)}\n\n"
        except TimeoutError:
            yield f"data: {json.dumps({'type': 'error', 'message': 'The assistant took too long to respond. Please try a simpler question.'})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
