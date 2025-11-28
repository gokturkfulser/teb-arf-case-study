import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from services.rag.service import RAGService
import json
from pathlib import Path as PathLib
from configs.rag_config import config
from shared.models.rag_models import CampaignMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Service")
rag_service = RAGService()

class QueryRequest(BaseModel):
    question: str
    k: int = 5

class QueryResponse(BaseModel):
    answer: str
    sources: list
    num_sources: int

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query RAG system"""
    try:
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        if rag_service.vector_store.index.ntotal == 0:
            raise HTTPException(status_code=503, detail="No indexed data available. Please index campaigns first.")
        
        result = rag_service.query(request.question.strip(), k=request.k)
        return QueryResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index")
async def index_campaigns():
    """Index campaigns from data directory"""
    try:
        data_path = PathLib(config.data_storage_path)
        campaigns = []
        
        for json_file in data_path.glob("*.json"):
            if json_file.name == "campaigns_summary.json":
                continue
            
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                campaigns.append(CampaignMetadata(**data))
        
        rag_service.index_campaigns(campaigns)
        
        rag_service.vector_store.load_latest_index()
        
        return {
            "status": "indexed", 
            "campaigns": len(campaigns),
            "index_name": rag_service.vector_store.current_index_name,
            "index_size": rag_service.vector_store.index.ntotal
        }
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "index_size": rag_service.vector_store.index.ntotal,
        "index_name": rag_service.vector_store.current_index_name or "none"
    }

