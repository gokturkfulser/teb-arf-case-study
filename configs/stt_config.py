from pydantic import BaseModel
from typing import List

class STTConfig(BaseModel):
    model_name: str = "medium"
    device: str = "cuda"
    audio_formats: List[str] = ["wav", "mp3", "m4a", "flac", "ogg"]
    chunk_size: int = 30
    language: str = None

config = STTConfig()

