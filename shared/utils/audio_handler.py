import base64
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import hashlib

ALLOWED_FORMATS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}

def validate_audio_format(filename: str) -> bool:
    """Validate audio file format by extension"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_FORMATS

def detect_audio_format(data: bytes) -> Optional[str]:
    """Detect audio format from magic number"""
    if len(data) < 12:
        return None
    
    # WAV: RIFF...WAVE
    if data[:4] == b"RIFF" and len(data) > 12 and data[8:12] == b"WAVE":
        return ".wav"
    
    # MP3: ID3 tag
    if data[:3] == b"ID3":
        return ".mp3"
    
    # MP3: Frame sync
    if data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return ".mp3"
    
    # M4A/MP4: ftyp or mdat at offset 4
    if len(data) > 8 and (data[4:8] == b"ftyp" or data[4:8] == b"mdat"):
        return ".m4a"
    
    # FLAC: fLaC
    if data[:4] == b"fLaC":
        return ".flac"
    
    # OGG: OggS
    if data[:4] == b"OggS":
        return ".ogg"
    
    # WEBM: \x1aE\xdf\xa3
    if data[:4] == b"\x1aE\xdf\xa3":
        return ".webm"
    
    return None

def validate_magic_number(data: bytes, expected_ext: str) -> bool:
    """Validate file magic number (file signature)"""
    detected_format = detect_audio_format(data)
    
    if not detected_format:
        return False
    
    ext = expected_ext.lower() if expected_ext else ""
    
    # Allow if detected format matches expected, or if it's a valid audio format
    if detected_format == ext:
        return True
    
    # Also allow if detected format is in allowed formats (file might have wrong extension)
    if detected_format in ALLOWED_FORMATS:
        return True
    
    return False

def validate_audio_file(data: bytes, filename: str) -> bool:
    """Validate audio file by extension and magic number"""
    if not validate_audio_format(filename):
        return False
    
    ext = Path(filename).suffix.lower()
    return validate_magic_number(data, ext)

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

