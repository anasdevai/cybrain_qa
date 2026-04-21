import copy
import hashlib
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def chunk_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
        keep_separator=True,
    )
    chunked = []
    for doc in docs:
        splits = splitter.split_documents([doc])
        for i, chunk in enumerate(splits):
            chunk.metadata = copy.deepcopy(doc.metadata)
            chunk.metadata["chunk_index"] = i
            
            # Deterministic ID for updating data in Qdrant later
            raw_id = f"{doc.metadata['source_id']}_chunk_{i}"
            chunk_hash = hashlib.md5(raw_id.encode('utf-8')).hexdigest()
            # Generate a standard UUID format using the hash
            uuid_str = f"{chunk_hash[:8]}-{chunk_hash[8:12]}-{chunk_hash[12:16]}-{chunk_hash[16:20]}-{chunk_hash[20:32]}"
            
            chunk.metadata["qdrant_id"] = uuid_str
            chunk.metadata["chunk_id"] = raw_id
            
        chunked.extend(splits)
    return chunked
