import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, File, UploadFile, HTTPException
from services.stt.service import STTService
import os
import tempfile

app = FastAPI(title="STT Service")
stt_service = STTService()

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe uploaded audio file"""
    if not file.content_type or not any(fmt in file.content_type for fmt in ["audio", "video"]):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        result = stt_service.transcribe(tmp_path)
        return result
    finally:
        os.unlink(tmp_path)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

