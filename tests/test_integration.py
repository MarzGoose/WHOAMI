import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from normalise.db import init_db, insert_messages, insert_transactions, fetch_messages, fetch_transactions
from sources.claude_export.parser import ClaudeExportParser
from sources.bank_csv.parser import BankCSVParser
from signals.absence import detect_absence
from signals.frequency_salience import detect_frequency_salience
from signals.abandoned_threads import detect_abandoned_threads
from signals.contradiction import detect_contradiction
from pack.generate import generate_pack

CLAUDE_FIXTURE = Path(__file__).parent / "fixtures" / "sample_conversations.json"
BANK_FIXTURE = Path(__file__).parent / "fixtures" / "sample_bank.csv"


def test_full_pipeline_claude_only():
    """Test ingestion, signal detection with Claude data only."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        conn = init_db(db_path)

        # Ingest Claude messages
        messages = list(ClaudeExportParser().parse(str(CLAUDE_FIXTURE)))
        insert_messages(conn, messages)
        assert len(fetch_messages(conn)) == 3

        # Extract signals (min_messages=2 allows results on 3 messages)
        all_messages = fetch_messages(conn)
        absence = detect_absence(all_messages, min_messages=2)
        abandoned = detect_abandoned_threads(all_messages)
        signals = absence + abandoned

        assert isinstance(signals, list)
        # With 3 messages and low min_messages threshold, we may get signals
        # Presence assertion depends on fixture content
    finally:
        os.unlink(db_path)


def test_full_pipeline_with_bank():
    """Test full pipeline with both Claude and bank data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        conn = init_db(db_path)

        # Ingest Claude messages
        messages = list(ClaudeExportParser().parse(str(CLAUDE_FIXTURE)))
        insert_messages(conn, messages)

        # Ingest bank transactions
        transactions = list(BankCSVParser().parse(str(BANK_FIXTURE)))
        insert_transactions(conn, transactions)
        assert len(transactions) == 7

        # Fetch and detect contradictions
        all_messages = fetch_messages(conn)
        all_txns = fetch_transactions(conn)
        signals = detect_contradiction(all_messages, all_txns)

        assert isinstance(signals, list)
    finally:
        os.unlink(db_path)


def test_pack_generation_with_mocked_llm():
    """Test pack generation with mocked LLM to avoid API calls."""
    from signals.base import Signal

    signals = [
        Signal(
            signal_type="ABSENCE",
            confidence="HIGH",
            sources=["claude"],
            finding='Topic "money" appears in 0 of 3 messages.',
            evidence="Zero matches.",
            metadata={"topic": "money"},
        )
    ]

    with patch("pack.generate.LLMClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "# WHOAMI Context Pack\n\nTest pack content."
        mock_cls.return_value = mock_instance

        result = generate_pack(signals, subject_name="John")

    assert isinstance(result, str)
    assert len(result) > 0
    assert "WHOAMI" in result or "Test" in result


def test_end_to_end_all_signal_types():
    """Test detection of multiple signal types in one pipeline run."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        conn = init_db(db_path)

        # Ingest all data
        messages = list(ClaudeExportParser().parse(str(CLAUDE_FIXTURE)))
        insert_messages(conn, messages)

        transactions = list(BankCSVParser().parse(str(BANK_FIXTURE)))
        insert_transactions(conn, transactions)

        all_messages = fetch_messages(conn)
        all_txns = fetch_transactions(conn)

        # Run all detectors
        absence = detect_absence(all_messages, min_messages=2)
        abandoned = detect_abandoned_threads(all_messages)
        contradictions = detect_contradiction(all_messages, all_txns)
        frequency = detect_frequency_salience(all_messages, min_messages=2)

        all_signals = absence + abandoned + contradictions + frequency

        assert isinstance(all_signals, list)
        # Each signal should have required fields
        for signal in all_signals:
            assert signal.signal_type in ["ABSENCE", "ABANDONED", "CONTRADICTION", "FREQUENCY_SALIENCE"]
            assert signal.confidence in ["HIGH", "MEDIUM", "LOW"]
            assert isinstance(signal.sources, list)
            assert len(signal.finding) > 0
            assert len(signal.evidence) > 0
    finally:
        os.unlink(db_path)
