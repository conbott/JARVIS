import os
import re
import json
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx
from config import settings

logger = logging.getLogger(__name__)

class ThinkTagFilter:
    """
    Stateful streaming filter that strips reasoning blocks (<think>...</think>)
    emitted by reasoning models (e.g. DeepSeek, QwQ) before tokens reach the user.
    """
    def __init__(self):
        self.in_think = False
        self.buffer = ""

    def process(self, chunk: str) -> List[str]:
        if not chunk:
            return []
        self.buffer += chunk
        output: List[str] = []

        while self.buffer:
            if not self.in_think:
                lower_buf = self.buffer.lower()
                idx = lower_buf.find("<think>")
                if idx != -1:
                    if idx > 0:
                        output.append(self.buffer[:idx])
                    self.buffer = self.buffer[idx + len("<think>"):]
                    self.in_think = True
                else:
                    matched_prefix = False
                    for p_len in range(min(len(self.buffer), 6), 0, -1):
                        prefix = self.buffer[-p_len:].lower()
                        if "<think>".startswith(prefix):
                            safe_part = self.buffer[:-p_len]
                            if safe_part:
                                output.append(safe_part)
                            self.buffer = self.buffer[-p_len:]
                            matched_prefix = True
                            break
                    if not matched_prefix:
                        output.append(self.buffer)
                        self.buffer = ""
                    break
            else:
                lower_buf = self.buffer.lower()
                idx = lower_buf.find("</think>")
                if idx != -1:
                    self.buffer = self.buffer[idx + len("</think>"):]
                    self.in_think = False
                else:
                    matched_prefix = False
                    for p_len in range(min(len(self.buffer), 7), 0, -1):
                        prefix = self.buffer[-p_len:].lower()
                        if "</think>".startswith(prefix):
                            self.buffer = self.buffer[-p_len:]
                            matched_prefix = True
                            break
                    if not matched_prefix:
                        self.buffer = ""
                    break
        return output

    def flush(self) -> List[str]:
        output = []
        if not self.in_think and self.buffer:
            output.append(self.buffer)
        self.buffer = ""
        return output

