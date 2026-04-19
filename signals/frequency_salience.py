from sources.base import Message
from signals.base import Signal

TRACKED_TOPICS = {
    "tools": ["tool", "tools", "hardware", "bunnings", "equipment", "gear"],
    "money": ["money", "spend", "spending", "buy", "bought", "purchase", "cost"],
    "work": ["work", "job", "project", "client", "meeting", "deadline"],
    "health": ["health", "sleep", "tired", "energy", "gym", "exercise", "diet"],
    "family": ["mum", "mom", "dad", "family", "kids", "children"],
    "learning": ["learn", "study", "course", "reading", "book", "research"],
}

SALIENCE_MARKERS = [
    "important", "central", "core", "fundamental", "key", "main", "primary",
    "most", "love", "passion", "care about", "matter", "matters", "focus",
]


def detect_frequency_salience(messages: list[Message], min_messages: int = 20) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    if len(human_messages) < min_messages:
        return []

    total = len(human_messages)
    signals = []

    for topic, keywords in TRACKED_TOPICS.items():
        topic_messages = [
            m for m in human_messages
            if any(kw in m.content.lower() for kw in keywords)
        ]
        frequency = len(topic_messages) / total
        if frequency < 0.10:
            continue

        # Check if topic is ever described as important/central
        salience_messages = [
            m for m in topic_messages
            if any(marker in m.content.lower() for marker in SALIENCE_MARKERS)
        ]
        if salience_messages:
            continue

        signals.append(Signal(
            signal_type="FREQUENCY_SALIENCE",
            confidence="HIGH" if frequency > 0.25 else "MEDIUM",
            sources=["claude"],
            finding=(
                f'"{topic}" appears in {len(topic_messages)} of {total} messages '
                f'({frequency:.0%}) but is never described as important or central.'
            ),
            evidence=(
                f"Frequency: {frequency:.0%}. "
                f"Salience markers checked: {', '.join(SALIENCE_MARKERS[:5])}... — none found near topic mentions."
            ),
            metadata={
                "topic": topic,
                "frequency": frequency,
                "mention_count": len(topic_messages),
                "message_total": total,
            },
        ))

    return signals
