import uuid
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from ..models import SOPVersion, KnowledgeChunk

class NormalizationService:
    """
    Service responsible for transforming raw input (Tiptap JSON or Scanned PDF)
    into the canonical Cybrain internal representation.
    """
    
    @staticmethod
    def normalize_to_entities(raw_content: Any, source_type: str = "editor") -> Dict[str, Any]:
        """
        Stub for the unified normalization pipe.
        Takes input and returns a dict ready for database ingestion.
        """
        # FUTURE: Implement Tiptap logic or OCR logic here
        return {
            "title": "Normalized Document",
            "content_json": raw_content if source_type == "editor" else {"type": "doc", "content": []},
            "status": "draft"
        }

class SemanticService:
    """
    Service interface for future BGE-M3 vector indexing.
    """
    
    @staticmethod
    def trigger_reindex(db: Session, entity_id: uuid.UUID, entity_type: str = "sop"):
        """
        Placeholder for semantic indexing trigger.
        Will eventually call a worker or a BGE-M3 microservice.
        """
        # 1. Fetch entity content
        # 2. Split into chunks
        # 3. Generate embeddings
        # 4. Save to KnowledgeChunk table
        print(f"DEBUG: Semantic reindexing triggered for {entity_type} {entity_id}")
        return True
