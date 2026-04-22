import os
import time
from datetime import datetime

from sqlalchemy import asc

from ..database import SessionLocal
from ..models import EmbeddingJob
from .semantic_pipeline import SemanticPipelineService, prewarm_runtime


POLL_INTERVAL_SECONDS = float(os.getenv("EMBEDDING_WORKER_POLL_SECONDS", "0.6"))
IDLE_LOG_INTERVAL_SECONDS = float(os.getenv("EMBEDDING_WORKER_IDLE_LOG_SECONDS", "30"))


def _claim_next_pending_job():
    db = SessionLocal()
    try:
        job = (
            db.query(EmbeddingJob)
            .filter(EmbeddingJob.status == "pending")
            .order_by(asc(EmbeddingJob.created_at))
            .first()
        )
        if not job:
            return None

        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job.id
    finally:
        db.close()


def run_worker_forever() -> None:
    print("[embedding-worker] Starting dedicated embedding worker...")
    prewarm_runtime()
    print("[embedding-worker] Runtime prewarmed; entering polling loop.")

    last_idle_log = 0.0
    while True:
        job_id = _claim_next_pending_job()
        if not job_id:
            now = time.time()
            if now - last_idle_log >= IDLE_LOG_INTERVAL_SECONDS:
                print("[embedding-worker] Idle: no pending embedding jobs.")
                last_idle_log = now
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        print(f"[embedding-worker] Processing job {job_id}")
        try:
            SemanticPipelineService.process_job(job_id)
            print(f"[embedding-worker] Job completed: {job_id}")
        except Exception as exc:
            print(f"[embedding-worker] Job failed: {job_id} ({exc})")


if __name__ == "__main__":
    run_worker_forever()
