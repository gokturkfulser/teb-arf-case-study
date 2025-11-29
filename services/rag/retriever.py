import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import re
import logging
import numpy as np
from typing import List, Dict, Optional
from services.rag.vector_store import VectorStore
from services.rag.embeddings import EmbeddingService
from configs.rag_config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.similarity_threshold = config.vector_similarity_threshold
    
    def retrieve(self, query: str, k: int = 5, similarity_threshold: Optional[float] = None) -> List[Dict]:
        """Multi-stage retrieval: vector search with semantic matching
        
        Args:
            query: Query text
            k: Number of results to return
            similarity_threshold: Maximum L2 distance threshold (default: from config)
        """
        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold
        
        query_processed = self.embedding_service.preprocess_turkish(query)
        query_vector = self.embedding_service.embed_text(query_processed)
        
        query_vector_np = np.array(query_vector).astype('float32')
        results = self.vector_store.search(query_vector_np, k=min(k*15, self.vector_store.index.ntotal))
        
        filtered_results = self._filter_by_threshold(results, similarity_threshold)
        
        reranked = self.rerank(query, filtered_results)
        
        return reranked[:k]
    
    def _filter_by_threshold(self, results: List[Dict], max_distance: float) -> List[Dict]:
        """Filter results by maximum distance threshold
        
        Note: If threshold is very high (>= 100), filtering is effectively disabled
        to allow reranking to handle quality sorting.
        """
        if max_distance >= 100.0:
            logger.debug(f"Threshold {max_distance} is very high, skipping distance filtering")
            return results
        
        filtered = []
        for result in results:
            distance = result.get("score", float('inf'))
            if distance <= max_distance:
                filtered.append(result)
            else:
                logger.debug(f"Filtered out result with distance {distance:.4f} (threshold: {max_distance})")
        
        if len(filtered) == 0 and len(results) > 0:
            logger.warning(f"All {len(results)} results filtered out by threshold {max_distance}. Returning top results anyway.")
            return results[:min(10, len(results))]
        
        logger.info(f"Filtered {len(results)} results to {len(filtered)} using threshold {max_distance}")
        return filtered
    
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
            if semantic_distance < float('inf'):
                max_distance = max(self.similarity_threshold, 10.0)
                normalized_distance = min(semantic_distance / max_distance, 1.0) if max_distance > 0 else 1.0
                semantic_similarity = 1.0 - normalized_distance
            else:
                semantic_similarity = 0.0
            
            word_match_score = exact_overlap / max(len(query_words), 1) if query_words else 0.0
            
            exact_match_in_title = query_lower in title if title else False
            exact_match_in_id = query_lower in campaign_id if campaign_id else False
            exact_match_in_text = query_lower in text if text else False
            
            key_words_in_title = sum(1 for word in query_words if word in title) if title else 0
            key_words_in_id = sum(1 for word in query_words if word in campaign_id) if campaign_id else 0
            key_words_in_text = sum(1 for word in query_words if word in text) if text else 0
            
            key_word_ratio_title = key_words_in_title / max(len(query_words), 1) if query_words else 0.0
            key_word_ratio_id = key_words_in_id / max(len(query_words), 1) if query_words else 0.0
            
            rerank_score = semantic_similarity * 0.4 + word_match_score * 0.3
            
            chunk_type = result.get("type", "")
            if chunk_type == "title_description":
                rerank_score += 0.1
            
            if exact_match_in_id:
                rerank_score = min(max(rerank_score, 0.9), 0.98)
            elif exact_match_in_title:
                rerank_score = min(max(rerank_score, 0.8), 0.92)
            elif exact_match_in_text:
                rerank_score = min(max(rerank_score, 0.7), 0.85)
            elif key_word_ratio_id >= 0.7:
                rerank_score = min(max(rerank_score, 0.75), 0.88)
            elif key_word_ratio_title >= 0.7:
                rerank_score = min(max(rerank_score, 0.65), 0.82)
            elif key_word_ratio_id >= 0.5:
                rerank_score = min(max(rerank_score, 0.6), 0.78)
            elif key_word_ratio_title >= 0.5:
                rerank_score = min(max(rerank_score, 0.55), 0.72)
            elif key_words_in_title > 0:
                rerank_score += 0.2
            elif key_words_in_id > 0:
                rerank_score += 0.25
            
            if variation_match:
                rerank_score += 0.1
            if variation_in_title:
                rerank_score += 0.15
            if variation_in_id:
                rerank_score += 0.2
            
            result["rerank_score"] = min(rerank_score, 0.99)
        
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
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
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
            
            key_words_in_title = sum(1 for word in query_words if word in title) if title else 0
            key_words_in_id = sum(1 for word in query_words if word in campaign_id) if campaign_id else 0
            key_word_ratio_title = key_words_in_title / max(len(query_words), 1) if query_words else 0.0
            key_word_ratio_id = key_words_in_id / max(len(query_words), 1) if query_words else 0.0
            
            exact_match_in_title = query_lower in title if title else False
            exact_match_in_id = query_lower in campaign_id if campaign_id else False
            
            current_score = result.get("rerank_score", result.get("keyword_score", result.get("score", 0)))
            
            if chunk_type == "title_description":
                current_score += 0.2
            
            if exact_match_in_id:
                current_score = min(max(current_score, 0.9), 0.98)
            elif exact_match_in_title:
                current_score = min(max(current_score, 0.8), 0.92)
            elif key_word_ratio_id >= 0.7:
                current_score = min(max(current_score, 0.75), 0.88)
            elif key_word_ratio_title >= 0.7:
                current_score = min(max(current_score, 0.65), 0.82)
            elif key_word_ratio_id >= 0.5:
                current_score = min(max(current_score, 0.6), 0.78)
            elif key_word_ratio_title >= 0.5:
                current_score = min(max(current_score, 0.55), 0.72)
            elif key_words_in_title > 0:
                current_score += 0.2
            elif key_words_in_id > 0:
                current_score += 0.25
            
            if variation_in_title:
                current_score += 0.2
            if variation_in_id:
                current_score += 0.3
            
            result["rerank_score"] = min(current_score, 0.99)
        
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

