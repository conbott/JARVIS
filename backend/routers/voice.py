import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Response, UploadFile, File
from pydantic import BaseModel
from config import settings
from core.voice import voice_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["Voice"])

class SynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = None

AVAILABLE_VOICES: List[Dict[str, str]] = [
    {"id": "en-US-GuyNeural", "name": "Guy (US Male - Deep & Calm)", "gender": "male", "accent": "US"},
    {"id": "en-US-ChristopherNeural", "name": "Christopher (US Male - Natural)", "gender": "male", "accent": "US"},
    {"id": "en-US-JennyNeural", "name": "Jenny (US Female - Clear & Friendly)", "gender": "female", "accent": "US"},
    {"id": "en-US-AriaNeural", "name": "Aria (US Female - Expressive)", "gender": "female", "accent": "US"},
    {"id": "en-GB-RyanNeural", "name": "Ryan (UK Male - British)", "gender": "male", "accent": "UK"},
    {"id": "en-GB-SoniaNeural", "name": "Sonia (UK Female - British)", "gender": "female", "accent": "UK"},
    {"id": "en-IN-PrabhatNeural", "name": "Prabhat (IN Male - Indian)", "gender": "male", "accent": "IN"},
    {"id": "en-IN-NeerjaNeural", "name": "Neerja (IN Female - Indian)", "gender": "female", "accent": "IN"},
    {"id": "en-AU-NatashaNeural", "name": "Natasha (AU Female - Australian)", "gender": "female", "accent": "AU"},
]

@router.get("/voices")
async def get_available_voices():
    """
    Returns the curated list of high-fidelity neural voices.
    """
    return {
        "voices": AVAILABLE_VOICES,
        "default": "en-US-GuyNeural"
    }

@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """
    Synthesizes neural speech (MP3) from text using edge-tts on CPU with 0 MB GPU VRAM.
    Allows specifying custom voice from the available voices list.
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

@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribes audio captured via browser MediaRecorder using faster-whisper.
    Ensures 100% browser compatibility (Opera GX, Brave, Chrome, Firefox, Safari).
    """
    if not settings.STT_ENABLED:
        raise HTTPException(status_code=403, detail="Speech-to-text is disabled by configuration (STT_ENABLED=false).")
    try:
        content = await audio.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio file received.")

        # Determine file suffix
        suffix = ".webm"
        if audio.filename and "." in audio.filename:
            suffix = "." + audio.filename.rsplit(".", 1)[1]

        from core.stt import get_stt_engine
        engine = get_stt_engine()
        transcription = engine.transcribe_audio_bytes(content, suffix=suffix)
        return {
            "status": "success",
            "text": transcription
        }
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
