# Docker Troubleshooting

## Docker Desktop Connection Error

If you see: `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`

**Solutions:**
1. Start/restart Docker Desktop
2. Check WSL2 backend is enabled in Docker Desktop settings
3. Run `wsl --shutdown` then restart Docker Desktop
4. Verify with `docker ps`

## Common Issues

### Build Hanging
**Problem**: Build gets stuck

**Solutions:**
1. Cancel and rebuild: `docker-compose up --build`
2. Check internet connection
3. Increase Docker resources in settings
4. Models download at runtime (first use)

### Gateway Missing Dependencies
**Problem**: `ModuleNotFoundError: No module named 'requests'`

**Solution**: Rebuild gateway:
```bash
docker-compose build gateway
docker-compose up -d gateway
```

### GPU not available
Use CPU version:
```bash
docker-compose -f docker-compose.cpu.yml up --build
```

### Model Downloads
Models download on first use (not during build):
- Whisper: ~1.5GB (first transcription)
- Sentence-transformers: ~420MB (first RAG query)
- Cached in volumes after first download

### Permission denied on volumes
**Solution**: Ensure Docker Desktop has access to project directory. On Windows, share the drive in Docker Desktop settings.

### Port already in use
**Solution**: Stop services using ports 8000, 8001, 8002, or change ports in docker-compose.yml

## Alternative: Run Without Docker

```bash
venv\Scripts\activate
python scripts/run_all_services.py
```
