"""One-off: process all pending embedding_jobs (same as embedding_worker)."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from sqlalchemy import asc  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import EmbeddingJob  # noqa: E402
from app.services.semantic_pipeline import SemanticPipelineService, prewarm_runtime  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0, help="0 = no limit; else stop after N jobs")
    args = ap.parse_args()
    print("[drain] Prewarm BGE/Qdrant...", flush=True)
    prewarm_runtime()
    n = 0
    while True:
        if args.max and n >= args.max:
            break
        db = SessionLocal()
        j = (
            db.query(EmbeddingJob)
            .filter(EmbeddingJob.status == "pending")
            .order_by(asc(EmbeddingJob.created_at))
            .first()
        )
        if not j:
            db.close()
            break
        jid = j.id
        db.close()
        SemanticPipelineService.process_job(jid)
        n += 1
        if n % 30 == 0 or n <= 3:
            print(f"[drain] processed {n} jobs", flush=True)
    print(f"[drain] DONE total {n}", flush=True)


if __name__ == "__main__":
    main()
