# Load Testing with Locust

## Quick Start

```bash
pip install locust
python scripts/run_all_services.py
locust -f locustfile.py --host=http://localhost:8000
```

Open http://localhost:8089 in browser.

## Headless Mode

```bash
locust -f locustfile.py --headless --users 20 --spawn-rate 2 --run-time 2m --host=http://localhost:8000
```

## Test Scenarios

- Text Query (5x) - Most common
- Health Check (2x) - Lightweight
- Transcribe (1x) - Less frequent

## Performance Targets

- Response time < 3s: Good
- Failure rate < 1%: Excellent

