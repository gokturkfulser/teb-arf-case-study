from locust import HttpUser, task, between, events
import random
import json

GATEWAY_URL = "http://localhost:8000"

sample_questions = [
    "iphone kampanyası nedir",
    "autoking kampanyası hakkında bilgi ver",
    "kampanya indirimleri",
    "cepteteb kampanyaları",
    "kredi kartı kampanyası",
    "mobil uygulama kampanyası",
    "yeni kampanyalar",
    "aktif kampanyalar"
]


class GatewayUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a simulated user starts"""
        self.client.base_url = GATEWAY_URL
    
    @task(5)
    def text_query(self):
        """Text query - most common operation"""
        question = random.choice(sample_questions)
        payload = {
            "question": question,
            "k": 3
        }
        with self.client.post(
            "/api/v1/text-query",
            json=payload,
            catch_response=True,
            timeout=60
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "answer" in data and len(data["answer"]) > 0:
                    response.success()
                else:
                    response.failure("Empty answer")
            elif response.status_code == 503:
                response.failure("Service unavailable")
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(2)
    def health_check(self):
        """Health check - lightweight operation"""
        with self.client.get("/health", catch_response=True, timeout=5) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(1)
    def transcribe(self):
        """Transcribe endpoint - less frequent"""
        fake_audio = b"fake audio data for load testing"
        files = {'file': ('test.wav', fake_audio, 'audio/wav')}
        with self.client.post(
            "/api/v1/transcribe",
            files=files,
            catch_response=True,
            timeout=60
        ) as response:
            if response.status_code in [200, 400]:
                response.success()
            else:
                response.failure(f"Transcribe failed: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print(f"\n{'='*60}")
    print("Load Test Starting")
    print(f"Target: {GATEWAY_URL}")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print(f"\n{'='*60}")
    print("Load Test Completed")
    print(f"{'='*60}\n")

