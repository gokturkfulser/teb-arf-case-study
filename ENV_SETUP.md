# Environment Variables

## Required

**`OPENAI_API_KEY`** - OpenAI API key for RAG generation
- Get from: https://platform.openai.com/api-keys

## Optional

**`WHISPER_DEVICE`** - `cuda` (default) or `cpu`

**`OPENAI_MODEL`** - `gpt-4.1-mini` (default)

**`CEPTETEB_URL`** - Scraping URL (default: https://www.cepteteb.com.tr)

**`VECTOR_SIMILARITY_THRESHOLD`** - Maximum L2 distance for vector search filtering (default: `50.0`)
- Lower values (e.g., `10.0`) = stricter filtering, fewer results
- Higher values (e.g., `100.0`) = more lenient, more results
- Set to `100.0` or higher to effectively disable distance filtering
- Only applies when using `search_strategy: "vector"`

**`STT_SERVICE_URL`** - Local dev only (default: http://localhost:8001)

**`RAG_SERVICE_URL`** - Local dev only (default: http://localhost:8002)

## Setup

1. Copy `env.example` to `.env`
2. Add your `OPENAI_API_KEY`
3. Adjust other vars if needed

