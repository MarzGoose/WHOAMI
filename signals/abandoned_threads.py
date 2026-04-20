from collections import defaultdict
from sources.base import Message
from signals.base import Signal

# Intent phrases that suggest a project or plan being started
INTENT_PHRASES = [
    "i want to", "i'm going to", "i plan to", "i was thinking about",
    "i should", "i need to start", "i've been meaning to",
    "i was considering", "i might", "thinking of starting",
    "want to learn", "want to try", "want to build",
]


def detect_abandoned_threads(messages: list[Message]) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]

    # Find messages containing intent phrases
    intent_messages = [
        m for m in human_messages
        if any(phrase in m.content.lower() for phrase in INTENT_PHRASES)
    ]

    if not intent_messages:
        return []

    # For each intent message, extract a short topic summary (first 6 words after intent phrase)
    def extract_topic(content: str) -> str:
        content_lower = content.lower()
        for phrase in INTENT_PHRASES:
            idx = content_lower.find(phrase)
            if idx != -1:
                after = content[idx + len(phrase):].strip()
                words = after.split()[:6]
                return " ".join(words).rstrip(".,!?")
        return content[:40]

    _STOP = {"to", "a", "an", "the", "how", "what", "it", "this", "that",
             "my", "i", "me", "and", "or", "of", "in", "on", "at", "up",
             "for", "with", "is", "be", "do", "get", "can", "not", "you"}

    def extract_key_terms(topic: str) -> set[str]:
        words = [w.strip(".,!?") for w in topic.lower().split()]
        meaningful = [w for w in words if w not in _STOP and len(w) > 3]
        return set(meaningful[:3]) if meaningful else set()

    # For each intent message, extract the topic and track which threads mention it
    intent_topics: dict[str, tuple[str, str, set[str]]] = {}  # topic_key -> (topic_text, intent_thread_id, key_terms)

    for m in intent_messages:
        topic = extract_topic(m.content)
        topic_key = topic[:30].lower()
        key_terms = extract_key_terms(topic)
        intent_topics[topic_key] = (topic, m.thread_id, key_terms)

    # Now scan ALL messages to see which threads mention these topics
    topic_threads: dict[str, set[str]] = defaultdict(set)

    for topic_key, (topic_text, intent_thread_id, key_terms) in intent_topics.items():
        if not key_terms:
            continue
        for m in human_messages:
            msg_lower = m.content.lower()
            if any(term in msg_lower for term in key_terms):
                topic_threads[topic_key].add(m.thread_id)

    # Flag topics that appear in only 1 thread
    signals = []
    for topic_key, (topic_text, intent_thread_id, key_terms) in intent_topics.items():
        if len(topic_threads[topic_key]) == 1:
            signals.append(Signal(
                signal_type="ABANDONED",
                confidence="MEDIUM",
                sources=["claude"],
                finding=(
                    f'Intent raised once and never returned to: '
                    f'"{topic_text}"'
                ),
                evidence=(
                    f"Appeared in 1 conversation thread. "
                    f"No subsequent references to this topic found across {len(human_messages)} messages."
                ),
                metadata={"topic": topic_text, "thread_count": 1},
            ))

    return signals
