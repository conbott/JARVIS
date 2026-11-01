import httpx
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["Models"])

class ModelSelectRequest(BaseModel):
    model: str

@router.get("")
async def list_models() -> Dict[str, Any]:
    """
    Returns the list of locally installed Ollama models,
    plus the currently active LLM and embedding models.
    """
    models: List[Dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("models", []):
                    models.append({
                        "name": m.get("name"),
                        "size_gb": round(m.get("size", 0) / (1024 ** 3), 2),
                        "parameter_size": m.get("details", {}).get("parameter_size", "unknown"),
                        "quantization": m.get("details", {}).get("quantization_level", "unknown"),
                        "family": m.get("details", {}).get("family", "unknown")
                    })
    except Exception as e:
        logger.warning(f"Could not fetch models from Ollama: {e}")

    return {
        "current_llm": settings.LLM_MODEL,
        "current_embedding": settings.EMBEDDING_MODEL,
        "installed_models": models
    }

@router.post("/select")
async def select_model(req: ModelSelectRequest) -> Dict[str, Any]:
    """
    Dynamically switches the active LLM model without requiring a server restart.
    """
    settings.LLM_MODEL = req.model
    logger.info(f"Switched active LLM model to: {req.model}")
    return {
        "status": "success",
        "active_model": settings.LLM_MODEL
    }
