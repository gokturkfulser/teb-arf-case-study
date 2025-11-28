# Postman Collection

Postman collection for testing the TEB ARF STT-RAG Integration API.

## Import Instructions

### Import Collection

1. Open Postman
2. Click **Import** button (top left)
3. Select **File** tab
4. Choose `TEB_ARF_STT_RAG_Integration.postman_collection.json`
5. Click **Import**

### Import Environment (Optional)

1. Click **Environments** in left sidebar
2. Click **Import**
3. Choose `TEB_ARF_Environment.postman_environment.json`
4. Click **Import**
5. Select the environment from the dropdown (top right)

## Collection Structure

### Gateway Service
- **Health Check** - Check all services health
- **Text Query** - Query with text input
- **Voice Query** - Query with audio file
- **Transcribe** - Transcribe audio only
- **Scrape Campaigns** - Scrape campaigns from website
- **Index Campaigns** - Scrape and index campaigns

### STT Service
- **Health Check** - Service health status
- **Transcribe File** - Upload audio file
- **Transcribe Base64** - Send base64 encoded audio
- **Get Metrics** - Performance metrics
- **Clear Cache** - Clear transcription cache

### RAG Service
- **Health Check** - Service health and index status
- **Query** - Query campaign data
- **Index Campaigns** - Index campaigns

## Usage

### Prerequisites

1. Start all services:
   ```bash
   python scripts/run_all_services.py
   ```

   Or with Docker:
   ```bash
   docker-compose up
   ```

2. Ensure services are running:
   - Gateway: http://localhost:8000
   - STT: http://localhost:8001
   - RAG: http://localhost:8002

### Testing Workflows

#### 1. Health Check All Services
1. Run **Gateway Service > Health Check**
2. Verify all services are healthy

#### 2. Text Query Workflow
1. Run **Gateway Service > Text Query**
2. Modify the question in the request body
3. Check response for answer and sources

#### 3. Voice Query Workflow
1. Run **Gateway Service > Voice Query**
2. Select an audio file (WAV, MP3, etc.)
3. Check response for transcription and answer

#### 4. Scrape and Index Workflow
1. Run **Gateway Service > Scrape Campaigns**
2. Wait for scraping to complete
3. Run **Gateway Service > Index Campaigns**
4. Wait for indexing to complete
5. Run **Gateway Service > Text Query** to test

#### 5. Direct STT Testing
1. Run **STT Service > Transcribe File**
2. Select an audio file
3. Check transcription result

#### 6. Direct RAG Testing
1. Ensure campaigns are indexed
2. Run **RAG Service > Query**
3. Modify question in request body
4. Check answer and sources

## Environment Variables

The collection uses these variables:
- `gateway_url` - Gateway service URL (default: http://localhost:8000)
- `stt_url` - STT service URL (default: http://localhost:8001)
- `rag_url` - RAG service URL (default: http://localhost:8002)

### Changing URLs

1. Select the environment from dropdown (top right)
2. Click **Edit** (gear icon)
3. Modify the URL values
4. Click **Save**

Or modify directly in the collection:
1. Click collection name
2. Go to **Variables** tab
3. Modify values

## Example Requests

### Text Query
```json
{
    "question": "iphone kampanyası nedir",
    "k": 3
}
```

### Base64 Audio (STT)
```json
{
    "audio_base64": "UklGRiQAAABXQVZFZm10...",
    "filename": "audio.wav"
}
```

### RAG Query
```json
{
    "question": "iphone kampanyası hakkında bilgi ver",
    "k": 5
}
```

## Response Examples

### Text Query Response
```json
{
    "answer": "iPhone kampanyası hakkında...",
    "sources": [
        {
            "campaign_id": "iphone-2024",
            "title": "iPhone Kampanyası",
            "score": 0.95
        }
    ],
    "num_sources": 1
}
```

### Health Check Response
```json
{
    "status": "healthy",
    "stt_service": "healthy",
    "rag_service": {
        "status": "healthy",
        "index_size": 150
    }
}
```

## Tips

1. **First Request**: First query may be slower due to model loading
2. **Indexing**: Indexing can take several minutes depending on campaign count
3. **Audio Files**: Supported formats: WAV, MP3, M4A, FLAC, OGG
4. **Timeout**: Some requests (indexing, scraping) may take 5+ minutes
5. **Error Handling**: Check response status codes and error messages

## Troubleshooting

### Service Not Available
- Ensure services are running
- Check service URLs in environment variables
- Verify ports are not blocked

### 503 Service Unavailable
- Check if STT or RAG services are running
- Verify service health endpoints
- Check service logs

### 400 Bad Request
- Verify request body format
- Check audio file format (for STT)
- Ensure required fields are present

### Empty Index (RAG)
- Run **Index Campaigns** endpoint first
- Wait for indexing to complete
- Check RAG service health for index size

