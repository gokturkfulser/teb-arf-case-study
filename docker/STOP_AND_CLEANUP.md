# Stopping and Cleaning Up Docker Resources

## Stop Services

### Stop all running containers (keep containers)
```bash
docker-compose stop
```

### Stop and remove containers (keep images and volumes)
```bash
docker-compose down
```

### Stop and remove everything (containers, networks, volumes)
```bash
docker-compose down -v
```

## Remove Images

### Remove project images
```bash
docker-compose down --rmi all
```

### Remove specific images
```bash
docker rmi teb-arf-case-study-stt
docker rmi teb-arf-case-study-rag
docker rmi teb-arf-case-study-gateway
```

### Remove all project images at once
```bash
docker rmi teb-arf-case-study-stt teb-arf-case-study-rag teb-arf-case-study-gateway
```

## Clean Up Volumes

### Remove volumes (this deletes cached models!)
```bash
docker-compose down -v
```

### Remove specific volumes
```bash
docker volume rm teb-arf-case-study_whisper-models
docker volume rm teb-arf-case-study_embeddings-models
```

## Complete Cleanup

### Stop everything and remove all resources
```bash
# Stop and remove containers, networks, and volumes
docker-compose down -v

# Remove all project images
docker rmi teb-arf-case-study-stt teb-arf-case-study-rag teb-arf-case-study-gateway
```

### Nuclear option - Remove everything Docker-related (use with caution!)
```bash
# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune

# Remove all unused networks
docker network prune
```

## Quick Reference

| Command | What it does |
|---------|-------------|
| `docker-compose stop` | Stop containers (can restart with `docker-compose start`) |
| `docker-compose down` | Stop and remove containers + networks |
| `docker-compose down -v` | Stop and remove containers + networks + volumes |
| `docker-compose down --rmi all` | Stop and remove containers + images |
| `docker-compose ps` | List running containers |
| `docker ps -a` | List all containers (running and stopped) |
| `docker images` | List all images |
| `docker volume ls` | List all volumes |

## Common Scenarios

### Just restart services
```bash
docker-compose restart
```

### Stop services but keep everything for later
```bash
docker-compose stop
# Later: docker-compose start
```

### Clean start (remove containers, keep images and volumes)
```bash
docker-compose down
docker-compose up -d
```

### Fresh start (remove everything including cached models)
```bash
docker-compose down -v --rmi all
docker-compose up --build
```

