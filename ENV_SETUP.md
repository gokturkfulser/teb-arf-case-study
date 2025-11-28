# Environment Variables

## Required

**`OPENAI_API_KEY`** - OpenAI API key for RAG generation
- Get from: https://platform.openai.com/api-keys

## Optional

**`WHISPER_DEVICE`** - `cuda` (default) or `cpu`

**`OPENAI_MODEL`** - `gpt-4.1-mini` (default)

**`CEPTETEB_URL`** - Scraping URL (default: https://www.cepteteb.com.tr)

**`STT_SERVICE_URL`** - Local dev only (default: http://localhost:8001)

**`RAG_SERVICE_URL`** - Local dev only (default: http://localhost:8002)

## Setup

1. Copy `env.example` to `.env`
2. Add your `OPENAI_API_KEY`
3. Adjust other vars if needed

