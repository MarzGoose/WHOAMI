from sources.base import Message
from signals.base import Signal
from signals.domains import DOMAIN_KEYWORDS

TRACKED_TOPICS = {
    k: v for k, v in DOMAIN_KEYWORDS.items()
    if k in {"work", "money", "health", "family", "relationships", "mental_health"}
}

SALIENCE_MARKERS = [
    "important", "central", "core", "fundamental", "primary",
    "love", "passion", "care about", "focus",
]

SALIENCE_SUPPRESS_RATE = 0.10


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

        def _salience_near_topic(msg: Message) -> bool:
            for sentence in msg.content.replace("!", ".").replace("?", ".").split("."):
                s = sentence.lower()
                if any(kw in s for kw in keywords) and any(mk in s for mk in SALIENCE_MARKERS):
                    return True
            return False

        salience_count = sum(1 for m in topic_messages if _salience_near_topic(m))
        if salience_count / len(topic_messages) >= SALIENCE_SUPPRESS_RATE:
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
                f"Salience markers checked in same sentence — none found in >{SALIENCE_SUPPRESS_RATE:.0%} of topic messages."
            ),
            metadata={
                "topic": topic,
                "frequency": frequency,
                "mention_count": len(topic_messages),
                "message_total": total,
                "effect_size": frequency,
                "data_quality": "sufficient",
            },
        ))

    return signals
