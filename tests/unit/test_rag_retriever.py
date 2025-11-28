import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock
import numpy as np

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from services.rag.retriever import Retriever


class TestRetriever:
    def test_init(self, mock_embedding_service, mock_vector_store):
        retriever = Retriever(mock_vector_store, mock_embedding_service)
        
        assert retriever.vector_store == mock_vector_store
        assert retriever.embedding_service == mock_embedding_service
    
    def test_retrieve(self, mock_embedding_service, mock_vector_store):
        mock_embedding_service.embed_text.return_value = np.array([0.1] * 768)
        mock_vector_store.search.return_value = [
            {"text": "chunk 1", "campaign_id": "test-1", "score": 0.5},
            {"text": "chunk 2", "campaign_id": "test-2", "score": 0.6}
        ]
        
        retriever = Retriever(mock_vector_store, mock_embedding_service)
        results = retriever.retrieve("test query", k=2)
        
        assert len(results) == 2
        mock_embedding_service.embed_text.assert_called_once()
        mock_vector_store.search.assert_called_once()
    
    def test_retrieve_empty_index(self, mock_embedding_service, mock_vector_store):
        mock_vector_store.index.ntotal = 0
        mock_vector_store.search.return_value = []
        
        retriever = Retriever(mock_vector_store, mock_embedding_service)
        results = retriever.retrieve("test query", k=2)
        
        assert results == []
    
    def test_rerank(self, mock_embedding_service, mock_vector_store):
        results = [
            {"text": "test chunk", "campaign_id": "test-1", "score": 0.5, "title": "Test"},
            {"text": "other chunk", "campaign_id": "test-2", "score": 0.6, "title": "Other"}
        ]
        
        retriever = Retriever(mock_vector_store, mock_embedding_service)
        reranked = retriever.rerank("test query", results)
        
        assert len(reranked) == 2
        assert "rerank_score" in reranked[0]
        assert reranked[0]["rerank_score"] > 0
    
    def test_keyword_search(self, mock_embedding_service, mock_vector_store):
        mock_vector_store.chunks = [
            {"text": "test chunk with query", "campaign_id": "test-1", "title": "Test"},
            {"text": "other chunk", "campaign_id": "test-2", "title": "Other"}
        ]
        
        retriever = Retriever(mock_vector_store, mock_embedding_service)
        results = retriever.keyword_search("query", k=2)
        
        assert len(results) > 0
        assert "keyword_score" in results[0]

