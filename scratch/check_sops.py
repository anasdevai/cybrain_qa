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
            # Check for sops
            result = await conn.execute(text("SELECT count(*) FROM sops"))
            count = result.scalar()
            print(f"Number of sops: {count}")
            
            if count > 0:
                result = await conn.execute(text("SELECT id, sop_number, title FROM sops LIMIT 5"))
                for row in result:
                    print(f"SOP: ID={row[0]}, Number={row[1]}, Title={row[2]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
