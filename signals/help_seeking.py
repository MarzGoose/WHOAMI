from sources.base import Message
from signals.base import Signal

PRACTICAL_PATTERNS = [
    "how do i", "how to", "how can i", "how does", "what is the", "what are the",
    "can you help", "help me", "show me", "write me", "give me", "create a",
    "fix this", "debug", "error", "not working", "broken", "install",
    "command", "syntax", "code", "script", "function", "setup", "configure",
]

INTERPRETIVE_PATTERNS = [
    "what does this mean", "what does it mean", "why did", "why does", "why is",
    "what do you think", "explain", "understand", "interpret", "curious about",
    "what's the difference", "how does this relate", "what would happen",
    "why would", "what causes",
]

EMOTIONAL_PATTERNS = [
    "i feel", "i'm feeling", "im feeling", "i felt", "i'm struggling", "im struggling",
    "i'm worried", "im worried", "i'm anxious", "im anxious", "i'm stressed",
    "i hate", "i love", "i miss", "i'm scared", "i can't stop", "i keep",
    "it's hard", "its hard", "i don't know what to do", "i need to talk",
    "i've been", "i have been", "i'm going through", "dealing with",
]

VALIDATING_PATTERNS = [
    "right?", "correct?", "does that make sense", "am i", "is that normal",
    "is it just me", "was i", "should i", "would you", "do you think i",
    "am i being", "is this okay", "is this ok", "fair enough", "you know what i mean",
]

CATEGORIES = {
    "practical": PRACTICAL_PATTERNS,
    "interpretive": INTERPRETIVE_PATTERNS,
    "emotional": EMOTIONAL_PATTERNS,
    "validating": VALIDATING_PATTERNS,
}

EMOTIONAL_ABSENCE_THRESHOLD = 0.02
VALIDATING_DOMINANCE_THRESHOLD = 0.15
MIN_MESSAGES = 30


def _classify(text: str) -> str:
    lower = text.lower()
    for category, patterns in CATEGORIES.items():
        if any(p in lower for p in patterns):
            return category
    return "practical"


def detect_help_seeking(messages: list[Message]) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    if len(human_messages) < MIN_MESSAGES:
        return []

    counts: dict[str, int] = {c: 0 for c in CATEGORIES}
    for m in human_messages:
        counts[_classify(m.content)] += 1

    total = len(human_messages)
    rates = {c: counts[c] / total for c in counts}

    signals = []

    if rates["emotional"] < EMOTIONAL_ABSENCE_THRESHOLD:
        signals.append(Signal(
            signal_type="HELP_SEEKING",
            confidence="MEDIUM",
            sources=["claude"],
            finding=(
                f"Emotional content almost entirely absent from AI conversations: "
                f"{counts['emotional']} of {total} messages ({rates['emotional']:.1%}). "
                f"Dominant mode: {max(rates, key=lambda k: rates[k])} ({max(rates.values()):.0%})."
            ),
            evidence=(
                f"Distribution — practical: {rates['practical']:.0%}, "
                f"interpretive: {rates['interpretive']:.0%}, "
                f"emotional: {rates['emotional']:.0%}, "
                f"validating: {rates['validating']:.0%}. "
                f"Emotional threshold: {EMOTIONAL_ABSENCE_THRESHOLD:.0%}."
            ),
            metadata={
                "distribution": rates,
                "counts": counts,
                "message_total": total,
                "signal_subtype": "emotional_absence",
                "effect_size": 1 - rates["emotional"],
                "data_quality": "sufficient",
            },
        ))

    if rates["validating"] >= VALIDATING_DOMINANCE_THRESHOLD:
        signals.append(Signal(
            signal_type="HELP_SEEKING",
            confidence="HIGH" if rates["validating"] > 0.20 else "MEDIUM",
            sources=["claude"],
            finding=(
                f"Validating messages account for {rates['validating']:.0%} of AI conversations "
                f"({counts['validating']} of {total}) — unusually high."
            ),
            evidence=(
                f"Distribution — practical: {rates['practical']:.0%}, "
                f"interpretive: {rates['interpretive']:.0%}, "
                f"emotional: {rates['emotional']:.0%}, "
                f"validating: {rates['validating']:.0%}. "
                f"Threshold for flagging: {VALIDATING_DOMINANCE_THRESHOLD:.0%}."
            ),
            metadata={
                "distribution": rates,
                "counts": counts,
                "message_total": total,
                "signal_subtype": "validating_dominance",
                "effect_size": rates["validating"],
                "data_quality": "sufficient",
            },
        ))

    if not signals:
        signals.append(Signal(
            signal_type="HELP_SEEKING",
            confidence="MEDIUM",
            sources=["claude"],
            finding=(
                f"Help-seeking distribution: practical {rates['practical']:.0%}, "
                f"interpretive {rates['interpretive']:.0%}, "
                f"emotional {rates['emotional']:.0%}, "
                f"validating {rates['validating']:.0%}."
            ),
            evidence=(
                f"Classified {total} human messages. "
                f"No anomalous distribution detected — reported as baseline profile."
            ),
            metadata={
                "distribution": rates,
                "counts": counts,
                "message_total": total,
                "signal_subtype": "baseline",
                "data_quality": "sufficient",
            },
        ))

    return signals
