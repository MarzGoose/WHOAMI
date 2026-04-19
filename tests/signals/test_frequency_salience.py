from datetime import datetime, timezone
from sources.base import Message
from signals.frequency_salience import detect_frequency_salience

def _msg(content, sender="human"):
    return Message(
        source="claude", source_id="x", sender=sender,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        content=content, thread_id="t1",
    )

def test_flags_high_frequency_low_salience_topic():
    # "tools" appears constantly but user never says it's important
    messages = [_msg("I went to Bunnings to look at tools") for _ in range(15)]
    messages += [_msg("I care most about my family and faith") for _ in range(5)]
    signals = detect_frequency_salience(messages, min_messages=10)
    topics = [s.metadata["topic"] for s in signals]
    assert "tools" in topics

def test_does_not_flag_topic_described_as_important():
    messages = [_msg("Tools are the most important thing to me") for _ in range(3)]
    messages += [_msg("I love tools, they are central to my life") for _ in range(3)]
    messages += [_msg("random stuff") for _ in range(14)]
    signals = detect_frequency_salience(messages, min_messages=10)
    topics = [s.metadata["topic"] for s in signals]
    assert "tools" not in topics

def test_returns_correct_signal_type():
    messages = [_msg("bought more hardware again") for _ in range(15)]
    messages += [_msg("other stuff") for _ in range(5)]
    signals = detect_frequency_salience(messages, min_messages=10)
    assert all(s.signal_type == "FREQUENCY_SALIENCE" for s in signals)
