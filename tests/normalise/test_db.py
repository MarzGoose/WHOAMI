import sqlite3
import tempfile
import os
from datetime import datetime, timezone
from sources.base import Message, Transaction
from normalise.db import init_db, insert_messages, insert_transactions, fetch_messages

def test_init_creates_tables():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        conn = init_db(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "messages" in tables
        assert "transactions" in tables
        assert "signals" in tables
    finally:
        os.unlink(db_path)

def test_insert_and_fetch_messages():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        conn = init_db(db_path)
        msgs = [
            Message(
                source="claude",
                source_id="m1",
                timestamp=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                sender="human",
                content="I never buy things on impulse",
                thread_id="conv1",
            )
        ]
        insert_messages(conn, msgs)
        fetched = fetch_messages(conn)
        assert len(fetched) == 1
        assert fetched[0].content == "I never buy things on impulse"
    finally:
        os.unlink(db_path)
