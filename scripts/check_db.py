import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

async def check():
    url = f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    print(f"Attempting to connect to: {url}")
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print("Successfully connected to the database.")
            
            # Check for tables
            result = await conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in result]
            print(f"Found tables: {tables}")
            
    except Exception as e:
        print(f"Error connecting to the database: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
