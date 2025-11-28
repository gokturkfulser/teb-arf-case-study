# Load Testing with Locust

Load testing for the Gateway API to measure performance under various load conditions.

## Prerequisites

1. Install Locust:
   ```bash
   pip install locust
   ```

2. Ensure all services are running:
   ```bash
   python scripts/run_all_services.py
   ```

## Running Load Tests

### Web UI Mode (Recommended)

Start Locust web interface:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser to:
- Set number of users
- Set spawn rate (users per second)
- Start the test
- View real-time statistics

### Headless Mode (CLI)

Run load test from command line:
```bash
# 10 users, spawn rate 2/sec, run for 60 seconds
locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 60s --host=http://localhost:8000

# 50 users, spawn rate 5/sec, run for 5 minutes
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m --host=http://localhost:8000
```

### Generate HTML Report

```bash
locust -f locustfile.py --headless --users 20 --spawn-rate 2 --run-time 2m --host=http://localhost:8000 --html=load_test_report.html
```

## Test Scenarios

The load test includes:

1. **Text Query (5x weight)** - Most common operation
   - Random questions from sample set
   - Validates response structure

2. **Health Check (2x weight)** - Lightweight monitoring
   - Fast endpoint for system health

3. **Transcribe (1x weight)** - Less frequent operation
   - Audio transcription endpoint

## Performance Metrics

Locust provides:
- **Response Times**: Min, max, median, average, 95th percentile
- **Requests per Second (RPS)**: Throughput measurement
- **Failure Rate**: Percentage of failed requests
- **User Count**: Concurrent simulated users

## Recommended Test Scenarios

### Light Load
```bash
locust -f locustfile.py --headless --users 10 --spawn-rate 1 --run-time 2m --host=http://localhost:8000
```

### Medium Load
```bash
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m --host=http://localhost:8000
```

### Heavy Load
```bash
locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 10m --host=http://localhost:8000
```

### Stress Test
```bash
locust -f locustfile.py --headless --users 200 --spawn-rate 20 --run-time 15m --host=http://localhost:8000
```

## Interpreting Results

- **Response Time < 1s**: Excellent
- **Response Time 1-3s**: Good
- **Response Time 3-5s**: Acceptable
- **Response Time > 5s**: Needs optimization

- **Failure Rate < 1%**: Excellent
- **Failure Rate 1-5%**: Acceptable
- **Failure Rate > 5%**: Needs investigation

## Notes

- First requests may be slower due to model loading
- STT transcription is CPU/GPU intensive - expect higher latency
- RAG queries depend on index size and query complexity
- Gateway orchestrates multiple services - latency accumulates

## Customizing Load Tests

Edit `locustfile.py` to:
- Add more test scenarios
- Adjust task weights
- Add custom assertions
- Test specific endpoints
- Simulate different user behaviors

