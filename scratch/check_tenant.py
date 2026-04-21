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
            # Check for sops with tenant_id
            result = await conn.execute(text("SELECT id, tenant_id, sop_number, title FROM sops"))
            for row in result:
                print(f"SOP: ID={row[0]}, TenantID={row[1]}, Number={row[2]}, Title={row[3]}")
                
            # Check if FIXED_TENANT_ID matches
            FIXED_TENANT_ID = "11111111-1111-1111-1111-111111111111"
            print(f"Target FIXED_TENANT_ID: {FIXED_TENANT_ID}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
