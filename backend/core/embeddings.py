import logging
from typing import Optional
from langchain_ollama import OllamaEmbeddings
from config import settings

logger = logging.getLogger(__name__)

class EmbeddingEngine:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model_name = settings.EMBEDDING_MODEL
        self._embeddings: Optional[OllamaEmbeddings] = None

    @property
    def client(self) -> OllamaEmbeddings:
        if self._embeddings is None:
            logger.info(f"Initializing Ollama embeddings with model: {self.model_name} at {self.base_url}")
            self._embeddings = OllamaEmbeddings(
                base_url=self.base_url,
                model=self.model_name,
            )
        return self._embeddings

embedding_engine = EmbeddingEngine()
