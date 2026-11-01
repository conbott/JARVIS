import os
import io
import logging
import asyncio
import edge_tts
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

class VoiceEngine:
    def __init__(self):
        self.default_voice = settings.VOICE_TTS_VOICE

    async def text_to_speech(self, text: str, voice: Optional[str] = None) -> bytes:
        """
        Synthesizes human-like neural speech using edge-tts asynchronously.
        Runs entirely on CPU/network with 0 MB GPU VRAM usage.
        Returns MP3 audio bytes.
        """
        selected_voice = voice or self.default_voice
        # Clean markdown or special characters before speaking
        cleaned_text = self._clean_text_for_speech(text)
        
        if not cleaned_text:
            cleaned_text = "I have processed your request."

        try:
            communicate = edge_tts.Communicate(cleaned_text, selected_voice)
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            audio_buffer.seek(0)
            return audio_buffer.read()
        except Exception as e:
            logger.error(f"Text-to-speech synthesis error: {e}")
            raise e

    def _clean_text_for_speech(self, text: str) -> str:
        """
        Removes markdown links, code blocks, and symbols for natural reading.
        """
        import re
        # Remove fenced code blocks
        clean = re.sub(r'```[\s\S]*?```', ' [Code block omitted] ', text)
        # Remove inline code
        clean = re.sub(r'`[^`]*`', '', clean)
        # Replace markdown links [text](url) with just text
        clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean)
        # Remove markdown headers and emphasis
        clean = re.sub(r'[#*_~>|]', '', clean)
        # Condense whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        # Truncate if excessively long for speech (read first ~1500 chars)
        if len(clean) > 1500:
            clean = clean[:1500] + "... and more."
        return clean

voice_engine = VoiceEngine()
