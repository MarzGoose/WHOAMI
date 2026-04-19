from datetime import datetime, timezone
from sources.base import Message
from signals.tone_shifts import detect_tone_shifts


def _msg(content, month=1, sender="human"):
    return Message(
        source="claude", source_id=f"m{month}",
        sender=sender,
        timestamp=datetime(2024, month, 1, tzinfo=timezone.utc),
        content=content, thread_id=f"t{month}",
    )


def test_detects_topic_with_shifting_sentiment():
    messages = (
        [_msg("I love my work, it's amazing and fulfilling", month=1) for _ in range(5)]
        + [_msg("work is fine", month=3) for _ in range(2)]
        + [_msg("work is exhausting and draining, terrible experience", month=6) for _ in range(5)]
    )
    signals = detect_tone_shifts(messages)
    assert len(signals) >= 1
    assert any(s.signal_type == "TONE_SHIFT" for s in signals)


def test_no_signal_for_consistent_topic():
    messages = [_msg("work is good today", month=i) for i in range(1, 7)]
    signals = detect_tone_shifts(messages)
    assert len(signals) == 0


def test_uses_only_human_messages():
    messages = (
        [_msg("I love my work so much", month=1, sender="human") for _ in range(5)]
        + [_msg("work is terrible and draining", month=6, sender="assistant") for _ in range(5)]
    )
    signals = detect_tone_shifts(messages)
    # Assistant messages about work should not trigger a tone shift
    assert len(signals) == 0
