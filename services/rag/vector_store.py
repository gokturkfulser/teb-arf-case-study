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
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from configs.rag_config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, dimension: int = 768, index_base_path: str = "data/vector_index", index_name: Optional[str] = None):
        self.dimension = dimension
        self.index_base_path = PathLib(index_base_path)
        self.index_base_path.mkdir(parents=True, exist_ok=True)
        
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []
        self.chunks = []
        self.current_index_name = index_name
        
        if index_name:
            self.load_index(index_name)
        else:
            self.load_latest_index()
    
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
    
    def create_new_index(self) -> str:
        """Create new timestamped index name"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        index_name = f"index_{timestamp}"
        self.current_index_name = index_name
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        self.chunks = []
        return index_name
    
    def save_index(self, index_name: Optional[str] = None):
        """Save index and metadata to disk with timestamp"""
        if not index_name:
            if not self.current_index_name:
                index_name = self.create_new_index()
            else:
                index_name = self.current_index_name
        
        index_dir = self.index_base_path / index_name
        index_dir.mkdir(parents=True, exist_ok=True)
        
        index_file = index_dir / "index.faiss"
        metadata_file = index_dir / "metadata.pkl"
        
        faiss.write_index(self.index, str(index_file))
        
        with open(metadata_file, "wb") as f:
            pickle.dump({"chunks": self.chunks, "metadata": self.metadata, "created_at": datetime.now().isoformat()}, f)
        
        self.current_index_name = index_name
        logger.info(f"Saved index '{index_name}' with {self.index.ntotal} vectors")
    
    def find_latest_index(self) -> Optional[str]:
        """Find the latest index directory or old format index"""
        if not self.index_base_path.exists():
            return None
        
        index_dirs = [d for d in self.index_base_path.iterdir() if d.is_dir() and d.name.startswith("index_")]
        
        old_index_file = self.index_base_path / "index.faiss"
        old_metadata_file = self.index_base_path / "metadata.pkl"
        
        if old_index_file.exists() and old_metadata_file.exists():
            if not index_dirs:
                return "legacy"
            else:
                old_mtime = old_index_file.stat().st_mtime
                latest_dir = max(index_dirs, key=lambda x: x.stat().st_mtime)
                if old_mtime > latest_dir.stat().st_mtime:
                    return "legacy"
        
        if not index_dirs:
            return None
        
        latest = max(index_dirs, key=lambda x: x.stat().st_mtime)
        return latest.name
    
    def load_index(self, index_name: str):
        """Load specific index by name"""
        if index_name == "legacy":
            index_file = self.index_base_path / "index.faiss"
            metadata_file = self.index_base_path / "metadata.pkl"
        else:
            index_dir = self.index_base_path / index_name
            index_file = index_dir / "index.faiss"
            metadata_file = index_dir / "metadata.pkl"
        
        if index_file.exists() and metadata_file.exists():
            self.index = faiss.read_index(str(index_file))
            
            with open(metadata_file, "rb") as f:
                data = pickle.load(f)
                self.chunks = data.get("chunks", [])
                self.metadata = data.get("metadata", [])
            
            self.current_index_name = index_name
            logger.info(f"Loaded index '{index_name}' with {self.index.ntotal} vectors")
        else:
            logger.warning(f"Index '{index_name}' not found, starting fresh")
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            self.chunks = []
    
    def load_latest_index(self):
        """Load the latest index"""
        latest_index = self.find_latest_index()
        if latest_index:
            self.load_index(latest_index)
        else:
            logger.info("No existing index found, starting fresh")
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            self.chunks = []

