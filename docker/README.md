# Docker Setup

## Quick Start

1. Copy `env.example` to `.env` and add your OpenAI API key
2. Start services:
   ```bash
   # GPU (default)
   docker-compose up --build
   
   # CPU only
   docker-compose -f docker-compose.cpu.yml up --build
   ```

3. Access:
   - Gateway: http://localhost:8000
   - STT: http://localhost:8001
   - RAG: http://localhost:8002

## Environment Variables

- `OPENAI_API_KEY` - Required
- `WHISPER_DEVICE` - `cuda` (default) or `cpu`
- `OPENAI_MODEL` - `gpt-4.1-mini` (default)

## Testing

```bash
.\tests\test_services.ps1
```

## Cleanup

```bash
docker-compose down        # Stop and remove containers
docker-compose down -v     # Remove volumes too
```

See [STOP_AND_CLEANUP.md](STOP_AND_CLEANUP.md) for more options.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.
