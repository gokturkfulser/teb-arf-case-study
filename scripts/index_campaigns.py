import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.rag.service import RAGService
import json
from pathlib import Path as PathLib
from configs.rag_config import config
from shared.models.rag_models import CampaignMetadata

def main():
    print("Loading campaigns...")
    data_path = PathLib(config.data_storage_path)
    campaigns = []
    
    for json_file in data_path.glob("*.json"):
        if json_file.name == "campaigns_summary.json":
            continue
        
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                campaigns.append(CampaignMetadata(**data))
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    print(f"Found {len(campaigns)} campaigns")
    
    if not campaigns:
        print("No campaigns to index!")
        return 1
    
    print("Initializing RAG service...")
    rag_service = RAGService()
    
    print("Indexing campaigns...")
    rag_service.index_campaigns(campaigns)
    
    print(f"\nIndexing completed! Indexed {len(campaigns)} campaigns")
    print(f"Total vectors in index: {rag_service.vector_store.index.ntotal}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

