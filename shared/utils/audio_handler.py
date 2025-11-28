import base64
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import hashlib

ALLOWED_FORMATS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}

def validate_audio_format(filename: str) -> bool:
    """Validate audio file format"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_FORMATS

def save_binary_audio(data: bytes, suffix: str = ".wav") -> str:
    """Save binary audio data to temporary file"""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(data)
    tmp_path = tmp.name
    tmp.close()
    return tmp_path

def decode_base64_audio(base64_data: str) -> bytes:
    """Decode base64 audio data"""
    if "," in base64_data:
        base64_data = base64_data.split(",")[1]
    return base64.b64decode(base64_data)

def get_audio_hash(data: bytes) -> str:
    """Generate hash for audio caching"""
    return hashlib.md5(data).hexdigest()

