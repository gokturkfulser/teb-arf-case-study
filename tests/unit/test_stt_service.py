import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import os

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from services.stt.service import STTService
from configs.stt_config import config


class TestSTTService:
    def test_init(self, mocker):
        mock_load_model = mocker.patch.object(STTService, 'load_model')
        service = STTService()
        
        assert service.model is None
        assert service.cache == {}
        mock_load_model.assert_called_once()
    
    def test_get_device_cuda_available(self, mocker):
        mocker.patch('torch.cuda.is_available', return_value=True)
        mocker.patch('torch.cuda.get_device_name', return_value="NVIDIA RTX 4060 Ti")
        mocker.patch.object(config, 'device', 'cuda')
        
        service = STTService()
        device = service._get_device()
        
        assert device == "cuda"
    
    def test_get_device_cuda_unavailable(self, mocker):
        mocker.patch('torch.cuda.is_available', return_value=False)
        mocker.patch.object(config, 'device', 'cuda')
        
        service = STTService()
        device = service._get_device()
        
        assert device == "cpu"
    
    def test_get_device_cpu(self, mocker):
        mocker.patch.object(config, 'device', 'cpu')
        
        service = STTService()
        device = service._get_device()
        
        assert device == "cpu"
    
    def test_get_device_gpu_normalized(self, mocker):
        mocker.patch('torch.cuda.is_available', return_value=True)
        mocker.patch('torch.cuda.get_device_name', return_value="NVIDIA RTX 4060 Ti")
        mocker.patch.object(config, 'device', 'gpu')
        
        service = STTService()
        device = service._get_device()
        
        assert device == "cuda"
    
    @patch('whisper.load_model')
    def test_load_model(self, mock_load_model, mocker):
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model
        mocker.patch('torch.cuda.is_available', return_value=False)
        mocker.patch.object(config, 'device', 'cpu')
        
        service = STTService()
        
        assert service.model == mock_model
        assert mock_load_model.call_count >= 1
        mock_load_model.assert_any_call(config.model_name, device="cpu")
        
        mock_load_model.reset_mock()
        service.load_model()
        mock_load_model.assert_called_once_with(config.model_name, device="cpu")
    
    def test_transcribe(self, mocker, mock_whisper_model):
        mocker.patch('whisper.load_model', return_value=mock_whisper_model)
        mocker.patch('torch.cuda.is_available', return_value=False)
        mocker.patch.object(config, 'device', 'cpu')
        
        service = STTService()
        service.model = mock_whisper_model
        service.device = "cpu"
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(b"fake audio data")
            tmp_path = tmp.name
        
        try:
            result = service.transcribe(tmp_path)
            
            assert "text" in result
            assert "language" in result
            assert "processing_time" in result
            assert result["text"] == "test transcription"
            mock_whisper_model.transcribe.assert_called_once()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_transcribe_with_cache(self, mocker, mock_whisper_model):
        mocker.patch('whisper.load_model', return_value=mock_whisper_model)
        mocker.patch('torch.cuda.is_available', return_value=False)
        mocker.patch.object(config, 'device', 'cpu')
        
        service = STTService()
        service.model = mock_whisper_model
        service.device = "cpu"
        
        audio_hash = "test_hash"
        service.cache[audio_hash] = {
            "text": "cached text",
            "language": "en",
            "processing_time": 0.1
        }
        
        result = service.transcribe("dummy_path", audio_hash=audio_hash)
        
        assert result["text"] == "cached text"
        mock_whisper_model.transcribe.assert_not_called()

