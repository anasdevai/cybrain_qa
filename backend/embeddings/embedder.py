from langchain_huggingface import HuggingFaceEmbeddings
import hashlib
from collections import Counter
from typing import Tuple, List

def get_embedder() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
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
