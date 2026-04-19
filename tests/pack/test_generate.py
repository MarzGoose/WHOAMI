from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from signals.base import Signal
from pack.generate import generate_pack

SAMPLE_SIGNALS = [
    Signal(
        signal_type="ABSENCE",
        confidence="HIGH",
        sources=["claude"],
        finding='Topic "money" appears in 0 of 200 messages (0.0%).',
        evidence="Zero matches across 200 human messages.",
        metadata={"topic": "money"},
    ),
    Signal(
        signal_type="CONTRADICTION",
        confidence="HIGH",
        sources=["claude", "bank"],
        finding="States no impulse purchasing — 8 late-night hardware transactions recorded.",
        evidence="Claim keywords found. 8 transactions after 9pm in hardware category.",
        metadata={"claim": "impulse", "late_night_count": 8},
    ),
]


def test_generate_pack_returns_markdown_string():
    with patch("pack.generate.LLMClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "# WHOAMI Context Pack\n\nTest content here — forensic identity analysis."
        mock_cls.return_value = mock_instance

        result = generate_pack(SAMPLE_SIGNALS, subject_name="John")

    assert isinstance(result, str)
    assert len(result) > 50


def test_generate_pack_includes_signal_count():
    with patch("pack.generate.LLMClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "# WHOAMI Context Pack\n\n2 signals found."
        mock_cls.return_value = mock_instance

        result = generate_pack(SAMPLE_SIGNALS, subject_name="John")

    assert result is not None


def test_generate_pack_writes_json_sidecar(tmp_path):
    with patch("pack.generate.LLMClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "# WHOAMI Context Pack\n\nContent."
        mock_cls.return_value = mock_instance

        output_path = tmp_path / "pack.md"
        generate_pack(SAMPLE_SIGNALS, subject_name="John", output_path=str(output_path))

    assert output_path.exists()
    json_path = output_path.with_suffix(".json")
    assert json_path.exists()
