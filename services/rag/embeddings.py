import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import torch
import logging
from typing import List
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading embedding model: {model_name} on {self.device}")
        self.model = SentenceTransformer(model_name, device=self.device)
        logger.info("Embedding model loaded")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        embeddings = self.model.encode(
            texts, 
            convert_to_numpy=True, 
            show_progress_bar=False,
            batch_size=batch_size
        )
        return embeddings.tolist()
    
    def preprocess_turkish(self, text: str) -> str:
        """Preprocess Turkish text for better embeddings"""
        import re
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

