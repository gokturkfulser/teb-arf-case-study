import requests
import sys
import os

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8001/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_transcribe(audio_file_path):
    """Test transcription endpoint"""
    if not os.path.exists(audio_file_path):
        print(f"Audio file not found: {audio_file_path}")
        return False
    
    try:
        with open(audio_file_path, "rb") as f:
            files = {"file": (os.path.basename(audio_file_path), f, "audio/wav")}
            response = requests.post("http://localhost:8001/transcribe", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Transcription successful!")
            print(f"Text: {result.get('text', '')}")
            print(f"Language: {result.get('language', 'unknown')}")
            return True
        else:
            print(f"Transcription failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Transcription error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        print("Testing STT Service...")
        if test_health():
            test_transcribe(audio_file)
        else:
            print("Service is not running. Start it with: python services/stt/main.py")
    else:
        print("Usage: python tests/test_stt.py <audio_file_path>")
        print("Example: python tests/test_stt.py test_audio.wav")

