import sys
from pathlib import Path
import pytest

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

@pytest.fixture
def mock_whisper_model(mocker):
    mock_model = mocker.MagicMock()
    mock_model.transcribe.return_value = {
        "text": "test transcription",
        "language": "tr"
    }
    return mock_model

@pytest.fixture
def mock_openai_client(mocker):
    mock_client = mocker.MagicMock()
    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock()]
    mock_response.choices[0].message.content = "Test answer"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

@pytest.fixture
def mock_embedding_service(mocker):
    mock_service = mocker.MagicMock()
    mock_service.embed_text.return_value = [0.1] * 768
    mock_service.embed_batch.return_value = [[0.1] * 768] * 5
    return mock_service

@pytest.fixture
def mock_vector_store(mocker):
    mock_store = mocker.MagicMock()
    mock_store.index.ntotal = 10
    mock_store.search.return_value = [
        {"text": "test chunk", "campaign_id": "test-1", "score": 0.5, "title": "Test Campaign"}
    ]
    mock_store.chunks = [{"text": "test", "campaign_id": "test-1"}]
    return mock_store

@pytest.fixture
def mock_vector_store(mocker):
    mock_store = mocker.MagicMock()
    mock_store.index.ntotal = 10
    mock_store.search.return_value = [
        {"text": "test chunk", "campaign_id": "test-1", "score": 0.5, "title": "Test Campaign"}
    ]
    mock_store.chunks = [{"text": "test", "campaign_id": "test-1"}]
    mock_store.current_index_name = "test_index"
    mock_store.create_new_index = mocker.MagicMock(return_value="test_index")
    return mock_store

@pytest.fixture
def mock_retriever(mocker, mock_vector_store, mock_embedding_service):
    from services.rag.retriever import Retriever
    retriever = Retriever(mock_vector_store, mock_embedding_service)
    retriever.hybrid_search = mocker.MagicMock(return_value=[
        {"text": "test chunk", "campaign_id": "test-1", "score": 0.5, "title": "Test"}
    ])
    return retriever

@pytest.fixture
def mock_generator(mocker):
    from services.rag.generator import ResponseGenerator
    generator = ResponseGenerator(use_openai=False)
    generator.generate = mocker.MagicMock(return_value="Test answer")
    return generator

@pytest.fixture
def sample_campaign():
    from shared.models.rag_models import CampaignMetadata
    return CampaignMetadata(
        campaign_id="test-1",
        title="Test Campaign",
        description="Test description",
        cleaned_text="Test content for campaign"
    )

