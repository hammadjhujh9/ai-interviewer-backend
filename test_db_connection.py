"""Quick DB connection test - run: python test_db_connection.py"""
import os
import sys
from dotenv import load_dotenv

load_dotenv(".env")

# Fix: .env has "DATABASE_URL = " with spaces - strip the value
url = os.getenv("DATABASE_URL", "").strip()
if not url:
    print("ERROR: DATABASE_URL not set in .env")
    sys.exit(1)

print(f"Testing: {url.replace(url.split('@')[0].split('//')[1], '***')}")

try:
    from sqlalchemy import create_engine, text
    engine = create_engine(url, connect_args={"connect_timeout": 10})
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✓ Connection OK")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)
