from sources.base import Message
from signals.base import Signal
from signals.domains import LIFE_DOMAINS


def detect_absence(messages: list[Message], min_messages: int = 20) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    if len(human_messages) < min_messages:
        return []

    sources = list({m.source for m in messages})
    claude_only = sources == ["claude"]

    total = len(human_messages)
    signals = []

    for domain, domain_def in LIFE_DOMAINS.items():
        keywords = domain_def["keywords"]
        description = domain_def["description"]
        mentions = sum(1 for m in human_messages
                       if any(kw in m.content.lower() for kw in keywords))
        rate = mentions / total

        if rate == 0:
            confidence = "HIGH"
        elif rate < 0.02:
            confidence = "MEDIUM"
        else:
            continue

        if claude_only:
            finding = (
                f'"{domain}" ({description}) never raised with AI assistant '
                f'across {total} messages ({rate:.1%}).'
            )
            evidence = (
                f"Keywords scanned: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}. "
                f"{mentions} matches across {total} human messages. "
                f"Note: absence from AI conversations reflects what the user does not bring to AI, "
                f"not necessarily absence from life."
            )
        else:
            finding = (
                f'Topic "{domain}" ({description}) appears in {mentions} of {total} messages ({rate:.1%}).'
            )
            evidence = (
                f"Keywords scanned: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}. "
                f"{mentions} matches across {total} human messages across sources: {', '.join(sources)}."
            )

        signals.append(Signal(
            signal_type="ABSENCE",
            confidence=confidence,
            sources=sources,
            finding=finding,
            evidence=evidence,
            metadata={
                "topic": domain,
                "mention_count": mentions,
                "message_total": total,
                "claude_only": claude_only,
                "data_quality": "marginal" if claude_only else "sufficient",
            },
        ))

    return signals
