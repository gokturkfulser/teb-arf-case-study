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

### Gateway Integration Tests

Gateway integration tests (`tests/integration/test_gateway_integration.py`) test the full gateway API with running STT and RAG services. These tests:
- Check service health endpoints
- Test text query flow (Gateway → RAG)
- Test voice query flow (Gateway → STT → RAG)
- Verify end-to-end functionality

