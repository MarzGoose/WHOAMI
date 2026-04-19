from pathlib import Path
from sources.claude_export.parser import ClaudeExportParser

FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample_conversations.json"

def test_parser_yields_messages():
    parser = ClaudeExportParser()
    messages = list(parser.parse(str(FIXTURE)))
    assert len(messages) == 3  # 2 from conv001, 1 from conv002

def test_parser_sets_correct_source():
    parser = ClaudeExportParser()
    messages = list(parser.parse(str(FIXTURE)))
    assert all(m.source == "claude" for m in messages)

def test_parser_sets_thread_id_to_conversation_uuid():
    parser = ClaudeExportParser()
    messages = list(parser.parse(str(FIXTURE)))
    assert messages[0].thread_id == "conv001"
    assert messages[2].thread_id == "conv002"

def test_parser_preserves_sender():
    parser = ClaudeExportParser()
    messages = list(parser.parse(str(FIXTURE)))
    assert messages[0].sender == "human"
    assert messages[1].sender == "assistant"

def test_parser_stores_conversation_name_in_metadata():
    parser = ClaudeExportParser()
    messages = list(parser.parse(str(FIXTURE)))
    assert messages[0].metadata["conversation_name"] == "Gut health and beans"
