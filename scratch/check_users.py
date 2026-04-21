import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load from backend folder
load_dotenv(dotenv_path="backend/.env")

async def check():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL not found in .env")
        return
        
    print(f"Connecting to: {url}")
    engine = create_async_engine(url.replace("postgresql://", "postgresql+asyncpg://"))
    try:
        async with engine.connect() as conn:
            # Check for users
            result = await conn.execute(text("SELECT count(*) FROM users"))
            count = result.scalar()
            print(f"Number of users: {count}")
            
            if count > 0:
                result = await conn.execute(text("SELECT id, email, username FROM users"))
                for row in result:
                    print(f"User: ID={row[0]}, Email={row[1]}, Username={row[2]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
