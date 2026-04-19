from datetime import datetime, timezone
from sources.base import Message
from signals.abandoned_threads import detect_abandoned_threads

def _msg(content, thread_id="t1", sender="human", day=1):
    return Message(
        source="claude", source_id=f"{thread_id}-{day}",
        sender=sender,
        timestamp=datetime(2024, day if day <= 28 else 1, 1, tzinfo=timezone.utc),
        content=content, thread_id=thread_id,
    )

def test_flags_topic_raised_once_and_dropped():
    messages = (
        [_msg("I want to start learning woodworking", thread_id="conv1")]
        + [_msg("other topics about coding") for _ in range(20)]
    )
    signals = detect_abandoned_threads(messages)
    findings = [s.finding for s in signals]
    assert any("woodworking" in f.lower() or "learn" in f.lower() for f in findings)

def test_does_not_flag_topic_returned_to():
    messages = (
        [_msg("I want to start learning woodworking", thread_id="conv1")]
        + [_msg("more about woodworking progress", thread_id="conv2")]
        + [_msg("my woodworking project is coming along", thread_id="conv3")]
    )
    signals = detect_abandoned_threads(messages)
    # woodworking appears in 3 threads so should NOT be flagged
    findings = " ".join(s.finding.lower() for s in signals)
    assert "woodworking" not in findings

def test_returns_correct_signal_type():
    messages = [_msg("I was thinking about starting a podcast", thread_id="c1")]
    messages += [_msg("other stuff", thread_id=f"c{i}") for i in range(2, 20)]
    signals = detect_abandoned_threads(messages)
    assert all(s.signal_type == "ABANDONED" for s in signals)
