import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.rag.data_pipeline import DataPipeline

def main():
    pipeline = DataPipeline()
    campaigns = pipeline.run()
    
    print(f"\nData collection completed!")
    print(f"Total campaigns collected: {len(campaigns)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

