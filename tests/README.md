# Testing Suite

## Unit Tests (pytest)

Unit tests with mocked external dependencies for fast, isolated testing.

### Run All Unit Tests
```bash
pytest tests/unit/
```

### Run Specific Test File
```bash
pytest tests/unit/test_stt_service.py
pytest tests/unit/test_rag_service.py
pytest tests/unit/test_gateway.py
```

### Run with Coverage
```bash
pytest tests/unit/ --cov=services --cov-report=html
```

### Run with Verbose Output
```bash
pytest tests/unit/ -v
```

## Test Structure

```
tests/
├── unit/                    # Unit tests (pytest)
│   ├── test_stt_service.py
│   ├── test_rag_service.py
│   ├── test_rag_retriever.py
│   ├── test_rag_generator.py
│   ├── test_gateway.py
│   └── test_chunker.py
├── conftest.py             # Shared pytest fixtures
├── test_stt.py             # Integration tests (requires running service)
├── test_rag.py             # Integration tests (requires running service)
└── test_services.ps1       # Docker service tests
```

## What's Tested

### STT Service
- Device detection (CUDA/CPU)
- Model loading
- Transcription with caching
- Error handling

### RAG Service
- Campaign indexing
- Query processing
- Empty input handling

### RAG Retriever
- Vector search
- Keyword search
- Hybrid search
- Re-ranking

### RAG Generator
- OpenAI integration (mocked)
- Template-based generation
- Context building

### Gateway API (Unit Tests)
- Helper functions (`call_stt_service`, `call_rag_service`)
- Circuit breaker logic
- Mocked HTTP calls

**Note:** Gateway unit tests focus on individual functions with mocked dependencies. For full integration testing with running services, see Integration Tests below.

### Chunker
- Text chunking
- Campaign chunking
- Edge cases

## Mocked Dependencies

- **Whisper model** - Mocked to avoid loading large models
- **OpenAI API** - Mocked to avoid API calls
- **Embedding service** - Mocked for fast tests
- **Vector store** - Mocked FAISS operations
- **HTTP clients** - Mocked for gateway tests

## Integration Tests

Integration tests require services to be running. Start services first:

```bash
# Start all services
python scripts/run_all_services.py

# Then run integration tests
pytest tests/integration/ -v

# Or run individual integration tests
python tests/run_and_test_stt.py <audio_file>
python tests/run_and_test_rag.py

# Test Docker services
.\tests\test_services.ps1
```

### End-to-End Workflow Tests

End-to-end tests (`tests/integration/test_e2e_workflows.py`) cover complete user journeys:

- **Text Query Journey**: User asks question → Gets answer with sources
- **Health Check Workflow**: Check all services through gateway
- **Scrape and Index Workflow**: Scrape → Index → Query
- **Transcribe Workflow**: Upload audio → Get transcription
- **Error Handling**: Invalid inputs → Proper error responses
- **Concurrent Queries**: Multiple simultaneous requests
- **Service Isolation**: Direct service calls work independently

### Gateway Integration Tests

Gateway integration tests (`tests/integration/test_gateway_integration.py`) test the full gateway API with running STT and RAG services. These tests:
- Check service health endpoints
- Test text query flow (Gateway → RAG)
- Test voice query flow (Gateway → STT → RAG)
- Verify end-to-end functionality

## Load Testing

Load testing with Locust to measure performance under various load conditions.

### Quick Start

```bash
# Install Locust (if not already installed)
pip install locust

# Start services first
python scripts/run_all_services.py

# Run Locust web UI
locust -f locustfile.py --host=http://localhost:8000

# Open http://localhost:8089 in browser
```

### Load Test Scenarios

The load test (`locustfile.py`) includes:
- **Text Query** (5x weight) - Most common operation
- **Health Check** (2x weight) - Lightweight monitoring
- **Transcribe** (1x weight) - Less frequent operation

See [tests/load/README.md](tests/load/README.md) for detailed load testing documentation.

