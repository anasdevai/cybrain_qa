from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE sops ADD CONSTRAINT unique_sop_number UNIQUE (sop_number);"))
        conn.commit()
        print("Unique constraint added successfully.")
    except Exception as e:
        print(f"Error: {e}")
