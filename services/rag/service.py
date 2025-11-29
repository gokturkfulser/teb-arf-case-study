import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from typing import List, Dict, Optional
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
    
    def index_campaigns(self, campaigns: List, chunking_strategy: str = "default"):
        """Index campaigns into vector store with new timestamped index
        
        Args:
            campaigns: List of campaigns to index
            chunking_strategy: "default", "sliding_window", or "semantic"
        """
        logger.info(f"Indexing {len(campaigns)} campaigns with chunking strategy: {chunking_strategy}")
        
        self.vector_store.create_new_index()
        
        all_chunks = []
        for campaign in campaigns:
            if chunking_strategy == "sliding_window":
                chunks = self._chunk_with_sliding_window(campaign)
            elif chunking_strategy == "semantic":
                chunks = self._chunk_with_semantic(campaign)
            else:
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
    
    def _chunk_with_sliding_window(self, campaign):
        """Chunk campaign using sliding window strategy"""
        chunks = []
        title = campaign.title or ""
        description = campaign.description or ""
        
        if title or description:
            title_desc_text = f"{title}\n\n{description}".strip()
            if title_desc_text:
                chunks.append({
                    "text": title_desc_text,
                    "campaign_id": campaign.campaign_id,
                    "title": title,
                    "chunk_index": 0,
                    "type": "title_description"
                })
        
        if campaign.cleaned_text:
            cleaned_chunks = self.chunker.sliding_window_chunk(campaign.cleaned_text, campaign.campaign_id)
            for i, chunk in enumerate(cleaned_chunks, start=len(chunks)):
                chunk["title"] = title
                chunk["chunk_index"] = i
                chunks.append(chunk)
        
        return chunks if chunks else self.chunker.chunk_campaign(campaign)
    
    def _chunk_with_semantic(self, campaign):
        """Chunk campaign using semantic strategy"""
        chunks = []
        title = campaign.title or ""
        description = campaign.description or ""
        
        if title or description:
            title_desc_text = f"{title}\n\n{description}".strip()
            if title_desc_text:
                chunks.append({
                    "text": title_desc_text,
                    "campaign_id": campaign.campaign_id,
                    "title": title,
                    "chunk_index": 0,
                    "type": "title_description"
                })
        
        if campaign.cleaned_text:
            cleaned_chunks = self.chunker.semantic_chunk(campaign.cleaned_text, campaign.campaign_id)
            for i, chunk in enumerate(cleaned_chunks, start=len(chunks)):
                chunk["title"] = title
                chunk["chunk_index"] = i
                chunks.append(chunk)
        
        return chunks if chunks else self.chunker.chunk_campaign(campaign)
    
    def query(self, question: str, k: int = 5, search_strategy: str = "hybrid", similarity_threshold: Optional[float] = None) -> Dict:
        """Query RAG system
        
        Args:
            question: Query question
            k: Number of results to return
            search_strategy: "vector", "keyword", or "hybrid"
            similarity_threshold: Maximum L2 distance for vector search (only used with "vector" strategy)
        """
        if search_strategy == "vector":
            retrieved = self.retriever.retrieve(question, k=k, similarity_threshold=similarity_threshold)
        elif search_strategy == "keyword":
            retrieved = self.retriever.keyword_search(question, k=k)
        else:
            retrieved = self.retriever.hybrid_search(question, k=k)
        
        response = self.generator.generate(question, retrieved)
        
        return {
            "answer": response,
            "sources": [
                {
                    "campaign_id": chunk.get("campaign_id", ""),
                    "title": chunk.get("title", ""),
                    "score": chunk.get("rerank_score", chunk.get("keyword_score", chunk.get("score", 0)))
                }
                for chunk in retrieved
            ],
            "num_sources": len(retrieved)
        }

