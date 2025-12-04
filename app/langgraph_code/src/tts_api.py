import io
import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://tts_service:8005")  # NOSONAR - Internal Docker service communication

logger = logging.getLogger("langgraph_nodes")

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "am_onyx"
    speed: Optional[float] = 1.0
    
@router.post("/tts")
async def synthesize_speech(request: TTSRequest):
    """Synthesize speech from text using the TTS service."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(f"{TTS_SERVICE_URL}/synthesize", json=request.model_dump())
            response.raise_for_status()
            media_type = response.headers.get("content-type", "audio/wav")
            logger.info("Synthesized speech with media type: %s", media_type)
            return StreamingResponse(io.BytesIO(response.content), media_type=media_type)
        except httpx.HTTPStatusError as e:
            logger.error("TTS service returned an error: %s - %s", e.response.status_code, e.response.text)
            return {"error": f"TTS service returned an error: {e.response.status_code} - {e.response.text}"}