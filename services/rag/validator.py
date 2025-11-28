import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import re
import logging
from typing import Optional
from shared.models.rag_models import CampaignMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataValidator:
    def validate(self, campaign: CampaignMetadata) -> bool:
        """Validate campaign data"""
        if not campaign.campaign_id or not campaign.campaign_id.strip():
            return False
        
        if not campaign.title or len(campaign.title.strip()) < 3:
            return False
        
        if not campaign.description or len(campaign.description.strip()) < 10:
            return False
        
        return True
    
    def clean(self, campaign: CampaignMetadata) -> CampaignMetadata:
        """Clean and normalize campaign data"""
        campaign.title = self._clean_text(campaign.title)
        campaign.description = self._clean_text(campaign.description)
        
        if campaign.terms:
            campaign.terms = self._clean_text(campaign.terms)
        
        if campaign.benefits:
            campaign.benefits = self._clean_text(campaign.benefits)
        
        if campaign.cleaned_text:
            campaign.cleaned_text = self._clean_text(campaign.cleaned_text)
        
        return campaign
    
    def _clean_text(self, text: str) -> str:
        """Clean text content"""
        if not text:
            return ""
        
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*\n", "\n", text)
        text = text.strip()
        
        return text

