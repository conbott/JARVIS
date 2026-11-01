import base64
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from core.voice import voice_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["Voice"])

class SynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = None

@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """
    Synthesizes neural speech (MP3) from text using edge-tts on CPU with 0 MB GPU VRAM.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    try:
        audio_bytes = await voice_engine.text_to_speech(request.text, voice=request.voice)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
