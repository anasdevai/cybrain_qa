from langchain_huggingface import HuggingFaceEmbeddings
import hashlib
import os
from pathlib import Path
from collections import Counter
from typing import Tuple, List

MODEL_NAME = "BAAI/bge-m3"


def _resolve_hf_cache_dir() -> str:
    """
    Resolve one stable cache path shared by backend/chatbot modules.
    Priority:
    1) HF_HOME
    2) HUGGINGFACE_HUB_CACHE
    3) EMBEDDING_HF_CACHE_DIR
    4) repo-local .hf-cache
    """
    configured = os.getenv("HF_HOME") or os.getenv("HUGGINGFACE_HUB_CACHE") or os.getenv("EMBEDDING_HF_CACHE_DIR")
    if configured:
        cache_dir = Path(configured).expanduser().resolve()
    else:
        cache_dir = (Path(__file__).resolve().parents[2] / ".hf-cache").resolve()

    cache_dir.mkdir(parents=True, exist_ok=True)
    # Keep both vars aligned so all libraries reuse same cache.
    os.environ["HF_HOME"] = str(cache_dir)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(cache_dir / "hub")
    return str(cache_dir)


def _is_model_cached(cache_dir: str, model_name: str) -> bool:
    model_key = model_name.replace("/", "--")
    snapshots_dir = Path(cache_dir) / "hub" / f"models--{model_key}" / "snapshots"
    if not snapshots_dir.exists():
        return False
    return any(p.is_dir() for p in snapshots_dir.iterdir())

def get_embedder() -> HuggingFaceEmbeddings:
    cache_dir = _resolve_hf_cache_dir()
    local_only = _is_model_cached(cache_dir, MODEL_NAME)
    return HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={
            "device": "cpu",
            "cache_folder": cache_dir,
            "local_files_only": local_only,
        },
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 64,
        },
    )

def generate_sparse_vector(text: str) -> Tuple[List[int], List[float]]:
    """
    Fallback python-native sparse vector generator using a hashing trick
    to avoid heavy C++ compilation dependencies like fastembed.
    """
    tokens = text.lower().split()
    counts = Counter(tokens)
    indices = []
    values = []
    for token, count in counts.items():
        # Hash token to a stable 32-bit positive integer index
        idx = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16) % (2**31 - 1)
        indices.append(idx)
        # Use simple Term Frequency (TF) for values
        values.append(float(count))
    return indices, values
