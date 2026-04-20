import re
from sources.base import Message
from signals.base import Signal
from signals.domains import DOMAIN_KEYWORDS

POSITIVE_WORDS = {
    "love", "amazing", "great", "excellent", "fantastic", "wonderful", "enjoy",
    "happy", "good", "brilliant", "exciting", "fulfilling", "rewarding", "grateful",
    "thankful", "proud", "thriving", "blessed", "inspired", "glad", "pleased",
    "delighted", "content", "hopeful", "optimistic", "energised", "energized",
}
NEGATIVE_WORDS = {
    "hate", "terrible", "awful", "horrible", "dread", "exhausting", "draining",
    "boring", "frustrating", "angry", "depressed", "stuck", "trapped", "miserable",
    "pointless", "meaningless", "struggling", "overwhelmed", "hopeless", "anxious",
    "drained", "defeated", "resentful", "bitter", "lonely", "lost",
}

MIN_NONZERO_RATE = 0.10
DELTA_THRESHOLD = 0.15


def _sentiment_score(text: str) -> float:
    words = set(re.sub(r"[^\w\s]", " ", text.lower()).split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def detect_tone_shifts(messages: list[Message], min_period_messages: int = 3) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    if len(human_messages) < 6:
        return []

    sorted_msgs = sorted(human_messages, key=lambda m: m.timestamp)
    mid = len(sorted_msgs) // 2
    early = sorted_msgs[:mid]
    late = sorted_msgs[mid:]

    signals = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        early_domain = [m for m in early if any(k in m.content.lower() for k in keywords)]
        late_domain = [m for m in late if any(k in m.content.lower() for k in keywords)]

        if len(early_domain) < min_period_messages or len(late_domain) < min_period_messages:
            continue

        all_domain = early_domain + late_domain
        nonzero_rate = sum(1 for m in all_domain if _sentiment_score(m.content) != 0) / len(all_domain)
        if nonzero_rate < MIN_NONZERO_RATE:
            continue

        early_score = sum(_sentiment_score(m.content) for m in early_domain) / len(early_domain)
        late_score = sum(_sentiment_score(m.content) for m in late_domain) / len(late_domain)
        delta = late_score - early_score

        if abs(delta) < DELTA_THRESHOLD:
            continue

        direction = "more negative" if delta < 0 else "more positive"
        data_quality = "sufficient" if nonzero_rate >= 0.20 else "marginal"

        signals.append(Signal(
            signal_type="TONE_SHIFT",
            confidence="HIGH" if abs(delta) > 0.30 else "MEDIUM",
            sources=["claude"],
            finding=(
                f'Tone around "{domain}" has become {direction} over time '
                f'(early score: {early_score:+.2f}, late score: {late_score:+.2f}).'
            ),
            evidence=(
                f"Early period: {len(early_domain)} messages, avg sentiment {early_score:+.2f}. "
                f"Late period: {len(late_domain)} messages, avg sentiment {late_score:+.2f}. "
                f"Delta: {delta:+.2f}. Sentiment coverage: {nonzero_rate:.0%} of domain messages."
            ),
            metadata={
                "domain": domain,
                "early_score": early_score,
                "late_score": late_score,
                "delta": delta,
                "nonzero_rate": nonzero_rate,
                "data_quality": data_quality,
                "effect_size": abs(delta),
                "sample_size": len(all_domain),
            },
        ))

    return signals
