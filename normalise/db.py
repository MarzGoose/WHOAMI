import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from sources.base import Message, Transaction
from signals.base import Signal


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    schema = (Path(__file__).parent / "schema.sql").read_text()
    conn.executescript(schema)
    conn.commit()
    return conn


def insert_messages(conn: sqlite3.Connection, messages: list[Message]) -> None:
    conn.executemany(
        "INSERT INTO messages (source, source_id, timestamp, sender, content, thread_id, metadata) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                m.source, m.source_id, m.timestamp.isoformat(),
                m.sender, m.content, m.thread_id, json.dumps(m.metadata),
            )
            for m in messages
        ],
    )
    conn.commit()


def insert_transactions(conn: sqlite3.Connection, transactions: list[Transaction]) -> None:
    conn.executemany(
        "INSERT INTO transactions (source, source_id, timestamp, amount, description, category, metadata) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                t.source, t.source_id, t.timestamp.isoformat(),
                t.amount, t.description, t.category, json.dumps(t.metadata),
            )
            for t in transactions
        ],
    )
    conn.commit()


def insert_signals(conn: sqlite3.Connection, signals: list[Signal]) -> None:
    conn.executemany(
        "INSERT INTO signals (signal_type, confidence, sources, finding, evidence, metadata, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                s.signal_type, s.confidence, json.dumps(s.sources),
                s.finding, s.evidence, json.dumps(s.metadata),
                datetime.now(timezone.utc).isoformat(),
            )
            for s in signals
        ],
    )
    conn.commit()


def fetch_messages(conn: sqlite3.Connection, source: str | None = None) -> list[Message]:
    from dateutil.parser import parse as parse_dt
    query = "SELECT source, source_id, timestamp, sender, content, thread_id, metadata FROM messages"
    params = ()
    if source:
        query += " WHERE source = ?"
        params = (source,)
    rows = conn.execute(query, params).fetchall()
    return [
        Message(
            source=row[0], source_id=row[1],
            timestamp=parse_dt(row[2]),
            sender=row[3], content=row[4],
            thread_id=row[5], metadata=json.loads(row[6]),
        )
        for row in rows
    ]


def fetch_transactions(conn: sqlite3.Connection) -> list[Transaction]:
    from dateutil.parser import parse as parse_dt
    rows = conn.execute(
        "SELECT source, source_id, timestamp, amount, description, category, metadata FROM transactions"
    ).fetchall()
    return [
        Transaction(
            source=row[0], source_id=row[1],
            timestamp=parse_dt(row[2]),
            amount=row[3], description=row[4],
            category=row[5], metadata=json.loads(row[6]),
        )
        for row in rows
    ]
