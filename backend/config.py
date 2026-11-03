import os
from typing import Optional, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    RATE_LIMIT_PER_MIN: int = int(os.getenv("RATE_LIMIT_PER_MIN", "0"))  # 0 = disabled

    # Provider Architecture
    # LLM_PROVIDER: "ollama" | "gemini" | "openai" | "anthropic"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama").lower()
    # EMBEDDING_PROVIDER: "ollama" | "gemini" | "openai"
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
    # VECTOR_BACKEND: "chroma" | "pinecone"
    VECTOR_BACKEND: str = os.getenv("VECTOR_BACKEND", "chroma").lower()
    # STT_ENABLED: Enable or disable voice speech-to-text
    STT_ENABLED: bool = os.getenv("STT_ENABLED", "true").lower() in ("true", "1", "yes")

    # Models configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen2.5-coder:7b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
    LLM_MODELS: str = os.getenv("LLM_MODELS", "")  # Comma-separated list for UI dropdown in API mode

    # Ollama settings (applies only when LLM_PROVIDER="ollama" or EMBEDDING_PROVIDER="ollama")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_NUM_CTX: int = int(os.getenv("OLLAMA_NUM_CTX", "4096"))

    # Provider API Keys & Base URLs (never logged, loaded from env)
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    LLM_BASE_URL: Optional[str] = os.getenv("LLM_BASE_URL")  # Generic OpenAI-compatible base URL (DeepSeek, Groq, OpenRouter)

    # Local ChromaDB Vector Store
    _backend_dir = os.path.dirname(os.path.abspath(__file__))
    _default_chroma = os.path.join(_backend_dir, "chroma_db")
    CHROMA_PERSIST_DIR: str = os.getenv(
        "CHROMA_PERSIST_DIR",
        _default_chroma if os.path.exists(_default_chroma) else "./chroma_db"
    )
    COLLECTION_NAME: str = "rag_collection"

    # Cloud Pinecone Vector Store
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "attention-paper")

    # RAG parameters
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    SIMILARITY_K: int = 4
    SIMILARITY_SCORE_THRESHOLD: float = 0.35

    # Web search
    MAX_SEARCH_RESULTS: int = 4

    # Voice settings
    VOICE_TTS_VOICE: str = os.getenv("VOICE_TTS_VOICE", "en-US-GuyNeural")

    @property
    def is_hosted(self) -> bool:
        return self.LLM_PROVIDER != "ollama"

    @property
    def parsed_cors_origins(self) -> List[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def available_llm_models(self) -> List[str]:
        if self.LLM_MODELS:
            return [m.strip() for m in self.LLM_MODELS.split(",") if m.strip()]
        return [self.LLM_MODEL]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
