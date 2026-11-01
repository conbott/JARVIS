import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx
from langchain_ollama import ChatOllama
from config import settings

logger = logging.getLogger(__name__)

class OllamaLLMClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model_name = settings.LLM_MODEL
        self._langchain_llm: Optional[ChatOllama] = None

    @property
    def langchain_model(self) -> ChatOllama:
        if self._langchain_llm is None:
            self._langchain_llm = ChatOllama(
                base_url=self.base_url,
                model=self.model_name,
                temperature=0.2,
            )
        return self._langchain_llm

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streams response tokens directly from local Ollama GPU runner.
        Uses Ollama's native streaming endpoint for zero overhead and minimal latency.
        """
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        
        payload_messages.extend(messages)

        request_data = {
            "model": self.model_name,
            "messages": payload_messages,
            "stream": True,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
            }
        }

        url = f"{self.base_url}/api/chat"
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream("POST", url, json=request_data) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Ollama chat error status {response.status_code}: {error_text}")
                        yield f"Error communicating with local LLM (HTTP {response.status_code})"
                        return

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            import json
                            data = json.loads(line)
                            token = data.get("message", {}).get("content", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break
                        except Exception as parse_err:
                            logger.debug(f"Line parse error: {parse_err}")
            except Exception as e:
                logger.error(f"Error streaming from Ollama: {e}")
                yield f"\n[LLM Connection Error: Ensure Ollama is running at {self.base_url}]"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Non-streaming generation returning complete text.
        """
        full_text = []
        async for token in self.stream_chat(messages, system_prompt):
            full_text.append(token)
        return "".join(full_text)

llm_client = OllamaLLMClient()
