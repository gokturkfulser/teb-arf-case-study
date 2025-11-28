# Docker Setup

## Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose

## Quick Start

1. Copy `env.example` to `.env` and configure:
   ```bash
   OPENAI_API_KEY=your_key_here
   OPENAI_MODEL=gpt-4o-mini
   WHISPER_DEVICE=cuda  # GPU is default
   ```

2. Build and start all services:
   
   **For GPU (CUDA) - DEFAULT:**
   ```bash
   docker-compose up --build
   ```
   Note: Requires NVIDIA GPU with Docker GPU support enabled
   
   **For CPU-only:**
   ```bash
   docker-compose -f docker-compose.cpu.yml up --build
   ```

3. Access services:
   - Gateway: http://localhost:8000
   - STT: http://localhost:8001
   - RAG: http://localhost:8002

## Docker Compose Files

- **`docker-compose.yml`** - Main compose file (GPU/CUDA version)
- **`docker-compose.cpu.yml`** - CPU-only version (for systems without GPU)

Both files are in the project root (not in `docker/` folder) because:
- Docker Compose looks for them in the root by default
- Build context (`.`) needs to be project root to access all files
- This is the standard Docker Compose convention

## Building Individual Services

**GPU version:**
```bash
docker build -f docker/Dockerfile.stt -t tebarf-stt .
docker build -f docker/Dockerfile.rag -t tebarf-rag .
docker build -f docker/Dockerfile.gateway -t tebarf-gateway .
```

**CPU version (STT only):**
```bash
docker build -f docker/Dockerfile.stt.cpu -t tebarf-stt .
```

## Volumes

- `./data` - Campaign data and vector indices
- `whisper-models` - Cached Whisper models
- `embeddings-models` - Cached sentence-transformers models

## Environment Variables

- `WHISPER_DEVICE`: `cuda` or `cpu` (default: `cuda`)
- `OPENAI_API_KEY`: OpenAI API key for RAG generation
- `OPENAI_MODEL`: Model name (default: `gpt-4o-mini`)
- `CEPTETEB_URL`: Base URL for scraping (default: https://www.cepteteb.com.tr)

## Testing Services

After starting services, test them:

```powershell
# Check service status
docker-compose ps

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Test text query
$body = @{ question = "iphone kampanyası nedir"; k = 3 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/text-query" -Method Post -Body $body -ContentType "application/json"

# Or run the test script
.\tests\test_services.ps1
```

## Stopping Services

**Stop containers (keep for restart):**
```bash
docker-compose stop
```

**Stop and remove containers:**
```bash
docker-compose down
```

**Stop and remove everything (including volumes):**
```bash
docker-compose down -v
```

See [STOP_AND_CLEANUP.md](STOP_AND_CLEANUP.md) for detailed cleanup commands.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting guide.

**Quick fixes:**
- **GPU not working**: Use `docker-compose -f docker-compose.cpu.yml up --build`
- **Models downloading**: Normal on first use, cached after that
- **Services not starting**: Check logs with `docker-compose logs [service-name]`
