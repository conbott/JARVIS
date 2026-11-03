import time
import logging
from collections import defaultdict
from typing import Dict, List
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import settings
from routers import chat, documents, voice, models
from core.vectorstore import vector_store_manager
from core.hardware import get_system_hardware

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("rag_chatbot")

app = FastAPI(
    title="RAG & Voice Assistant API",
    description="Full-Stack Local & Hosted RAG + Voice Assistant with Web Search Fallback and Multi-Provider Support",
    version="2.0.0"
)

# In-Memory Per-IP Rate Limiter Middleware
class InMemoryRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.ip_records: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        limit = settings.RATE_LIMIT_PER_MIN
        if limit > 0 and request.method != "OPTIONS":
            forwarded = request.headers.get("x-forwarded-for")
            client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
            now = time.time()
            cutoff = now - 60.0
            
            # Prune records older than 1 minute
            history = [t for t in self.ip_records[client_ip] if t > cutoff]
            if len(history) >= limit:
                logger.warning(f"Rate limit exceeded for client IP: {client_ip} ({len(history)} req/min)")
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit of {limit} requests per minute exceeded. Please wait a moment."}
                )
            history.append(now)
            self.ip_records[client_ip] = history

        return await call_next(request)

app.add_middleware(InMemoryRateLimiter)

# CORS setup for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(voice.router)
app.include_router(models.router)

@app.get("/api/health")
async def health_check(request: Request):
    """
    Verifies overall system health, active provider, model configuration,
    vector backend status, and STT enablement.
    Sensitive API keys are strictly excluded.
    """
    provider = settings.LLM_PROVIDER
    ollama_online = False

    if provider == "ollama":
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(settings.OLLAMA_BASE_URL)
                if resp.status_code == 200:
                    ollama_online = True
        except Exception:
            ollama_online = False
    else:
        # Hosted mode (Gemini, OpenAI, Anthropic)
        ollama_online = True

    session_id = request.headers.get("x-session-id")
    stats = vector_store_manager.get_stats(session_id=session_id)
    hardware_info = get_system_hardware()

    return {
        "status": "healthy",
        "provider": settings.LLM_PROVIDER,
        "model": settings.LLM_MODEL,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "vector_backend": settings.VECTOR_BACKEND,
        "stt_enabled": settings.STT_ENABLED,
        "hosted": settings.is_hosted,
        "ollama_online": ollama_online,
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "device_info": hardware_info,
        "vector_store": {
            "type": "Pinecone" if settings.VECTOR_BACKEND == "pinecone" else "ChromaDB",
            "total_chunks": stats.get("total_chunks", 0),
            "documents": stats.get("documents", []),
            "collection": stats.get("collection", "")
        },
        "cloud_sync_target": {
            "type": "Pinecone",
            "index": settings.PINECONE_INDEX_NAME,
            "configured": bool(settings.PINECONE_API_KEY)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
