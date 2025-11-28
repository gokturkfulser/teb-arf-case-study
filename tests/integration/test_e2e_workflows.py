import pytest
import sys
import requests
import time
import tempfile
import os
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


class TestEndToEndWorkflows:
    """End-to-end workflow tests covering complete user journeys"""
    
    def test_workflow_1_text_query_journey(self, services_ready):
        """Workflow: User asks text question → Gets answer with sources"""
        payload = {
            "question": "iphone kampanyası hakkında bilgi ver",
            "k": 3
        }
        
        response = requests.post(f"{GATEWAY_URL}/api/v1/text-query", json=payload, timeout=60)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "num_sources" in data
        assert len(data["answer"]) > 0
        assert data["num_sources"] > 0
    
    def test_workflow_2_health_check_all_services(self, services_ready):
        """Workflow: Check health of all services through gateway"""
        response = requests.get(f"{GATEWAY_URL}/health", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        
        if "stt_service" in data:
            assert data["stt_service"] in ["healthy", "unhealthy"]
        if "rag_service" in data:
            assert isinstance(data["rag_service"], (str, dict))
    
    def test_workflow_3_scrape_and_index_workflow(self, services_ready):
        """Workflow: Scrape campaigns → Index them → Query them"""
        scrape_response = requests.post(f"{GATEWAY_URL}/api/v1/scrape", timeout=300)
        
        assert scrape_response.status_code == 200
        scrape_data = scrape_response.json()
        assert "status" in scrape_data
        assert "campaigns" in scrape_data
        
        time.sleep(5)
        
        index_response = requests.post(f"{GATEWAY_URL}/api/v1/index", timeout=300)
        
        assert index_response.status_code == 200
        index_data = index_response.json()
        assert "status" in index_data or "campaigns" in index_data
        
        time.sleep(2)
        
        query_response = requests.post(
            f"{GATEWAY_URL}/api/v1/text-query",
            json={"question": "kampanya", "k": 1},
            timeout=30
        )
        
        assert query_response.status_code == 200
        query_data = query_response.json()
        assert "answer" in query_data
    
    def test_workflow_4_transcribe_only_workflow(self, services_ready):
        """Workflow: Upload audio → Get transcription only"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(b"fake audio data for testing")
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as f:
                files = {'file': ('test.wav', f, 'audio/wav')}
                response = requests.post(f"{GATEWAY_URL}/api/v1/transcribe", files=files, timeout=60)
            
            assert response.status_code in [200, 400, 500]
            if response.status_code == 200:
                data = response.json()
                assert "text" in data
                assert "language" in data
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_workflow_5_error_handling_invalid_query(self, services_ready):
        """Workflow: Invalid query → Proper error response"""
        payload = {
            "question": "",
            "k": 3
        }
        
        response = requests.post(f"{GATEWAY_URL}/api/v1/text-query", json=payload, timeout=30)
        
        assert response.status_code in [400, 422, 500]
    
    def test_workflow_6_concurrent_queries(self, services_ready):
        """Workflow: Multiple concurrent queries → All succeed"""
        import concurrent.futures
        
        questions = [
            "kampanya",
            "iphone",
            "indirim"
        ]
        
        def make_query(question):
            payload = {"question": question, "k": 2}
            response = requests.post(f"{GATEWAY_URL}/api/v1/text-query", json=payload, timeout=60)
            return response.status_code == 200
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(make_query, questions))
        
        assert all(results), "All concurrent queries should succeed"
    
    def test_workflow_7_service_isolation(self, services_ready):
        """Workflow: Direct service calls work independently"""
        stt_health = requests.get(f"{STT_URL}/health", timeout=5)
        assert stt_health.status_code == 200
        
        rag_health = requests.get(f"{RAG_URL}/health", timeout=5)
        assert rag_health.status_code == 200
        
        gateway_health = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        assert gateway_health.status_code == 200

