import httpx
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from config import settings
from core.llm import llm_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["Models"])

class ModelSelectRequest(BaseModel):
    model: str

@router.get("")
async def list_models() -> Dict[str, Any]:
    """
    Returns available models:
    - In local mode (Ollama): fetches locally installed models from Ollama runtime.
    - In hosted/API mode: returns models configured in LLM_MODELS / LLM_MODEL.
    """
    provider = settings.LLM_PROVIDER
    models: List[Dict[str, Any]] = []

    if provider == "ollama":
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
            logger.warning(f"Could not fetch models from local Ollama: {e}")
    else:
        # Hosted API mode
        available = settings.available_llm_models
        for m in available:
            models.append({
                "name": m,
                "size_gb": 0,
                "parameter_size": "Hosted API",
                "quantization": "Cloud",
                "family": provider.capitalize()
            })

    return {
        "provider": provider,
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
    llm_client._model_name = req.model
    logger.info(f"Switched active LLM model to: {req.model} (Provider: {settings.LLM_PROVIDER})")
    return {
        "status": "success",
        "provider": settings.LLM_PROVIDER,
        "active_model": settings.LLM_MODEL
    }
