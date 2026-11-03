import re
import logging
from typing import Optional, Any
from config import settings

logger = logging.getLogger(__name__)

def get_safe_collection_name(provider: str, model_name: str, base_prefix: str = "rag") -> str:
    """
    Constructs a valid ChromaDB collection name including the provider and embedding model,
    preventing mixing vectors of differing dimensions.
    For default local Ollama (qwen3-embedding:0.6b), keeps 'rag_collection' for seamless backward compatibility.
    """
    if provider == "ollama" and ("qwen3" in model_name or model_name == "qwen3-embedding:0.6b"):
        return settings.COLLECTION_NAME or "rag_collection"

    clean_provider = re.sub(r'[^a-zA-Z0-9]', '_', provider).strip('_').lower()
    clean_model = re.sub(r'[^a-zA-Z0-9]', '_', model_name).strip('_').lower()
    candidate = f"{base_prefix}_{clean_provider}_{clean_model}"
    # Chroma collection names must be 3-63 characters, start and end with alphanumeric
    candidate = re.sub(r'_+', '_', candidate)
    candidate = candidate[:60].strip('_')
    if len(candidate) < 3:
        candidate = "rag_default_store"
    return candidate

class EmbeddingEngine:
    """
    Multi-provider embedding engine supporting:
    - "ollama": local dense vectors via OllamaEmbeddings
    - "gemini": GoogleGenerativeAIEmbeddings (using GOOGLE_API_KEY)
    - "openai": OpenAIEmbeddings (using OPENAI_API_KEY and optional LLM_BASE_URL)
    """
    def __init__(self):
        self._provider = settings.EMBEDDING_PROVIDER
        self._model_name = settings.EMBEDDING_MODEL
        self._cached_client: Optional[Any] = None
        self._cached_key: Optional[str] = None

    @property
    def provider(self) -> str:
        return settings.EMBEDDING_PROVIDER

    @property
    def model_name(self) -> str:
        return settings.EMBEDDING_MODEL

    @property
    def collection_name(self) -> str:
        return get_safe_collection_name(self.provider, self.model_name)

    @property
    def client(self) -> Any:
        current_key = f"{self.provider}:{self.model_name}:{settings.GOOGLE_API_KEY}:{settings.OPENAI_API_KEY}"
        if self._cached_client is not None and self._cached_key == current_key:
            return self._cached_client

        provider = self.provider
        model_name = self.model_name
        logger.info(f"Initializing embeddings provider '{provider}' with model '{model_name}'")

        if provider == "gemini":
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required for Gemini embeddings. Set GOOGLE_API_KEY in .env.")
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            try:
                emb_model = model_name if ("models/" in model_name or "text-embedding" in model_name) else "models/text-embedding-004"
                self._cached_client = GoogleGenerativeAIEmbeddings(
                    model=emb_model,
                    google_api_key=settings.GOOGLE_API_KEY,
                )
            except Exception as e:
                raise ValueError(f"Failed to initialize Gemini embeddings '{model_name}': {e}")

        elif provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings. Set OPENAI_API_KEY in .env.")
            from langchain_openai import OpenAIEmbeddings
            kwargs = {
                "model": model_name or "text-embedding-3-small",
                "api_key": settings.OPENAI_API_KEY,
            }
            if settings.LLM_BASE_URL:
                kwargs["base_url"] = settings.LLM_BASE_URL.rstrip("/")
            try:
                self._cached_client = OpenAIEmbeddings(**kwargs)
            except Exception as e:
                raise ValueError(f"Failed to initialize OpenAI embeddings '{model_name}': {e}")

        elif provider == "ollama":
            from langchain_ollama import OllamaEmbeddings
            self._cached_client = OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL.rstrip("/"),
                model=model_name or "qwen3-embedding:0.6b",
            )
        else:
            raise ValueError(f"Unsupported EMBEDDING_PROVIDER '{provider}'. Options: ollama, gemini, openai")

        self._cached_key = current_key
        return self._cached_client

embedding_engine = EmbeddingEngine()
