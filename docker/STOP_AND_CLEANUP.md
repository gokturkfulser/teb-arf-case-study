# Docker Cleanup

## Stop Services

```bash
docker-compose stop          # Stop containers
docker-compose down          # Stop and remove containers
docker-compose down -v       # Remove volumes too
```

## Remove Images

```bash
docker-compose down --rmi all
```

Or individually:
```bash
docker rmi teb-arf-case-study-stt
docker rmi teb-arf-case-study-rag
docker rmi teb-arf-case-study-gateway
```

## Remove Volumes

```bash
docker-compose down -v
```

Or specific volumes:
```bash
docker volume rm teb-arf-case-study_whisper-models
docker volume rm teb-arf-case-study_embeddings-models
```

## Complete Cleanup

```bash
docker-compose down -v --rmi all
```

## Common Commands

| Command | Description |
|---------|-------------|
| `docker-compose stop` | Stop containers |
| `docker-compose down` | Stop and remove |
| `docker-compose down -v` | Remove volumes |
| `docker-compose logs -f` | View logs |
| `docker-compose ps` | List services |

