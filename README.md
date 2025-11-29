# TEB ARF STT-RAG Integration

STT and RAG integration for campaign queries.

## Features

- Speech-to-Text with Whisper (GPU)
- RAG system with OpenAI
- Unified gateway API
- Auto-indexing on first use

## Quick Start

### Docker (Recommended)

1. Copy environment file: `cp env.example .env`
2. Add your OpenAI API key to `.env`
3. Start services:
   - **GPU (default)**: `docker-compose up --build`
   - **CPU-only**: `docker-compose -f docker-compose.cpu.yml up --build`
4. Access Gateway: http://localhost:8000

See [docker/README.md](docker/README.md) for detailed Docker instructions.

### Local Development

1. Create virtual environment: `python -m venv venv`
2. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
3. Install PyTorch:
   - **GPU (CUDA 12.1)**: `pip install -r requirements-cuda.txt`
   - **CPU-only**: `pip install torch torchvision torchaudio`
4. Install dependencies: `pip install -r requirements.txt`
5. Run services: `python scripts/run_all_services.py`

## API Endpoints

### Gateway Service (Port 8000)

- `POST /api/v1/voice-query` - Audio input → Text response
  - Query params: `search_strategy` (vector/keyword/hybrid)
- `POST /api/v1/text-query` - Text input → Text response
  - Body: `question`, `k`, `search_strategy`, `similarity_threshold`
- `POST /api/v1/transcribe` - Audio → Text only
- `POST /api/v1/scrape` - Scrape campaigns
- `POST /api/v1/index` - Index campaigns
  - Body: `chunking_strategy` (default/sliding_window/semantic)
- `GET /health` - Health check

### STT Service (Port 8001)

- `POST /transcribe` - Transcribe audio file
- `POST /transcribe/json` - Transcribe base64 audio
- `GET /health` - Health check

### RAG Service (Port 8002)

- `POST /query` - Query campaign data
  - Body: `question`, `k`, `search_strategy`, `similarity_threshold`
- `POST /index` - Index campaigns
  - Body: `chunking_strategy` (default/sliding_window/semantic)
- `GET /health` - Health check

## Usage Examples

### Text Query
```bash
curl -X POST http://localhost:8000/api/v1/text-query \
  -H "Content-Type: application/json" \
  -d '{"question": "iphone kampanyası vardı o neydi", "k": 3, "search_strategy": "hybrid"}'
```

### Voice Query
```bash
curl -X POST "http://localhost:8000/api/v1/voice-query?search_strategy=hybrid" \
  -F "file=@audio.wav"
```

### Index Campaigns
```bash
curl -X POST http://localhost:8000/api/v1/index \
  -H "Content-Type: application/json" \
  -d '{"chunking_strategy": "default"}'
```

## Indexing Strategies

### Search Strategies (Query Time)

Choose how to search for relevant documents:

- **`hybrid`** (default): Combines vector semantic search and keyword matching for best results
- **`vector`**: Pure semantic similarity search using embeddings (filters by similarity threshold)
- **`keyword`**: Text-based keyword matching with Turkish variation detection

**Usage:**
```json
{
  "question": "iphone kampanyası nedir",
  "k": 5,
  "search_strategy": "hybrid",
  "similarity_threshold": 50.0
}
```

### Chunking Strategies (Indexing Time)

Choose how to split campaign data into searchable chunks:

- **`default`** (default): Title+description as one chunk + semantic chunks from cleaned_text
- **`sliding_window`**: Overlapping fixed-size chunks for comprehensive coverage
- **`semantic`**: Paragraph-based semantic chunks preserving document structure

**Usage:**
```json
{
  "chunking_strategy": "default"
}
```

## Configuration

See [ENV_SETUP.md](ENV_SETUP.md) for environment variable configuration.

**Required:**
- `OPENAI_API_KEY` - OpenAI API key for RAG generation

**Optional:**
- `WHISPER_DEVICE` - `cuda` (default) or `cpu`
- `OPENAI_MODEL` - Model name (default: `gpt-4.1-mini`)
- `VECTOR_SIMILARITY_THRESHOLD` - Maximum L2 distance for vector search (default: `50.0`)
  - Lower values = stricter filtering (fewer results)
  - Higher values = more lenient (more results)
  - Set to `100.0` or higher to disable filtering

## Testing

See [tests/README.md](tests/README.md) for detailed testing documentation.

### Unit Tests

```bash
pytest tests/unit/
pytest tests/unit/ --cov=services --cov-report=html
```

### Integration Tests

```bash
python scripts/run_all_services.py
pytest tests/integration/ -v
```

### Load Testing

```bash
pip install locust
locust -f locustfile.py --host=http://localhost:8000
```

### Postman

Import `postman/TEB_ARF_STT_RAG_Integration.postman_collection.json` into Postman.

### Manual Testing

Test services manually:
```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## Streamlit Web App

Interactive web interface for testing APIs:

```bash
# Start services first
python scripts/run_all_services.py

# Run the app (in a new terminal)
python scripts/run_streamlit.py

# Or directly
streamlit run streamlit/app.py
```

Access at: http://localhost:8501

**Features:**
- 💬 Text queries with example questions
- 🎙️ Voice queries with audio upload
- 📝 Audio transcription
- 🔍 Campaign scraping and indexing
- 📈 System health monitoring
- 🎨 Modern, responsive UI

## Project Structure

```
tebarf-stt-rag-integration/
├── streamlit/
│   └── app.py        # Streamlit web application
├── services/
│   ├── stt/          # Speech-to-Text service
│   ├── rag/          # RAG service
│   └── gateway/      # Unified API gateway
├── shared/           # Shared models and utilities
├── configs/          # Configuration files
├── tests/            # Test files
├── scripts/          # Utility scripts
└── docker/           # Docker configuration
```

## Documentation

- [Docker Setup](docker/README.md)
- [Environment Variables](ENV_SETUP.md)
- [Docker Troubleshooting](docker/TROUBLESHOOTING.md)

