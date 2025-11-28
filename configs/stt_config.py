from pydantic import BaseModel, ConfigDict
from typing import List
import os

class STTConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_name: str = "medium"
    device: str = os.getenv("WHISPER_DEVICE", "cuda")
    audio_formats: List[str] = ["wav", "mp3", "m4a", "flac", "ogg"]
    chunk_size: int = 30
    language: str = None

config = STTConfig()

