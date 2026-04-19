from sources.base import Message
from signals.base import Signal

LIFE_DOMAINS = {
    "money": ["money", "finance", "finances", "budget", "savings", "debt", "income",
              "salary", "bank", "spend", "spending", "cost", "afford", "expensive"],
    "family": ["family", "mum", "mom", "dad", "father", "mother", "sister", "brother",
               "parent", "parents", "child", "children", "kids"],
    "relationships": ["relationship", "partner", "girlfriend", "boyfriend", "wife", "husband",
                      "marriage", "dating", "love", "lonely", "friend", "friendship"],
    "health": ["health", "sick", "illness", "doctor", "medication", "pain", "body",
               "sleep", "diet", "exercise", "mental health", "anxiety", "depression"],
    "work": ["work", "job", "career", "boss", "colleague", "workplace", "employ",
             "salary", "promotion", "fired", "hired", "business"],
    "faith": ["god", "faith", "church", "prayer", "spiritual", "bible", "theology",
              "belief", "worship", "religion"],
    "future": ["future", "goal", "plan", "dream", "ambition", "hope", "retire",
               "five years", "someday", "eventually"],
    "past": ["regret", "mistake", "wish i had", "should have", "used to", "back then",
             "childhood", "grew up"],
}


def detect_absence(messages: list[Message], min_messages: int = 20) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    if len(human_messages) < min_messages:
        return []

    total = len(human_messages)
    signals = []

    for domain, keywords in LIFE_DOMAINS.items():
        mentions = sum(1 for m in human_messages
                       if any(kw in m.content.lower() for kw in keywords))
        rate = mentions / total

        if rate == 0:
            confidence = "HIGH"
        elif rate < 0.02:
            confidence = "MEDIUM"
        else:
            continue

        signals.append(Signal(
            signal_type="ABSENCE",
            confidence=confidence,
            sources=["claude"],
            finding=f'Topic "{domain}" appears in {mentions} of {total} messages ({rate:.1%}).',
            evidence=f"Keywords scanned: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}. "
                     f"Zero matches across {total} human messages.",
            metadata={"topic": domain, "mention_count": mentions, "message_total": total},
        ))

    return signals
