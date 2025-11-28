import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import faiss
import numpy as np
import json
import pickle
import logging
from pathlib import Path as PathLib
from typing import List, Dict, Tuple
from configs.rag_config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, dimension: int = 768, index_path: str = "data/vector_index"):
        self.dimension = dimension
        self.index_path = PathLib(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []
        self.chunks = []
        
        self.load_index()
    
    def add_vectors(self, vectors: np.ndarray, chunks: List[Dict]):
        """Add vectors and metadata to index"""
        if len(vectors) != len(chunks):
            raise ValueError("Vectors and chunks must have same length")
        
        vectors = np.array(vectors).astype('float32')
        self.index.add(vectors)
        
        for chunk in chunks:
            self.chunks.append(chunk)
            self.metadata.append({
                "chunk_index": len(self.metadata),
                "campaign_id": chunk.get("campaign_id", ""),
                "text": chunk.get("text", "")[:200]
            })
        
        logger.info(f"Added {len(chunks)} vectors to index. Total: {self.index.ntotal}")
    
    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Dict]:
        """Search for similar vectors"""
        if self.index.ntotal == 0:
            return []
        
        query_vector = np.array([query_vector]).astype('float32')
        distances, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.chunks):
                result = self.chunks[idx].copy()
                result["score"] = float(distance)
                result["rank"] = i + 1
                results.append(result)
        
        return results
    
    def save_index(self):
        """Save index and metadata to disk"""
        index_file = self.index_path / "index.faiss"
        metadata_file = self.index_path / "metadata.pkl"
        
        faiss.write_index(self.index, str(index_file))
        
        with open(metadata_file, "wb") as f:
            pickle.dump({"chunks": self.chunks, "metadata": self.metadata}, f)
        
        logger.info(f"Saved index with {self.index.ntotal} vectors")
    
    def load_index(self):
        """Load index and metadata from disk"""
        index_file = self.index_path / "index.faiss"
        metadata_file = self.index_path / "metadata.pkl"
        
        if index_file.exists() and metadata_file.exists():
            self.index = faiss.read_index(str(index_file))
            
            with open(metadata_file, "rb") as f:
                data = pickle.load(f)
                self.chunks = data.get("chunks", [])
                self.metadata = data.get("metadata", [])
            
            logger.info(f"Loaded index with {self.index.ntotal} vectors")
        else:
            logger.info("No existing index found, starting fresh")

