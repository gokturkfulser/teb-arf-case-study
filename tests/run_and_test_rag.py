import sys
from pathlib import Path
import subprocess
import time
import signal
import os

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def start_rag_service():
    """Start RAG service in background"""
    print("Starting RAG service...")
    process = subprocess.Popen(
        [sys.executable, "services/rag/main.py"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return process

def wait_for_service(url="http://localhost:8002/health", max_wait=30):
    """Wait for service to be ready"""
    import requests
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print("RAG service is ready!")
                return True
        except:
            pass
        time.sleep(1)
    return False

def main():
    """Run RAG service and tests"""
    rag_process = None
    
    try:
        rag_process = start_rag_service()
        time.sleep(3)
        
        if not wait_for_service():
            print("Failed to start RAG service")
            return 1
        
        print("\nRunning tests...")
        sys.path.insert(0, str(project_root / "tests"))
        from test_rag import run_all_tests
        success = run_all_tests()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        if rag_process:
            print("\nStopping RAG service...")
            rag_process.terminate()
            try:
                rag_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                rag_process.kill()
            print("RAG service stopped")

if __name__ == "__main__":
    sys.exit(main())

