import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Server configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True

    # Ollama settings (100% Local GPU runtime)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen2.5-coder:7b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
    OLLAMA_NUM_CTX: int = int(os.getenv("OLLAMA_NUM_CTX", "4096"))  # Minimum 4096 tokens for multi-turn/context RAG

    # Local ChromaDB Vector Store
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    COLLECTION_NAME: str = "rag_collection"

    # Cloud Pinecone Vector Store
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "attention-paper")

    # RAG parameters
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    SIMILARITY_K: int = 4
    SIMILARITY_SCORE_THRESHOLD: float = 0.35  # If best score < threshold, fallback to web search

    # Web search
    MAX_SEARCH_RESULTS: int = 4

    # Voice settings
    VOICE_TTS_VOICE: str = "en-US-GuyNeural"  # High fidelity Microsoft Neural voice (edge-tts)

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
