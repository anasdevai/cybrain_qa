import asyncio
from database.config import engine, Base
from database.models import User, ChatSession, ChatMessage # ensure models are imported

async def init_db():
    print("Initializing database tables...")
    async with engine.begin() as conn:
        # Check tables
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialization complete.")

if __name__ == "__main__":
    asyncio.run(init_db())
