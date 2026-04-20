import re
from sources.base import Message
from signals.base import Signal
from signals.domains import DOMAIN_KEYWORDS

VALIDATION_PATTERNS = [
    r"\bright\?",
    r"does that make sense\??",
    r"am i (over)?thinking",
    r"is that (right|correct|fair|normal|weird|crazy|bad|okay|ok)\?",
    r"make sense\?",
    r"is it just me",
    r"am i (wrong|right|crazy|overthinking|being)",
    r"does that sound",
    r"fair enough\?",
    r"is that (too|a bit|kind of|sort of)",
    r"you know what i mean\?",
    r"do you think (i|that|it)",
    r"was i (wrong|right|being)",
]

TOPIC_KEYWORDS = {k: v for k, v in DOMAIN_KEYWORDS.items()
                  if k in {"work", "money", "family", "relationships", "mental_health", "health", "faith"}}

VALIDATION_RATE_THRESHOLD = 0.03


def _is_validation(text: str) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in VALIDATION_PATTERNS)


def detect_validation_seeking(messages: list[Message]) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    if not human_messages:
        return []

    total = len(human_messages)
    validation_msgs = [m for m in human_messages if _is_validation(m.content)]
    overall_rate = len(validation_msgs) / total

    if overall_rate < VALIDATION_RATE_THRESHOLD:
        return []

    per_topic: dict[str, int] = {}
    topic_totals: dict[str, int] = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        topic_msgs = [m for m in human_messages if any(kw in m.content.lower() for kw in keywords)]
        if len(topic_msgs) < 5:
            continue
        topic_totals[topic] = len(topic_msgs)
        per_topic[topic] = sum(1 for m in topic_msgs if _is_validation(m.content))

    topic_rates = {
        t: per_topic[t] / topic_totals[t]
        for t in per_topic
        if topic_totals[t] > 0
    }

    elevated = {t: r for t, r in topic_rates.items() if r >= overall_rate * 1.5}
    elevated_str = ", ".join(
        f'"{t}" ({r:.0%})' for t, r in sorted(elevated.items(), key=lambda x: -x[1])
    ) if elevated else "no single domain dominant"

    signals = [Signal(
        signal_type="VALIDATION_SEEKING",
        confidence="HIGH" if overall_rate > 0.06 else "MEDIUM",
        sources=["claude"],
        finding=(
            f"Validation-seeking language detected in {len(validation_msgs)} of {total} messages "
            f"({overall_rate:.1%}). Elevated in: {elevated_str}."
        ),
        evidence=(
            f"Patterns matched: questions ending 'right?', 'does that make sense?', "
            f"'am I overthinking', 'is that normal?' and similar. "
            f"Overall rate: {overall_rate:.1%}. "
            f"Per-topic rates: {', '.join(f'{t}={r:.1%}' for t, r in sorted(topic_rates.items(), key=lambda x: -x[1])[:4])}."
        ),
        metadata={
            "overall_rate": overall_rate,
            "validation_count": len(validation_msgs),
            "message_total": total,
            "per_topic_rates": topic_rates,
            "elevated_topics": list(elevated.keys()),
            "effect_size": overall_rate,
            "data_quality": "sufficient",
        },
    )]

    return signals
