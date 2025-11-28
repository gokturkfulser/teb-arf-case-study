import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import os

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from services.rag.generator import ResponseGenerator


class TestResponseGenerator:
    def test_init_with_openai(self, mocker):
        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
        mocker.patch('services.rag.generator.OpenAI')
        
        generator = ResponseGenerator(use_openai=True)
        
        assert generator.use_openai is True
    
    def test_init_without_openai(self, mocker):
        mocker.patch.dict(os.environ, {}, clear=True)
        
        generator = ResponseGenerator(use_openai=False)
        
        assert generator.use_openai is False
        assert generator.openai_client is None
    
    @patch('services.rag.generator.OpenAI')
    def test_generate_with_openai(self, mock_openai_class, mocker):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated answer"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "gpt-4.1-mini"})
        
        generator = ResponseGenerator(use_openai=True)
        generator.openai_client = mock_client
        
        context = [{"text": "test context", "campaign_id": "test-1"}]
        answer = generator.generate("test question", context)
        
        assert answer == "Generated answer"
        mock_client.chat.completions.create.assert_called_once()
    
    def test_generate_without_openai(self, mocker):
        mocker.patch.dict(os.environ, {}, clear=True)
        
        generator = ResponseGenerator(use_openai=False)
        
        context = [{"text": "test context", "campaign_id": "test-1"}]
        answer = generator.generate("test question", context)
        
        assert isinstance(answer, str)
        assert len(answer) > 0

