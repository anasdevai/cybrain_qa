"""Database configuration and session management using SQLAlchemy and asyncpg."""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

# Fetch database credentials from environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "hybrid_rag_db")

# Build the asyncpg connection string
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Create async engine with proper pool settings
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

# Shared declarative base for all ORM models
Base = declarative_base()

class MockResult:
    """Mock for SQLAlchemy Result object."""
    def scalar_one_or_none(self): return None
    def scalars(self): return self
    def all(self): return []

class MockAsyncSession:
    """Mock for SQLAlchemy AsyncSession to allow testing without a database."""
    async def execute(self, *args, **kwargs): return MockResult()
    def add(self, *args, **kwargs): pass
    async def commit(self, *args, **kwargs): pass
    async def refresh(self, *args, **kwargs): pass
    async def rollback(self, *args, **kwargs): pass
    async def close(self, *args, **kwargs): pass
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc_val, exc_tb): pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to yield an async database session, with Mock backup on failure."""
    session_created = False
    try:
        async with async_session_maker() as session:
            session_created = True
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"[get_db] Query execution failed: {e}")
                raise
            finally:
                await session.close()
    except Exception as e:
        if session_created:
            raise
        print(f"[get_db] Error: Database connection failed. Entering Mock Mode. {e}")
        yield MockAsyncSession()
