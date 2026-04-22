from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

app_dir = Path(__file__).resolve().parent
backend_dir = app_dir.parent
project_dir = backend_dir.parent

# Prefer the backend-local env file, but still support a repo-root .env.
for env_path in (backend_dir / ".env", project_dir / ".env"):
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured. Set it in backend/.env or the environment.")
if DATABASE_URL.startswith("sqlite"):
    raise RuntimeError("SQLite is not supported for the SOP QA workspace. Configure PostgreSQL instead.")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
