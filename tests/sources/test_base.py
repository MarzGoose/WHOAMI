from datetime import datetime, timezone
from sources.base import Message


def test_message_requires_fields():
    msg = Message(
        source="claude",
        source_id="abc123",
        timestamp=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        sender="human",
        content="Hello world",
        thread_id="conv001",
    )
    assert msg.source == "claude"
    assert msg.content == "Hello world"
    assert msg.metadata == {}
