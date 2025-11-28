# Testing

## Unit Tests

```bash
pytest tests/unit/
pytest tests/unit/ --cov=services --cov-report=html
```

## Test Structure

- `tests/unit/` - Unit tests with mocks
- `tests/integration/` - Integration tests (requires running services)
- `tests/load/` - Load testing docs

## Integration Tests

```bash
python scripts/run_all_services.py
pytest tests/integration/ -v
```

## Load Testing

```bash
pip install locust
locust -f locustfile.py --host=http://localhost:8000
```

See [tests/load/README.md](tests/load/README.md) for details.

