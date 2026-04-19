from dataclasses import dataclass, field


@dataclass
class Signal:
    signal_type: str   # ABSENCE | CONTRADICTION | FREQUENCY_SALIENCE | TONE_SHIFT | ABANDONED
    confidence: str    # HIGH | MEDIUM | LOW
    sources: list[str]
    finding: str
    evidence: str
    metadata: dict = field(default_factory=dict)
