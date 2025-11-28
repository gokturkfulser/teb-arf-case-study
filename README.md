# TEB ARF STT-RAG Integration

Integration service combining Speech-to-Text (STT) and Retrieval-Augmented Generation (RAG) services.

## Project Structure

```
tebarf-stt-rag-integration/
├── services/
│   ├── stt/
│   ├── rag/
│   └── gateway/
├── shared/
│   ├── models/
│   └── utils/
├── tests/
├── docker/
├── configs/
└── scripts/
```

## Setup

1. Create virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install PyTorch:
   - **For GPU (CUDA 12.1)**: `pip install -r requirements-cuda.txt`
   - **For CPU-only**: `pip install torch torchvision torchaudio`
4. Install other dependencies: `pip install -r requirements.txt`

