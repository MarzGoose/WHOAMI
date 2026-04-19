from datetime import datetime, timezone
from sources.base import Message
from signals.absence import detect_absence

def _msg(content, sender="human"):
    return Message(
        source="claude", source_id="x", sender=sender,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        content=content, thread_id="t1",
    )

def test_flags_domain_with_zero_mentions():
    messages = [_msg("I love programming") for _ in range(20)]
    signals = detect_absence(messages, min_messages=5)
    topics = [s.metadata["topic"] for s in signals]
    assert "money" in topics

def test_does_not_flag_domain_that_appears():
    messages = [_msg("I need to check my bank account and finances")]
    messages += [_msg("random other content") for _ in range(19)]
    signals = detect_absence(messages, min_messages=5)
    topics = [s.metadata["topic"] for s in signals]
    assert "money" not in topics

def test_returns_high_confidence_for_zero_mentions():
    messages = [_msg("coding all day") for _ in range(30)]
    signals = detect_absence(messages, min_messages=5)
    money_signals = [s for s in signals if s.metadata["topic"] == "money"]
    assert money_signals[0].confidence == "HIGH"

def test_skips_assistant_messages():
    # Assistant messages about money should not count as user mentions
    messages = [_msg("Here's how finances work", sender="assistant") for _ in range(5)]
    messages += [_msg("I like coding", sender="human") for _ in range(20)]
    signals = detect_absence(messages, min_messages=5)
    topics = [s.metadata["topic"] for s in signals]
    assert "money" in topics

def test_returns_empty_list_for_small_corpus():
    messages = [_msg("hello")]
    signals = detect_absence(messages, min_messages=10)
    assert signals == []
