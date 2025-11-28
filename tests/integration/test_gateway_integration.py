import pytest
import sys
import requests
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

GATEWAY_URL = "http://localhost:8000"
STT_URL = "http://localhost:8001"
RAG_URL = "http://localhost:8002"


def wait_for_service(url, max_wait=60):
    """Wait for a service to be ready"""
    for _ in range(max_wait):
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False


@pytest.fixture(scope="module")
def services_ready():
    """Check if all services are running"""
    stt_ready = wait_for_service(STT_URL, max_wait=10)
    rag_ready = wait_for_service(RAG_URL, max_wait=10)
    gateway_ready = wait_for_service(GATEWAY_URL, max_wait=10)
    
    if not (stt_ready and rag_ready and gateway_ready):
        pytest.skip("Services not running. Start them with: python scripts/run_all_services.py")


class TestGatewayIntegration:
    def test_health_endpoint(self, services_ready):
        response = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_text_query_endpoint(self, services_ready):
        payload = {
            "question": "test kampanyası",
            "k": 3
        }
        response = requests.post(f"{GATEWAY_URL}/api/v1/text-query", json=payload, timeout=30)
        
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
            assert "sources" in data

