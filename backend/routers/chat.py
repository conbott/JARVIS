import logging
from typing import List, Dict, Optional
from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from core.rag_chain import rag_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    chat_history: Optional[List[ChatMessage]] = []
    search_mode: Optional[str] = Field(default="auto", description="Search mode: auto, web, or docs")

@router.post("")
async def chat_endpoint(
    chat_req: ChatRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """
    Server-Sent Events (SSE) streaming chat endpoint with multi-provider RAG and web search fallback.
    Supports search_mode: 'auto', 'web', or 'docs'.
    Accepts per-session namespace via 'X-Session-Id' header.
    """
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in chat_req.chat_history]
    
    return StreamingResponse(
        rag_pipeline.stream_query(
            chat_req.query,
            history_dicts,
            search_mode=chat_req.search_mode,
            session_id=x_session_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
