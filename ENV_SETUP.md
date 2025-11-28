# Environment Variables Setup

## Required Variables

### For RAG Service (OpenAI Integration)

**`OPENAI_API_KEY`** - **REQUIRED**
- Your OpenAI API key for RAG response generation
- Without this, RAG will fall back to template-based responses (lower quality)
- Get your key from: https://platform.openai.com/api-keys

## Optional Variables

### STT Service

**`WHISPER_DEVICE`** - Optional (default: `cuda` - GPU)
- **Default is `cuda` (GPU)** for best performance
- Set to `cpu` only if no GPU available or having issues
- Example: `WHISPER_DEVICE=cuda` (default, no need to set)

### RAG Service

**`OPENAI_MODEL`** - Optional (default: `gpt-4o-mini`)
- OpenAI model to use for response generation
- Options: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`, etc.
- Note: `gpt-4.1-mini` is an alias for `gpt-4o-mini`
- Example: `OPENAI_MODEL=gpt-4o-mini`

**`CEPTETEB_URL`** - Optional (default: `https://www.cepteteb.com.tr`)
- Base URL for scraping campaigns
- Only change if the website URL changes
- Example: `CEPTETEB_URL=https://www.cepteteb.com.tr`

### Gateway Service (Local Development Only)

**`STT_SERVICE_URL`** - Optional (default: `http://localhost:8001`)
- STT service URL for local development
- Not needed for Docker (set automatically)
- Example: `STT_SERVICE_URL=http://localhost:8001`

**`RAG_SERVICE_URL`** - Optional (default: `http://localhost:8002`)
- RAG service URL for local development
- Not needed for Docker (set automatically)
- Example: `RAG_SERVICE_URL=http://localhost:8002`

## Setup Instructions

1. Copy the example file:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. Adjust other variables as needed (device, model, etc.)

## For Docker

When using Docker Compose, the `.env` file is automatically loaded. Make sure to:
- Set `OPENAI_API_KEY` (required)
- Set `WHISPER_DEVICE=cpu` if you don't have GPU support
- Other variables have sensible defaults

## Notes

- The `.env` file is in `.gitignore` and won't be committed
- Never share your `OPENAI_API_KEY` publicly
- For production, use Docker secrets or environment variable injection

