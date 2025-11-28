import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import re
import logging
import numpy as np
from typing import List, Dict
from services.rag.vector_store import VectorStore
from services.rag.embeddings import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """Multi-stage retrieval: vector search with semantic matching"""
        query_processed = self.embedding_service.preprocess_turkish(query)
        query_vector = self.embedding_service.embed_text(query_processed)
        
        query_vector_np = np.array(query_vector).astype('float32')
        results = self.vector_store.search(query_vector_np, k=min(k*15, self.vector_store.index.ntotal))
        
        reranked = self.rerank(query, results)
        
        return reranked
    
    def rerank(self, query: str, results: List[Dict]) -> List[Dict]:
        """Reranking that prioritizes semantic similarity and variation matches"""
        from services.rag.preprocessing import TurkishPreprocessor
        preprocessor = TurkishPreprocessor()
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        processed_query = preprocessor.preprocess_query(query)
        processed_variations = preprocessor._generate_variations(processed_query)
        query_variations = preprocessor._generate_variations(query)
        all_variations = query_variations | processed_variations
        
        for result in results:
            text = result.get("text", "").lower()
            title = result.get("title", "").lower() if result.get("title") else ""
            campaign_id = result.get("campaign_id", "").lower()
            full_text = f"{text} {title} {campaign_id}"
            text_words = set(text.split())
            
            exact_overlap = len(query_words & text_words)
            
            variation_match = False
            variation_in_title = False
            variation_in_id = False
            for variation in all_variations:
                if len(variation) > 2:
                    if variation in full_text:
                        variation_match = True
                    if variation in title:
                        variation_in_title = True
                    if variation in campaign_id:
                        variation_in_id = True
                        break
            
            semantic_distance = result.get("score", float('inf'))
            semantic_similarity = 1.0 / (1.0 + semantic_distance) if semantic_distance < float('inf') else 0.0
            
            word_match_score = exact_overlap / max(len(query_words), 1) if query_words else 0.0
            
            rerank_score = semantic_similarity * 0.4 + word_match_score * 0.1
            
            chunk_type = result.get("type", "")
            if chunk_type == "title_description":
                rerank_score += 0.2
            
            if variation_match:
                rerank_score += 0.3
            if variation_in_title:
                rerank_score += 0.6
            if variation_in_id:
                rerank_score += 0.8
            
            result["rerank_score"] = rerank_score
        
        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return results
    
    def hybrid_search(self, query: str, k: int = 5) -> List[Dict]:
        """Hybrid search combining vector and keyword matching"""
        from services.rag.preprocessing import TurkishPreprocessor
        preprocessor = TurkishPreprocessor()
        
        processed_query = preprocessor.preprocess_query(query)
        all_variations = preprocessor._generate_variations(query) | preprocessor._generate_variations(processed_query)
        
        vector_results = self.retrieve(query, k=k*15)
        
        keyword_results = self.keyword_search(query, k=k*5)
        
        combined = self._merge_results(vector_results, keyword_results)
        
        for result in combined:
            title = result.get("title", "").lower() if result.get("title") else ""
            text = result.get("text", "").lower()
            campaign_id = result.get("campaign_id", "").lower()
            chunk_type = result.get("type", "")
            full_text = f"{text} {title} {campaign_id}"
            
            variation_in_title = False
            variation_in_id = False
            for variation in all_variations:
                if len(variation) > 2:
                    if variation in title:
                        variation_in_title = True
                    if variation in campaign_id:
                        variation_in_id = True
                        break
            
            current_score = result.get("rerank_score", result.get("keyword_score", result.get("score", 0)))
            
            if chunk_type == "title_description":
                current_score += 0.3
            
            if variation_in_title:
                current_score += 0.6
            if variation_in_id:
                current_score += 0.9
            result["rerank_score"] = current_score
        
        combined_sorted = sorted(combined, key=lambda x: x.get("rerank_score", x.get("keyword_score", x.get("score", float('inf')))), reverse=True)
        
        return combined_sorted[:k]
    
    def keyword_search(self, query: str, k: int = 5) -> List[Dict]:
        """Keyword-based search with variation matching"""
        from services.rag.preprocessing import TurkishPreprocessor
        preprocessor = TurkishPreprocessor()
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        processed_query = preprocessor.preprocess_query(query)
        processed_variations = preprocessor._generate_variations(processed_query)
        query_variations = preprocessor._generate_variations(query)
        all_variations = query_variations | processed_variations
        
        matches = []
        
        for chunk in self.vector_store.chunks:
            text = chunk.get("text", "").lower()
            title = chunk.get("title", "").lower() if chunk.get("title") else ""
            campaign_id = chunk.get("campaign_id", "").lower()
            text_words = set(text.split())
            full_text = f"{text} {title} {campaign_id}"
            
            exact_overlap = len(query_words & text_words)
            
            variation_match = False
            variation_in_title = False
            variation_in_id = False
            for variation in all_variations:
                if len(variation) > 2:
                    if variation in full_text:
                        variation_match = True
                    if variation in title:
                        variation_in_title = True
                    if variation in campaign_id:
                        variation_in_id = True
                        break
            
            if exact_overlap > 0 or variation_match:
                score = (exact_overlap / max(len(query_words), 1)) * 0.3
                if variation_match:
                    score += 0.4
                if variation_in_title:
                    score += 0.5
                if variation_in_id:
                    score += 0.7
                
                match = chunk.copy()
                match["keyword_score"] = score
                matches.append(match)
        
        matches.sort(key=lambda x: x.get("keyword_score", 0), reverse=True)
        return matches[:k]
    
    def _merge_results(self, vector_results: List[Dict], keyword_results: List[Dict]) -> List[Dict]:
        """Merge and deduplicate results"""
        seen = set()
        merged = []
        
        for result in vector_results + keyword_results:
            chunk_id = f"{result.get('campaign_id', '')}_{result.get('chunk_index', 0)}"
            if chunk_id not in seen:
                seen.add(chunk_id)
                merged.append(result)
        
        return merged

