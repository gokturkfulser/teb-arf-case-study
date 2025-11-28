import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import torch

print("=" * 50)
print("GPU/CUDA Check")
print("=" * 50)
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"Number of GPUs: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
else:
    print("\n⚠️  CUDA not available!")
    print("To use GPU, you need:")
    print("1. NVIDIA GPU with CUDA support")
    print("2. CUDA-enabled PyTorch installation")
    print("\nInstall CUDA PyTorch:")
    print("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")

print("=" * 50)

