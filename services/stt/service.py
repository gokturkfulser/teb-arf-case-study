import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import whisper
import torch
import time
import logging
import warnings
from typing import Optional, Dict
from collections import deque
from threading import Lock
from configs.stt_config import config
from shared.utils.audio_handler import get_audio_hash

warnings.filterwarnings("ignore", category=FutureWarning, module="whisper")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STTService:
    def __init__(self):
        self.model = None
        self.device = self._get_device()
        self.cache: Dict[str, dict] = {}
        self.request_queue = deque()
        self.queue_lock = Lock()
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "processing_times": []
        }
        self.load_model()
    
    def _get_device(self) -> str:
        """Get device with GPU priority"""
        device = config.device.lower()
        if device in ["cuda", "gpu"]:
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                logger.info(f"CUDA available: {device_name}")
                return "cuda"
            else:
                logger.warning("CUDA requested but not available, falling back to CPU")
                return "cpu"
        elif device == "cpu":
            logger.info("Using device: CPU")
            return "cpu"
        else:
            logger.warning(f"Unknown device '{device}', falling back to CPU")
            return "cpu"
    
    def load_model(self):
        """Load Whisper model"""
        logger.info(f"Loading Whisper model: {config.model_name} on {self.device}")
        try:
            self.model = whisper.load_model(config.model_name, device=self.device)
            if self.device == "cuda":
                torch.cuda.empty_cache()
                logger.info(f"Model loaded on GPU: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("Model loaded on CPU")
        except Exception as e:
            logger.error(f"Failed to load model on {self.device}: {e}")
            if self.device == "cuda":
                logger.info("Falling back to CPU")
                self.device = "cpu"
                self.model = whisper.load_model(config.model_name, device="cpu")
            else:
                raise
    
    def unload_model(self):
        """Unload model to free GPU memory"""
        if self.model:
            del self.model
            self.model = None
            if self.device == "cuda":
                torch.cuda.empty_cache()
            logger.info("Model unloaded")
    
    def preprocess_audio(self, audio_path: str) -> str:
        """Preprocess audio (Whisper handles this internally)"""
        return audio_path
    
    def detect_language(self, audio_path: str) -> Optional[str]:
        """Detect language with Turkish priority"""
        try:
            audio = whisper.load_audio(audio_path)
            _, probs = self.model.detect_language(audio)
            detected = max(probs, key=probs.get)
            if detected == "tr" or probs.get("tr", 0) > 0.3:
                return "tr"
            return detected
        except:
            return None
    
    def transcribe(self, audio_path: str, language: Optional[str] = None, audio_hash: Optional[str] = None) -> dict:
        """Transcribe audio file to text"""
        start_time = time.time()
        
        if audio_hash and audio_hash in self.cache:
            self.metrics["cache_hits"] += 1
            logger.info("Cache hit")
            cached = self.cache[audio_hash].copy()
            cached["processing_time"] = 0.001
            return cached
        
        try:
            if not language:
                language = self.detect_language(audio_path) or config.language
            
            result = self.model.transcribe(
                audio_path,
                language=language,
                task="transcribe"
            )
            
            processing_time = time.time() - start_time
            self.metrics["total_requests"] += 1
            self.metrics["processing_times"].append(processing_time)
            if len(self.metrics["processing_times"]) > 100:
                self.metrics["processing_times"] = self.metrics["processing_times"][-100:]
            
            response = {
                "text": result["text"].strip(),
                "language": result.get("language", language or "unknown"),
                "processing_time": round(processing_time, 3)
            }
            
            if audio_hash:
                self.cache[audio_hash] = response
            
            return response
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    def get_metrics(self) -> dict:
        """Get performance metrics"""
        times = self.metrics["processing_times"]
        avg_time = sum(times) / len(times) if times else 0
        return {
            "total_requests": self.metrics["total_requests"],
            "cache_hits": self.metrics["cache_hits"],
            "cache_size": len(self.cache),
            "avg_processing_time": round(avg_time, 3),
            "queue_size": len(self.request_queue)
        }
    
    def clear_cache(self):
        """Clear transcription cache"""
        self.cache.clear()
        logger.info("Cache cleared")
