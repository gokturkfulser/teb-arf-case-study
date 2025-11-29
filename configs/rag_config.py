from pydantic import BaseModel, ConfigDict
from typing import List
import os

class RAGConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    cepteteb_base_url: str = os.getenv("CEPTETEB_URL", "https://www.cepteteb.com.tr")
    campaigns_path: str = "/kampanyalar"
    data_storage_path: str = "data/campaigns"
    scrape_delay: float = 1.0
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    vector_similarity_threshold: float = float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", "50.0"))

config = RAGConfig()

