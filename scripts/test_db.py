#!/usr/bin/env python3
"""
Test database connection.
Usage: python scripts/test_db.py (run from project root)
       DATABASE_URL can be set in .env or environment
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def test_db_connection() -> bool:
    """Test PostgreSQL connection. Returns True on success."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("FAIL: DATABASE_URL not set in environment or .env")
        return False

    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(database_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("PASS: Database connection successful")
        return True
    except Exception as e:
        print(f"FAIL: Database connection failed - {e}")
        return False


if __name__ == "__main__":
    success = test_db_connection()
    sys.exit(0 if success else 1)
