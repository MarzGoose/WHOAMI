import json
from dateutil.parser import parse as parse_dt
from typing import Iterator
from sources.base import Message, BaseParser


class ClaudeExportParser(BaseParser):
    def parse(self, path: str) -> Iterator[Message]:
        with open(path, encoding="utf-8") as f:
            conversations = json.load(f)

        for conv in conversations:
            thread_id = conv["uuid"]
            conv_name = conv.get("name", "")
            for msg in conv.get("chat_messages", []):
                text = msg.get("text", "").strip()
                if not text:
                    continue
                yield Message(
                    source="claude",
                    source_id=msg["uuid"],
                    timestamp=parse_dt(msg["created_at"]),
                    sender=msg["sender"],
                    content=text,
                    thread_id=thread_id,
                    metadata={"conversation_name": conv_name},
                )
