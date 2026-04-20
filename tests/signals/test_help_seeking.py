from datetime import datetime, timezone
from sources.base import Message
from signals.help_seeking import detect_help_seeking


def _msg(content, sender="human"):
    return Message(
        source="claude", source_id="x", sender=sender,
        timestamp=datetime.now(timezone.utc),
        content=content, thread_id="t1",
    )


def test_returns_baseline_signal_for_normal_distribution():
    msgs = [_msg("How do I install Python?")] * 70
    msgs += [_msg("Why does this happen?")] * 20
    msgs += [_msg("I feel really tired today.")] * 5
    msgs += [_msg("Is that right?")] * 5
    result = detect_help_seeking(msgs)
    assert len(result) >= 1
    assert any(s.signal_type == "HELP_SEEKING" for s in result)


def test_flags_emotional_absence():
    msgs = [_msg("How do I fix this error?")] * 95
    msgs += [_msg("What does this mean?")] * 5
    result = detect_help_seeking(msgs)
    subtypes = [s.metadata["signal_subtype"] for s in result]
    assert "emotional_absence" in subtypes


def test_flags_validating_dominance():
    msgs = [_msg("Is that right? Does that make sense?")] * 20
    msgs += [_msg("How do I do this?")] * 80
    result = detect_help_seeking(msgs)
    subtypes = [s.metadata["signal_subtype"] for s in result]
    assert "validating_dominance" in subtypes


def test_assistant_messages_not_classified():
    msgs = [_msg("How do I fix this?", sender="human")] * 30
    msgs += [_msg("I feel anxious today.", sender="assistant")] * 30
    result = detect_help_seeking(msgs)
    for s in result:
        assert s.metadata["message_total"] == 30


def test_too_few_messages_returns_empty():
    msgs = [_msg("How do I do this?")] * 10
    assert detect_help_seeking(msgs) == []


def test_metadata_contains_distribution():
    msgs = [_msg("How do I install Python?")] * 50
    msgs += [_msg("I feel overwhelmed.")] * 10
    msgs += [_msg("Why does this work?")] * 10
    msgs += [_msg("Am I right?")] * 30
    result = detect_help_seeking(msgs)
    assert len(result) >= 1
    assert "distribution" in result[0].metadata
    dist = result[0].metadata["distribution"]
    assert set(dist.keys()) == {"practical", "interpretive", "emotional", "validating"}
