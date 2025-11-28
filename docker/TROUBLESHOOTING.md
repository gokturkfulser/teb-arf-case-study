# Docker Troubleshooting

## Docker Desktop Connection Error

If you see this error:
```
error during connect: Get "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.51/images/...": 
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

### Solutions:

1. **Start Docker Desktop**
   - Make sure Docker Desktop is running
   - Wait for it to fully start (whale icon in system tray should be steady)

2. **Restart Docker Desktop**
   - Right-click Docker Desktop icon → Quit Docker Desktop
   - Start Docker Desktop again
   - Wait 30-60 seconds for it to initialize

3. **Check WSL2 Backend**
   - Docker Desktop → Settings → General
   - Ensure "Use the WSL 2 based engine" is checked
   - If not available, update Docker Desktop

4. **Restart WSL**
   ```powershell
   wsl --shutdown
   ```
   Then restart Docker Desktop

5. **Check Docker Service**
   ```powershell
   # Check if Docker is running
   docker ps
   ```
   If this fails, Docker Desktop is not properly started

6. **Verify Docker Installation**
   ```powershell
   docker --version
   docker-compose --version
   ```

## Common Issues

### Issue: Build Hanging/Not Finishing
**Problem**: Build gets stuck (usually during dependency installation)

**Solutions**:
1. **Cancel and rebuild**: Press Ctrl+C, then `docker-compose up --build` again
2. **Check internet connection** - Package downloads require stable connection
3. **Increase Docker resources** - Allocate more RAM/CPU in Docker Desktop settings
4. **Models download at runtime** - First query/transcription will download models (~2GB)

### Issue: Gateway service missing dependencies
**Problem**: `ModuleNotFoundError: No module named 'requests'` or similar

**Solution**: Rebuild gateway service:
```bash
docker-compose build gateway
docker-compose up -d gateway
```

### Issue: GPU not available
**Solution**: Use CPU version:
```bash
docker-compose -f docker-compose.cpu.yml up --build
```

### Issue: Models taking too long to download
**Note**: Models download at runtime (on first query/transcription), not during build.

**What to expect**:
- First transcription: Downloads Whisper model (~1.5GB, 2-5 minutes)
- First RAG query: Downloads embeddings model (~420MB, 1-2 minutes)
- Subsequent uses: Models cached, instant loading

**If stuck**: Check internet connection and Docker network settings

### Issue: Permission denied on volumes
**Solution**:
- Ensure Docker Desktop has access to the project directory
- On Windows, share the drive in Docker Desktop settings

### Issue: Port already in use
**Solution**:
- Stop services using ports 8000, 8001, 8002
- Or change ports in docker-compose.yml

## Alternative: Run Without Docker

If Docker continues to have issues, you can run services locally:

```bash
# Activate virtual environment
venv\Scripts\activate

# Run services using the script
python scripts/run_all_services.py
```

