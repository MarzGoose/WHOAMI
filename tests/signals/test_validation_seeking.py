from datetime import datetime, timezone
from sources.base import Message
from signals.validation_seeking import detect_validation_seeking


def _msg(content, sender="human"):
    return Message(
        source="claude", source_id="x", sender=sender,
        timestamp=datetime.now(timezone.utc),
        content=content, thread_id="t1",
    )


def test_no_signals_below_threshold():
    messages = [_msg("How do I install Python?") for _ in range(50)]
    assert detect_validation_seeking(messages) == []


def test_detects_right_question():
    msgs = [_msg("That's the correct approach right?")] * 10
    msgs += [_msg("How do I install Python?")] * 90
    result = detect_validation_seeking(msgs)
    assert len(result) == 1
    assert result[0].signal_type == "VALIDATION_SEEKING"


def test_detects_does_that_make_sense():
    msgs = [_msg("I'm thinking we should refactor this, does that make sense?")] * 8
    msgs += [_msg("Show me how to do it.")] * 92
    result = detect_validation_seeking(msgs)
    assert len(result) == 1


def test_assistant_messages_ignored():
    # 2 human validation messages out of 100 human = 2% < 3% threshold
    # 50 assistant validation messages should not inflate the count
    msgs = [_msg("Is that right?", sender="human")] * 2
    msgs += [_msg("Yes, that's right! Right? Does that make sense?", sender="assistant")] * 50
    msgs += [_msg("How do I fix this?", sender="human")] * 98
    result = detect_validation_seeking(msgs)
    assert result == []


def test_metadata_contains_rate():
    msgs = [_msg("Am I overthinking this?")] * 6
    msgs += [_msg("Help me with Python.")] * 94
    result = detect_validation_seeking(msgs)
    assert len(result) == 1
    assert "overall_rate" in result[0].metadata
    assert result[0].metadata["overall_rate"] >= 0.03
