import logging
from typing import List, Dict, Optional
from fastapi import APIRouter
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
async def chat_endpoint(request: ChatRequest):
    """
    Server-Sent Events (SSE) streaming chat endpoint with dual-tier RAG and web search fallback.
    Supports search_mode: 'auto', 'web', or 'docs'.
    """
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.chat_history]
    
    return StreamingResponse(
        rag_pipeline.stream_query(request.query, history_dicts, search_mode=request.search_mode),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
