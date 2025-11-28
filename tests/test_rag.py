import sys
from pathlib import Path
import requests
import time
import json

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

RAG_SERVICE_URL = "http://localhost:8002"

def test_health():
    """Test health check endpoint"""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/health", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "status" in data
        assert "index_size" in data
        print(f"✓ Health check passed: {data}")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ RAG service is not running. Start it with: python services/rag/main.py")
        return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_query():
    """Test query endpoint"""
    print("\nTesting /query endpoint...")
    try:
        payload = {
            "question": "iphone kampanyası hakkında bilgi ver",
            "k": 3
        }
        response = requests.post(f"{RAG_SERVICE_URL}/query", json=payload, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "num_sources" in data
        assert isinstance(data["sources"], list)
        assert data["num_sources"] > 0, "Should return at least one source"
        print(f"✓ Query test passed")
        print(f"  Answer length: {len(data['answer'])} characters")
        print(f"  Sources: {data['num_sources']}")
        if data["sources"]:
            print(f"  Top source: {data['sources'][0].get('title', 'N/A')}")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ RAG service is not running")
        return False
    except Exception as e:
        print(f"✗ Query test failed: {e}")
        return False

def test_query_empty():
    """Test query with empty question"""
    print("\nTesting /query with empty question...")
    try:
        payload = {
            "question": "",
            "k": 3
        }
        response = requests.post(f"{RAG_SERVICE_URL}/query", json=payload, timeout=30)
        assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}"
        print(f"✓ Empty query handled (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"✗ Empty query test failed: {e}")
        return False

def test_index():
    """Test index endpoint"""
    print("\nTesting /index endpoint...")
    try:
        response = requests.post(f"{RAG_SERVICE_URL}/index", timeout=60)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "status" in data
        assert "campaigns" in data
        print(f"✓ Index test passed: {data['campaigns']} campaigns indexed")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ RAG service is not running")
        return False
    except Exception as e:
        print(f"✗ Index test failed: {e}")
        return False

def test_service_direct():
    """Test RAG service directly - uses existing index"""
    print("\nTesting RAG service directly...")
    try:
        from services.rag.service import RAGService
        
        service = RAGService()
        
        if service.vector_store.index.ntotal == 0:
            print("  Warning: No indexed data found, skipping direct test")
            return True
        
        result = service.query("kampanya", k=1)
        assert "answer" in result
        assert "sources" in result
        
        print(f"✓ Direct service test passed")
        print(f"  Answer: {result['answer'][:100]}...")
        return True
    except Exception as e:
        print(f"✗ Direct service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("RAG Service Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Health Check", test_health()))
    time.sleep(1)
    
    results.append(("Query", test_query()))
    time.sleep(1)
    
    results.append(("Empty Query", test_query_empty()))
    time.sleep(1)
        
    results.append(("Index", test_index()))
    time.sleep(1)
    
    results.append(("Direct Service", test_service_direct()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

