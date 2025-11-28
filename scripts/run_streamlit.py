import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
app_path = project_root / "streamlit" / "app.py"

if __name__ == "__main__":
    print("Starting Streamlit app...")
    print(f"App will be available at: http://localhost:8501")
    print("Press Ctrl+C to stop")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.port", "8501",
        "--server.address", "localhost"
    ])