class UnifiedLLMClient:
    """
    Unified LLM Client providing a consistent streaming interface across:
    - local: "ollama" (with num_ctx)
    - hosted/API: "gemini", "openai" (and OpenAI-compatible like DeepSeek/Groq), "anthropic"
    """
    def __init__(self):
        self._provider = settings.LLM_PROVIDER
        self._model_name = settings.LLM_MODEL

    @property
    def provider(self) -> str:
        return settings.LLM_PROVIDER

    @property
    def model_name(self) -> str:
        return settings.LLM_MODEL

    def _get_langchain_chat_model(self):
        provider = self.provider
        model_name = self.model_name

        if provider == "gemini":
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is not configured in environment. Please add it to your .env file.")
            from langchain_google_genai import ChatGoogleGenerativeAI
            try:
                return ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=settings.GOOGLE_API_KEY,
                    temperature=0.2,
                    streaming=True,
                )
            except Exception as e:
                raise ValueError(f"Failed to initialize Gemini model '{model_name}': {e}")

        elif provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not configured in environment. Please add it to your .env file.")
            from langchain_openai import ChatOpenAI
            kwargs = {
                "model": model_name,
                "api_key": settings.OPENAI_API_KEY,
                "temperature": 0.2,
                "streaming": True,
            }
            if settings.LLM_BASE_URL:
                kwargs["base_url"] = settings.LLM_BASE_URL.rstrip("/")
            return ChatOpenAI(**kwargs)

        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is not configured in environment. Please add it to your .env file.")
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=model_name,
                api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.2,
                streaming=True,
            )

        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                base_url=settings.OLLAMA_BASE_URL.rstrip("/"),
                model=model_name,
                temperature=0.2,
                num_ctx=settings.OLLAMA_NUM_CTX,
            )
        else:
            raise ValueError(f"Unknown LLM provider '{provider}'. Supported: ollama, gemini, openai, anthropic")

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        provider = self.provider
        think_filter = ThinkTagFilter()

        # Provider: Ollama (Native HTTP streaming endpoint with num_ctx)
        if provider == "ollama":
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
                    "num_ctx": settings.OLLAMA_NUM_CTX,
                }
            }

            url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
            async with httpx.AsyncClient(timeout=120.0) as client:
                try:
                    async with client.stream("POST", url, json=request_data) as response:
                        if response.status_code != 200:
                            error_text = (await response.aread()).decode("utf-8", errors="ignore")
                            logger.error(f"Ollama chat error status {response.status_code}: {error_text}")
                            if response.status_code == 404 or "not found" in error_text.lower():
                                yield (
                                    f"⚠️ **Model '{self.model_name}' Not Found:** It looks like this model has not been downloaded yet.\n\n"
                                    f"Please open your terminal and run:\n"
                                    f"```bash\nollama pull {self.model_name}\n```\n"
                                    f"*(Or open the **System Panel** in the top right to select an already installed model)*"
                                )
                            else:
                                yield f"Error communicating with local LLM (HTTP {response.status_code})"
                            return

                        async for line in response.aiter_lines():
                            if not line.strip():
                                continue
                            try:
                                data = json.loads(line)
                                raw_token = data.get("message", {}).get("content", "")
                                if raw_token:
                                    for clean_tok in think_filter.process(raw_token):
                                        yield clean_tok
                                if data.get("done", False):
                                    break
                            except Exception as parse_err:
                                logger.debug(f"Line parse error: {parse_err}")
                except Exception as e:
                    err_str = str(e).lower()
                    if "429" in err_str or "rate" in err_str:
                        yield "\n\n⚠️ **Rate Limit Exceeded:** Local service request limit reached. Please wait a moment."
                    else:
                        logger.error(f"Error streaming from Ollama: {e}")
                        yield f"\n[LLM Connection Error: Ensure Ollama is running at {settings.OLLAMA_BASE_URL}]"
            for remaining in think_filter.flush():
                yield remaining
            return

        # Hosted Providers: Gemini, OpenAI / DeepSeek / Groq, Anthropic via LangChain
        try:
            lc_model = self._get_langchain_chat_model()
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

            lc_messages: List[BaseMessage] = []
            if system_prompt:
                lc_messages.append(SystemMessage(content=system_prompt))

            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))
                else:
                    lc_messages.append(HumanMessage(content=content))

            async for chunk in lc_model.astream(lc_messages):
                raw_chunk = ""
                if hasattr(chunk, "content"):
                    if isinstance(chunk.content, str):
                        raw_chunk = chunk.content
                    elif isinstance(chunk.content, list):
                        # Some models return list of content parts
                        parts = []
                        for part in chunk.content:
                            if isinstance(part, str):
                                parts.append(part)
                            elif isinstance(part, dict) and "text" in part:
                                parts.append(part["text"])
                        raw_chunk = "".join(parts)
                if raw_chunk:
                    for clean_tok in think_filter.process(raw_chunk):
                        yield clean_tok

            for remaining in think_filter.flush():
                yield remaining

        except Exception as e:
            err_msg = str(e)
            err_lower = err_msg.lower()
            logger.error(f"Error calling hosted LLM ({provider} / {self.model_name}): {err_msg}")

            if "429" in err_lower or "resourceexhausted" in err_lower or "rate limit" in err_lower or "quota" in err_lower:
                yield (
                    "\n\n⚠️ **Rate Limit / Quota Exceeded (HTTP 429):** The provider reported that rate limits or quotas "
                    f"have been exceeded for '{self.model_name}'. Please wait a moment or check your billing plan."
                )
            elif "401" in err_lower or "unauthorized" in err_lower or "invalid api key" in err_lower or "api_key" in err_lower:
                yield (
                    f"\n\n⚠️ **Authentication Error:** The API key for provider '{provider}' is missing or invalid. "
                    "Please verify your credentials in your environment configuration (.env)."
                )
            elif "not found" in err_lower or "invalid_argument" in err_lower or "model" in err_lower:
                yield (
                    f"\n\n⚠️ **Model Error:** The model name '{self.model_name}' was rejected or not found by {provider}. "
                    f"Please verify LLM_MODEL in your .env or choose an active model. (Details: {err_msg})"
                )
            else:
                yield f"\n\n⚠️ **AI Provider Error ({provider}):** {err_msg}"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        full_text = []
        async for token in self.stream_chat(messages, system_prompt):
            full_text.append(token)
        return "".join(full_text)

llm_client = UnifiedLLMClient()
