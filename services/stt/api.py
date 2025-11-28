import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, File, UploadFile, HTTPException
from services.stt.service import STTService
from shared.models.stt_models import TranscribeRequest, TranscribeResponse, HealthResponse
from shared.utils.audio_handler import (
    validate_audio_format, validate_audio_file, validate_magic_number,
    detect_audio_format, save_binary_audio, decode_base64_audio, get_audio_hash
)
import os
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="STT Service")
stt_service = STTService()

@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio_file(file: UploadFile = File(...)):
    """Transcribe audio file from binary upload"""
    audio_path = None
    
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not validate_audio_format(file.filename):
            raise HTTPException(status_code=400, detail="Invalid audio format extension")
        
        content = await file.read()
        
        if not validate_audio_file(content, file.filename):
            raise HTTPException(status_code=400, detail="Invalid audio file: magic number mismatch")
        
        audio_hash = get_audio_hash(content)
        suffix = os.path.splitext(file.filename)[1] or ".wav"
        audio_path = save_binary_audio(content, suffix)
        
        result = stt_service.transcribe(audio_path, audio_hash=audio_hash)
        return TranscribeResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)

@app.post("/transcribe/json", response_model=TranscribeResponse)
async def transcribe_audio_json(request: TranscribeRequest):
    """Transcribe audio from base64 JSON"""
    audio_path = None
    
    try:
        if not request.audio_data:
            raise HTTPException(status_code=400, detail="No audio data provided")
        
        content = decode_base64_audio(request.audio_data)
        
        detected_format = detect_audio_format(content)
        if not detected_format:
            raise HTTPException(status_code=400, detail="Invalid audio file: unsupported format or corrupted file")
        
        audio_hash = get_audio_hash(content)
        audio_path = save_binary_audio(content, detected_format)
        
        result = stt_service.transcribe(audio_path, language=request.language, audio_hash=audio_hash)
        return TranscribeResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        model_loaded=stt_service.model is not None,
        device=stt_service.device,
        queue_size=len(stt_service.request_queue)
    )

@app.get("/metrics")
async def metrics():
    """Get performance metrics"""
    return stt_service.get_metrics()

@app.post("/cache/clear")
async def clear_cache():
    """Clear transcription cache"""
    stt_service.clear_cache()
    return {"status": "cache cleared"}
