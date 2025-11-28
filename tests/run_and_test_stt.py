import subprocess
import sys
import time
import requests
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
service_script = project_root / "services" / "stt" / "main.py"

def start_service():
    """Start STT service in background"""
    print("Starting STT service...")
    process = subprocess.Popen(
        [sys.executable, str(service_script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(project_root)
    )
    return process

def wait_for_service(max_wait=30):
    """Wait for service to be ready"""
    print("Waiting for service to start...")
    for i in range(max_wait):
        try:
            response = requests.get("http://localhost:8001/health", timeout=2)
            if response.status_code == 200:
                print("Service is ready!")
                return True
        except:
            pass
        time.sleep(1)
        print(".", end="", flush=True)
    print("\nService failed to start in time")
    return False

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        print(f"✓ Health check: {response.status_code}")
        print(f"  Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_transcribe(audio_file_path):
    """Test transcription endpoint"""
    if not os.path.exists(audio_file_path):
        print(f"✗ Audio file not found: {audio_file_path}")
        return False
    
    print(f"\nTesting transcription with: {audio_file_path}")
    try:
        with open(audio_file_path, "rb") as f:
            files = {"file": (os.path.basename(audio_file_path), f, "audio/wav")}
            print("Sending request...")
            response = requests.post("http://localhost:8001/transcribe", files=files, timeout=600)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Transcription successful!")
            print(f"  Text: {result.get('text', '')[:100]}...")
            print(f"  Language: {result.get('language', 'unknown')}")
            return True
        else:
            print(f"✗ Transcription failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Transcription error: {e}")
        return False

def stop_service(process):
    """Stop the service process"""
    print("\nStopping service...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    print("Service stopped")

def main():
    audio_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not audio_file:
        print("Usage: python tests/run_and_test_stt.py <audio_file_path>")
        print("Example: python tests/run_and_test_stt.py iphone.wav")
        sys.exit(1)
    
    process = None
    try:
        process = start_service()
        time.sleep(2)
        
        if not wait_for_service():
            print("Failed to start service")
            return 1
        
        print("\n" + "="*50)
        print("Running Tests")
        print("="*50)
        
        results = []
        results.append(("Health Check", test_health()))
        results.append(("Transcription", test_transcribe(audio_file)))
        
        print("\n" + "="*50)
        print("Test Results")
        print("="*50)
        for test_name, passed in results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{test_name}: {status}")
        
        all_passed = all(result[1] for result in results)
        return 0 if all_passed else 1
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    finally:
        if process:
            stop_service(process)

if __name__ == "__main__":
    sys.exit(main())

