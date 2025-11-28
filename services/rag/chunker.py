import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import re
from typing import List, Dict
from shared.models.rag_models import CampaignMetadata

class Chunker:
    def __init__(self, chunk_size: int = 300, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def sliding_window_chunk(self, text: str, campaign_id: str) -> List[Dict]:
        """Create sliding window chunks with overlap"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "campaign_id": campaign_id,
                    "chunk_index": len(chunks),
                    "start_pos": i,
                    "end_pos": min(i + self.chunk_size, len(words))
                })
        
        return chunks
    
    def semantic_chunk(self, text: str, campaign_id: str) -> List[Dict]:
        """Create semantic chunks based on sentences and paragraphs"""
        chunks = []
        paragraphs = text.split("\n\n")
        
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_length = len(para.split())
            
            if current_length + para_length > self.chunk_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "campaign_id": campaign_id,
                    "chunk_index": len(chunks),
                    "type": "semantic"
                })
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length
        
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "campaign_id": campaign_id,
                "chunk_index": len(chunks),
                "type": "semantic"
            })
        
        return chunks
    
    def chunk_campaign(self, campaign: CampaignMetadata) -> List[Dict]:
        """Chunk campaign: title+description as 1 chunk, then cleaned_text chunks"""
        chunks = []
        
        title = campaign.title or ""
        description = campaign.description or ""
        
        if title or description:
            title_desc_text = f"{title}\n\n{description}".strip()
            if title_desc_text:
                chunks.append({
                    "text": title_desc_text,
                    "campaign_id": campaign.campaign_id,
                    "title": title,
                    "chunk_index": 0,
                    "type": "title_description"
                })
        
        if campaign.cleaned_text and len(campaign.cleaned_text.strip()) > 50:
            cleaned_text = campaign.cleaned_text.strip()
            
            cleaned_chunks = self.semantic_chunk(cleaned_text, campaign.campaign_id)
            
            if len(cleaned_chunks) == 1 and len(cleaned_text.split()) > self.chunk_size:
                cleaned_chunks = self.sliding_window_chunk(cleaned_text, campaign.campaign_id)
            
            for i, chunk in enumerate(cleaned_chunks, start=len(chunks)):
                chunk_text = chunk.get("text", "")
                if title and title not in chunk_text:
                    chunk_text = f"{title}\n\n{chunk_text}"
                
                chunk["text"] = chunk_text
                chunk["campaign_id"] = campaign.campaign_id
                chunk["title"] = title
                chunk["chunk_index"] = i
                chunks.append(chunk)
        
        if not chunks:
            fallback_text = f"{title}\n\n{description}".strip() if (title or description) else ""
            if fallback_text:
                chunks.append({
                    "text": fallback_text,
                    "campaign_id": campaign.campaign_id,
                    "title": title,
                    "chunk_index": 0,
                    "type": "fallback"
                })
        
        return chunks

