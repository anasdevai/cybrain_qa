from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, HnswConfigDiff,
    PayloadSchemaType
)

def create_collection(client: QdrantClient, name: str):
    # Check if collection exists first, we avoid recreating to support Upsert
    collections = client.get_collections().collections
    if any(c.name == name for c in collections):
        print(f"Collection '{name}' already exists.")
        return

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE,
        ),
        hnsw_config=HnswConfigDiff(
            m=16,
            ef_construct=100,
            full_scan_threshold=10_000,
        ),
        on_disk_payload=True,
    )
    for field, schema in [
        ("category", PayloadSchemaType.KEYWORD),
        ("source_id", PayloadSchemaType.KEYWORD),
        ("timestamp", PayloadSchemaType.DATETIME),
        ("tags",      PayloadSchemaType.KEYWORD),
    ]:
        client.create_payload_index(
            collection_name=name,
            field_name=field,
            field_schema=schema,
        )
    print(f"Collection '{name}' created with payload indexes.")
