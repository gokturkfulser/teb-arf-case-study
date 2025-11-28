import uvicorn
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    uvicorn.run("services.gateway.api:app", host="0.0.0.0", port=8000, reload=True)

