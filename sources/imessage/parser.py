import re
import sqlite3
from datetime import datetime, timezone
from typing import Iterator
from sources.base import Message, BaseParser

APPLE_EPOCH = 978307200  # Unix timestamp of 2001-01-01 00:00:00 UTC

TAPBACK_PREFIXES = (
    "Reacted ", "Liked ", "Loved ", "Disliked ",
    "Emphasized ", "Laughed at ", "Questioned ",
)


def _apple_ts_to_datetime(ts: int) -> datetime:
    seconds = ts / 1e9 if ts > 1e15 else float(ts)
    return datetime.fromtimestamp(APPLE_EPOCH + seconds, tz=timezone.utc)


def _extract_text(text_field: str | None, attributed_body: bytes | None) -> str | None:
    if text_field:
        return text_field.strip()
    if not attributed_body:
        return None
    match = re.search(rb"\x01\+([\x00-\xff])([\x00-\xff]+)", attributed_body, re.DOTALL)
    if not match:
        return None
    length = match.group(1)[0]
    data = match.group(2)
    # Handle multi-byte length encoding
    if length == 0x81:
        if len(data) < 1:
            return None
        length = data[0]
        data = data[1:]
    elif length == 0x82:
        if len(data) < 2:
            return None
        length = (data[0] << 8) | data[1]
        data = data[2:]
    text = data[:length].decode("utf-8", errors="replace").strip("\x00").strip()
    return text or None


def _is_tapback(text: str) -> bool:
    return any(text.startswith(p) for p in TAPBACK_PREFIXES)


class IMessageParser(BaseParser):
    def __init__(self, db_path: str = "~/Library/Messages/chat.db"):
        import os
        self.db_path = os.path.expanduser(db_path)

    def parse(self, path: str | None = None) -> Iterator[Message]:
        db = path or self.db_path
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT
                m.ROWID        AS msg_id,
                m.text         AS text_field,
                m.attributedBody AS attributed_body,
                m.date         AS date_ts,
                m.is_from_me   AS is_from_me,
                m.item_type    AS item_type,
                h.id           AS handle_id,
                cmj.chat_id    AS chat_id
            FROM message m
            LEFT JOIN handle h ON m.handle_id = h.ROWID
            LEFT JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
            WHERE m.date > 0
              AND m.item_type = 0
            ORDER BY m.date ASC
        """)

        for row in rows:
            text = _extract_text(row["text_field"], row["attributed_body"])
            if not text:
                continue
            if _is_tapback(text):
                continue

            sender = "human" if row["is_from_me"] else (row["handle_id"] or "unknown")
            timestamp = _apple_ts_to_datetime(row["date_ts"])
            thread_id = str(row["chat_id"]) if row["chat_id"] else "unknown"

            yield Message(
                source="imessage",
                source_id=str(row["msg_id"]),
                timestamp=timestamp,
                sender=sender,
                content=text,
                thread_id=thread_id,
                metadata={"handle": row["handle_id"] or ""},
            )

        conn.close()
