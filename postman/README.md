# Postman Collection

## Import

1. Open Postman → Import
2. Select `TEB_ARF_STT_RAG_Integration.postman_collection.json`
3. (Optional) Import `TEB_ARF_Environment.postman_environment.json`

## Endpoints

**Gateway**: Health, Text Query, Voice Query, Transcribe, Scrape, Index

**STT**: Health, Transcribe File, Transcribe Base64, Metrics, Clear Cache

**RAG**: Health, Query, Index

## Usage

1. Start services: `python scripts/run_all_services.py` or `docker-compose up`
2. Import collection and environment
3. Test endpoints

## Variables

- `gateway_url` - http://localhost:8000
- `stt_url` - http://localhost:8001
- `rag_url` - http://localhost:8002

Edit in environment or collection variables.

## Strategy Parameters

### Search Strategies (for queries)
- **`hybrid`** (default): Combines vector and keyword search for best results
- **`vector`**: Semantic similarity search using embeddings
- **`keyword`**: Text-based keyword matching with variation detection

### Chunking Strategies (for indexing)
- **`default`** (default): Title+description as one chunk + semantic chunks from cleaned_text
- **`sliding_window`**: Overlapping fixed-size chunks
- **`semantic`**: Paragraph-based semantic chunks

## Example Requests

### Text Query with Search Strategy
```json
{
    "question": "iphone kampanyası vardı o neydi",
    "k": 3,
    "search_strategy": "hybrid"
}
```

### Voice Query with Search Strategy
```
POST /api/v1/voice-query?search_strategy=hybrid
Form-data: file (audio file)
```

### Index with Chunking Strategy
```json
{
    "chunking_strategy": "default"
}
```

