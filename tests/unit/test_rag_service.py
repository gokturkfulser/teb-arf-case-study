import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from services.rag.service import RAGService
from shared.models.rag_models import CampaignMetadata


class TestRAGService:
    def test_init(self, mocker):
        mock_embedding = mocker.patch('services.rag.service.EmbeddingService')
        mock_vector = mocker.patch('services.rag.service.VectorStore')
        mock_retriever = mocker.patch('services.rag.service.Retriever')
        mock_generator = mocker.patch('services.rag.service.ResponseGenerator')
        mock_chunker = mocker.patch('services.rag.service.Chunker')
        
        service = RAGService()
        
        assert service.embedding_service is not None
        assert service.vector_store is not None
        assert service.retriever is not None
        assert service.generator is not None
        assert service.chunker is not None
    
    def test_index_campaigns(self, mocker, sample_campaign, mock_embedding_service, mock_vector_store):
        mocker.patch('services.rag.service.EmbeddingService', return_value=mock_embedding_service)
        mocker.patch('services.rag.service.VectorStore', return_value=mock_vector_store)
        mocker.patch('services.rag.service.Retriever')
        mocker.patch('services.rag.service.ResponseGenerator')
        
        mock_chunker = MagicMock()
        mock_chunk = {"text": "test chunk", "campaign_id": "test-1"}
        mock_chunker.chunk_campaign.return_value = [mock_chunk]
        mocker.patch('services.rag.service.Chunker', return_value=mock_chunker)
        
        mock_vector_store.create_new_index = MagicMock()
        
        service = RAGService()
        service.chunker = mock_chunker
        service.vector_store = mock_vector_store
        service.embedding_service = mock_embedding_service
        
        campaigns = [sample_campaign]
        service.index_campaigns(campaigns)
        
        mock_vector_store.create_new_index.assert_called_once()
        mock_chunker.chunk_campaign.assert_called_once_with(sample_campaign)
        mock_embedding_service.embed_batch.assert_called_once()
        mock_vector_store.add_vectors.assert_called_once()
        mock_vector_store.save_index.assert_called_once()
    
    def test_index_campaigns_empty(self, mocker, mock_embedding_service, mock_vector_store):
        mocker.patch('services.rag.service.EmbeddingService', return_value=mock_embedding_service)
        mocker.patch('services.rag.service.VectorStore', return_value=mock_vector_store)
        mocker.patch('services.rag.service.Retriever')
        mocker.patch('services.rag.service.ResponseGenerator')
        
        mock_chunker = MagicMock()
        mock_chunker.chunk_campaign.return_value = []
        mocker.patch('services.rag.service.Chunker', return_value=mock_chunker)
        
        service = RAGService()
        service.chunker = mock_chunker
        service.vector_store = mock_vector_store
        
        service.index_campaigns([])
        
        mock_vector_store.add_vectors.assert_not_called()
    
    def test_query(self, mocker, mock_retriever, mock_generator):
        mocker.patch('services.rag.service.EmbeddingService')
        mocker.patch('services.rag.service.VectorStore')
        mocker.patch('services.rag.service.Retriever', return_value=mock_retriever)
        mocker.patch('services.rag.service.ResponseGenerator', return_value=mock_generator)
        mocker.patch('services.rag.service.Chunker')
        
        mock_retriever.hybrid_search = mocker.MagicMock(return_value=[
            {"text": "test chunk", "campaign_id": "test-1", "score": 0.5, "title": "Test"}
        ])
        
        service = RAGService()
        service.retriever = mock_retriever
        service.generator = mock_generator
        
        result = service.query("test question", k=3)
        
        assert "answer" in result
        assert "sources" in result
        assert "num_sources" in result
        assert result["answer"] == "Test answer"
        mock_retriever.hybrid_search.assert_called_once_with("test question", k=3)
        mock_generator.generate.assert_called_once()

