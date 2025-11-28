import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from typing import List, Dict
from services.rag.vector_store import VectorStore
from services.rag.embeddings import EmbeddingService
from services.rag.retriever import Retriever
from services.rag.generator import ResponseGenerator
from services.rag.chunker import Chunker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore(dimension=768)
        self.retriever = Retriever(self.vector_store, self.embedding_service)
        self.generator = ResponseGenerator()
        self.chunker = Chunker()
    
    def index_campaigns(self, campaigns: List):
        """Index campaigns into vector store with new timestamped index"""
        logger.info(f"Indexing {len(campaigns)} campaigns")
        
        self.vector_store.create_new_index()
        
        all_chunks = []
        for campaign in campaigns:
            chunks = self.chunker.chunk_campaign(campaign)
            all_chunks.extend(chunks)
        
        if not all_chunks:
            logger.warning("No chunks to index")
            return
        
        texts = [chunk["text"] for chunk in all_chunks]
        embeddings = self.embedding_service.embed_batch(texts)
        
        import numpy as np
        self.vector_store.add_vectors(np.array(embeddings), all_chunks)
        self.vector_store.save_index()
        
        logger.info(f"Indexed {len(all_chunks)} chunks into '{self.vector_store.current_index_name}'")
    
    def query(self, question: str, k: int = 5) -> Dict:
        """Query RAG system"""
        retrieved = self.retriever.hybrid_search(question, k=k)
        response = self.generator.generate(question, retrieved)
        
        return {
            "answer": response,
            "sources": [
                {
                    "campaign_id": chunk.get("campaign_id", ""),
                    "title": chunk.get("title", ""),
                    "score": chunk.get("rerank_score", chunk.get("score", 0))
                }
                for chunk in retrieved
            ],
            "num_sources": len(retrieved)
        }

