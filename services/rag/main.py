import sys
import os
from pathlib import Path
import uvicorn

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    uvicorn.run("services.rag.api:app", host="0.0.0.0", port=8002, reload=True)

