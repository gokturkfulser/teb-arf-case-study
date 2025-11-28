import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from services.gateway.api import call_stt_service, call_rag_service, CircuitBreaker


class TestGatewayFunctions:
    """Unit tests for gateway helper functions with mocked HTTP calls"""
    
    @pytest.mark.asyncio
    async def test_call_stt_service(self, mocker):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "text": "test transcription",
            "language": "tr",
            "processing_time": 1.0
        }
        
        async def mock_post(*args, **kwargs):
            return mock_response
        
        mocker.patch('httpx.AsyncClient.post', side_effect=mock_post)
        
        result = await call_stt_service(b"fake audio", "test.wav")
        
        assert "text" in result
        assert result["text"] == "test transcription"
    
    @pytest.mark.asyncio
    async def test_call_rag_service(self, mocker):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "Test answer",
            "sources": [{"title": "Test"}],
            "num_sources": 1
        }
        
        async def mock_post(*args, **kwargs):
            return mock_response
        
        mocker.patch('httpx.AsyncClient.post', side_effect=mock_post)
        
        result = await call_rag_service("test question", k=3)
        
        assert "answer" in result
        assert result["answer"] == "Test answer"
    
    def test_circuit_breaker(self):
        breaker = CircuitBreaker()
        
        assert breaker.state == "closed"
        assert breaker.failure_count == 0

