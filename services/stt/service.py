import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import whisper
import torch
from typing import Optional
from configs.stt_config import config

class STTService:
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.load_model()
    
    def load_model(self):
        """Load Whisper model"""
        self.model = whisper.load_model(config.model_name, device=self.device)
    
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> dict:
        """Transcribe audio file to text"""
        result = self.model.transcribe(
            audio_path,
            language=language or config.language
        )
        return {
            "text": result["text"],
            "language": result.get("language", "unknown")
        }

