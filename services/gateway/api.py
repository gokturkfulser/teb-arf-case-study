import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
import httpx
import logging
import os
from typing import Optional
from services.rag.data_pipeline import DataPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gateway Service")

STT_SERVICE_URL = os.getenv("STT_SERVICE_URL", "http://localhost:8001")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8002")

class TextQueryRequest(BaseModel):
    question: str
    k: int = 5
    search_strategy: str = "hybrid"
    similarity_threshold: Optional[float] = None

class VoiceQueryResponse(BaseModel):
    transcription: str
    answer: str
    sources: list
    num_sources: int

class TextQueryResponse(BaseModel):
    answer: str
    sources: list
    num_sources: int

class TranscribeResponse(BaseModel):
    text: str
    language: str
    processing_time: float

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        import time
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"
        self.time = time
    
    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise HTTPException(status_code=503, detail="Service temporarily unavailable")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = self.time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
    
    def _should_attempt_reset(self):
        if self.last_failure_time:
            return self.time.time() - self.last_failure_time > self.timeout
        return True

stt_breaker = CircuitBreaker()
rag_breaker = CircuitBreaker()

async def call_stt_service(audio_content: bytes, filename: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {"file": (filename, audio_content)}
        response = await client.post(f"{STT_SERVICE_URL}/transcribe", files=files)
        response.raise_for_status()
        return response.json()

async def call_rag_service(question: str, k: int = 5, search_strategy: str = "hybrid", similarity_threshold: Optional[float] = None) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {"question": question, "k": k, "search_strategy": search_strategy}
        if similarity_threshold is not None:
            payload["similarity_threshold"] = similarity_threshold
        response = await client.post(f"{RAG_SERVICE_URL}/query", json=payload)
        response.raise_for_status()
        return response.json()

async def call_rag_index(chunking_strategy: str = "default") -> dict:
    async with httpx.AsyncClient(timeout=300.0) as client:
        payload = {"chunking_strategy": chunking_strategy}
        response = await client.post(f"{RAG_SERVICE_URL}/index", json=payload)
        response.raise_for_status()
        return response.json()

async def check_rag_index() -> dict:
    """Check if RAG service has indexed data"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{RAG_SERVICE_URL}/health")
            response.raise_for_status()
            return response.json()
    except:
        return {"index_size": 0}

async def check_scraped_campaigns() -> bool:
    """Check if campaigns are already scraped"""
    from pathlib import Path
    from configs.rag_config import config
    
    data_path = Path(config.data_storage_path)
    if not data_path.exists():
        return False
    
    json_files = list(data_path.glob("*.json"))
    campaign_files = [f for f in json_files if f.name != "campaigns_summary.json"]
    return len(campaign_files) > 0

async def ensure_index_exists():
    """Ensure index exists, always scrape and create if not"""
    health_data = await check_rag_index()
    index_size = health_data.get("index_size", 0)
    
    if index_size == 0:
        logger.info("No index found, scraping campaigns to get latest data...")
        
        try:
            pipeline = DataPipeline()
            campaigns = pipeline.run()
            logger.info(f"Scraped {len(campaigns)} campaigns")
        except Exception as e:
            logger.error(f"Failed to scrape campaigns: {e}")
            raise HTTPException(status_code=503, detail=f"Failed to scrape campaigns: {str(e)}")
        
        logger.info("Creating index automatically...")
        try:
            await call_rag_index()
            logger.info("Index created successfully")
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            raise HTTPException(status_code=503, detail=f"Failed to create index: {str(e)}")

class VoiceQueryRequest(BaseModel):
    search_strategy: str = "hybrid"

@app.post("/api/v1/voice-query", response_model=VoiceQueryResponse)
async def voice_query(
    file: UploadFile = File(...), 
    search_strategy: str = Query("hybrid", description="Search strategy: vector, keyword, or hybrid")
):
    """Voice query: audio input → text response
    
    Query params:
        search_strategy: "vector", "keyword", or "hybrid" (default: "hybrid")
    """
    try:
        await ensure_index_exists()
        
        valid_strategies = ["vector", "keyword", "hybrid"]
        strategy = search_strategy.lower() if search_strategy else "hybrid"
        if strategy not in valid_strategies:
            raise HTTPException(status_code=400, detail=f"Invalid search_strategy. Must be one of: {valid_strategies}")
        
        content = await file.read()
        
        transcription_result = await stt_breaker.call(call_stt_service, content, file.filename or "audio.wav")
        transcription_text = transcription_result.get("text", "")
        
        if not transcription_text:
            raise HTTPException(status_code=400, detail="No transcription text generated")
        
        rag_result = await rag_breaker.call(call_rag_service, transcription_text, 5, strategy)
        
        return VoiceQueryResponse(
            transcription=transcription_text,
            answer=rag_result.get("answer", ""),
            sources=rag_result.get("sources", []),
            num_sources=rag_result.get("num_sources", 0)
        )
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"Service error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Voice query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/text-query", response_model=TextQueryResponse)
async def text_query(request: TextQueryRequest):
    """Text query: text input → text response"""
    try:
        await ensure_index_exists()
        
        valid_strategies = ["vector", "keyword", "hybrid"]
        strategy = request.search_strategy.lower() if request.search_strategy else "hybrid"
        if strategy not in valid_strategies:
            raise HTTPException(status_code=400, detail=f"Invalid search_strategy. Must be one of: {valid_strategies}")
        
        threshold = request.similarity_threshold if request.similarity_threshold is not None else None
        rag_result = await rag_breaker.call(call_rag_service, request.question, request.k, strategy, threshold)
        
        return TextQueryResponse(
            answer=rag_result.get("answer", ""),
            sources=rag_result.get("sources", []),
            num_sources=rag_result.get("num_sources", 0)
        )
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"Service error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Text query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile = File(...)):
    """Transcribe: audio → text only"""
    try:
        content = await file.read()
        
        transcription_result = await stt_breaker.call(call_stt_service, content, file.filename or "audio.wav")
        
        return TranscribeResponse(
            text=transcription_result.get("text", ""),
            language=transcription_result.get("language", "unknown"),
            processing_time=transcription_result.get("processing_time", 0.0)
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Service error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Transcribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/scrape")
async def scrape_campaigns(background_tasks: BackgroundTasks):
    """Scrape campaigns from CEPTETEB website"""
    try:
        pipeline = DataPipeline()
        campaigns = pipeline.run()
        
        background_tasks.add_task(index_after_scrape)
        
        return {
            "status": "scraped",
            "campaigns": len(campaigns),
            "message": "Campaigns scraped successfully. Indexing in background..."
        }
    except Exception as e:
        logger.error(f"Scraping error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def index_after_scrape(chunking_strategy: str = "default"):
    """Background task to index after scraping"""
    try:
        await call_rag_index(chunking_strategy)
        logger.info("Background indexing completed")
    except Exception as e:
        logger.error(f"Background indexing error: {e}")

class IndexRequest(BaseModel):
    chunking_strategy: str = "default"

@app.post("/api/v1/index")
async def index_campaigns(request: IndexRequest = IndexRequest()):
    """Index campaigns from data directory - always scrapes first to get latest data
    
    Args:
        chunking_strategy: "default", "sliding_window", or "semantic"
    """
    try:
        logger.info("Scraping campaigns to get latest data before indexing...")
        pipeline = DataPipeline()
        campaigns = pipeline.run()
        logger.info(f"Scraped {len(campaigns)} campaigns")
        
        valid_strategies = ["default", "sliding_window", "semantic"]
        strategy = request.chunking_strategy.lower() if request.chunking_strategy else "default"
        if strategy not in valid_strategies:
            raise HTTPException(status_code=400, detail=f"Invalid chunking_strategy. Must be one of: {valid_strategies}")
        
        result = await rag_breaker.call(call_rag_index, strategy)
        return {
            **result,
            "scraped_campaigns": len(campaigns),
            "message": "Campaigns scraped and indexed successfully"
        }
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"Service error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check"""
    stt_healthy = False
    rag_healthy = False
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            stt_response = await client.get(f"{STT_SERVICE_URL}/health")
            stt_healthy = stt_response.status_code == 200
    except:
        pass
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            rag_response = await client.get(f"{RAG_SERVICE_URL}/health")
            rag_healthy = rag_response.status_code == 200
    except:
        pass
    
    return {
        "status": "healthy" if (stt_healthy and rag_healthy) else "degraded",
        "stt_service": "healthy" if stt_healthy else "unavailable",
        "rag_service": "healthy" if rag_healthy else "unavailable"
    }

