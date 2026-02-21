#!/usr/bin/env python
"""Minimal DB test - no app imports. Run: python test_db_minimal.py"""
import os
import sys
from dotenv import load_dotenv
load_dotenv(".env")

url = os.getenv("DATABASE_URL", "").strip() or "postgresql://admin:spade@localhost:5432/recruiter_ai_db"
url = url + ("?" if "?" not in url else "&") + "connect_timeout=5"

print("Connecting (5s timeout)...")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
