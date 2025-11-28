import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import json
import logging
from pathlib import Path
from typing import List
from configs.rag_config import config
from shared.models.rag_models import CampaignMetadata, CampaignData
from services.rag.scraper import CEPTETEBScraper
from services.rag.validator import DataValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self):
        self.scraper = CEPTETEBScraper()
        self.validator = DataValidator()
        self.storage_path = Path(config.data_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def run(self) -> List[CampaignMetadata]:
        """Run complete data collection pipeline"""
        logger.info("Starting data collection pipeline")
        
        campaigns = self.scraper.scrape_campaigns()
        
        validated_campaigns = []
        for campaign in campaigns:
            if self.validator.validate(campaign):
                cleaned = self.validator.clean(campaign)
                validated_campaigns.append(cleaned)
            else:
                logger.warning(f"Campaign {campaign.campaign_id} failed validation")
        
        if validated_campaigns:
            self.save_campaigns(validated_campaigns)
        
        logger.info(f"Pipeline completed: {len(validated_campaigns)} valid campaigns")
        return validated_campaigns
    
    def save_campaigns(self, campaigns: List[CampaignMetadata]):
        """Save campaigns to storage"""
        for campaign in campaigns:
            file_path = self.storage_path / f"{campaign.campaign_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(campaign.model_dump(), f, ensure_ascii=False, indent=2)
        
        summary_path = self.storage_path / "campaigns_summary.json"
        summary = CampaignData(campaigns=campaigns)
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary.model_dump(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(campaigns)} campaigns to {self.storage_path}")

