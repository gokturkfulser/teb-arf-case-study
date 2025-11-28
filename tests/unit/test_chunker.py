import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from services.rag.chunker import Chunker
from shared.models.rag_models import CampaignMetadata


class TestChunker:
    def test_init(self):
        chunker = Chunker(chunk_size=300, overlap=50)
        
        assert chunker.chunk_size == 300
        assert chunker.overlap == 50
    
    def test_sliding_window_chunk(self):
        chunker = Chunker(chunk_size=10, overlap=2)
        text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
        
        chunks = chunker.sliding_window_chunk(text, "test-1")
        
        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("campaign_id" in chunk for chunk in chunks)
    
    def test_chunk_campaign(self, sample_campaign):
        chunker = Chunker(chunk_size=300, overlap=50)
        
        chunks = chunker.chunk_campaign(sample_campaign)
        
        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("campaign_id" in chunk for chunk in chunks)
        assert all(chunk["campaign_id"] == sample_campaign.campaign_id for chunk in chunks)
    
    def test_chunk_campaign_empty(self):
        chunker = Chunker()
        empty_campaign = CampaignMetadata(
            campaign_id="empty",
            title="",
            description="",
            cleaned_text=""
        )
        
        chunks = chunker.chunk_campaign(empty_campaign)
        
        assert isinstance(chunks, list)

