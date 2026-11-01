import logging
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    title="Local RAG & Voice Assistant API",
    description="Full-Stack Local RAG + Voice Assistant with Web Search Fallback and Pinecone Cloud Sync",
    version="1.1.0"
)

# CORS setup for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
async def health_check():
    """
    Verifies overall system health, Ollama status, dynamic hardware info, and ChromaDB vector count.
    """
    ollama_online = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(settings.OLLAMA_BASE_URL)
            if resp.status_code == 200:
                ollama_online = True
    except Exception:
        ollama_online = False

    stats = vector_store_manager.get_stats()
    hardware_info = get_system_hardware()

    return {
        "status": "healthy",
        "ollama_online": ollama_online,
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "device_info": hardware_info,
        "vector_store": {
            "type": "ChromaDB",
            "total_chunks": stats.get("total_chunks", 0),
            "documents": stats.get("documents", [])
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
