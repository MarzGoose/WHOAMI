from sources.base import Message, Transaction
from signals.base import Signal

# Claims that suggest restraint or deliberateness with spending
# Each entry: (claim_name, claim_keywords, category_name, description_keywords)
RESTRAINT_CLAIMS = [
    (
        "impulse",
        ["impulse", "impulsive"],
        "hardware",
        ["bunnings", "hardware", "mitre 10", "total tools"],
    ),
    (
        "frugal",
        ["frugal", "careful with money", "save money", "don't spend much"],
        "online_retail",
        ["amazon", "ebay", "marketplace", "wish.com", "aliexpress"],
    ),
    (
        "minimalist",
        ["minimalist", "don't need much", "don't buy much"],
        "online_retail",
        ["amazon", "ebay", "marketplace", "wish.com", "aliexpress"],
    ),
]

LATE_NIGHT_HOUR_START = 21  # 9pm


def _is_late_night(txn: Transaction) -> bool:
    return txn.timestamp.hour >= LATE_NIGHT_HOUR_START


def _matches_category(txn: Transaction, category: str, description_keywords: list[str]) -> bool:
    """Match a transaction by category field, falling back to description keywords."""
    if txn.category == category:
        return True
    if not txn.category:
        desc = txn.description.lower()
        return any(kw in desc for kw in description_keywords)
    return False


def detect_contradiction(
    messages: list[Message],
    transactions: list[Transaction],
) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    corpus = " ".join(m.content.lower() for m in human_messages)
    signals = []

    for claim_name, claim_keywords, spend_category, desc_keywords in RESTRAINT_CLAIMS:
        claim_found = any(kw in corpus for kw in claim_keywords)
        if not claim_found:
            continue

        # Find transactions that match this category (by field or description fallback)
        category_txns = [
            t for t in transactions
            if _matches_category(t, spend_category, desc_keywords) and t.amount < 0
        ]
        late_txns = [t for t in category_txns if _is_late_night(t)]

        # Contradiction: claim restraint but frequent late-night category spending
        if len(late_txns) >= 5:
            total_spend = abs(sum(t.amount for t in late_txns))
            signals.append(Signal(
                signal_type="CONTRADICTION",
                confidence="HIGH",
                sources=["claude", "bank"],
                finding=(
                    f'States no "{claim_name}" purchasing — '
                    f'{len(late_txns)} late-night {spend_category} transactions '
                    f'recorded (total: ${total_spend:.2f}).'
                ),
                evidence=(
                    f'Claim keywords found: {", ".join(claim_keywords)}. '
                    f'Counter-evidence: {len(late_txns)} transactions after 9pm '
                    f'in category "{spend_category}".'
                ),
                metadata={
                    "claim": claim_name,
                    "late_night_count": len(late_txns),
                    "total_spend": total_spend,
                    "category": spend_category,
                },
            ))
        elif len(category_txns) >= 8:
            total_spend = abs(sum(t.amount for t in category_txns))
            signals.append(Signal(
                signal_type="CONTRADICTION",
                confidence="MEDIUM",
                sources=["claude", "bank"],
                finding=(
                    f'States no "{claim_name}" purchasing — '
                    f'{len(category_txns)} {spend_category} transactions found '
                    f'(total: ${total_spend:.2f}).'
                ),
                evidence=(
                    f'Claim keywords: {", ".join(claim_keywords)}. '
                    f'{len(category_txns)} transactions in "{spend_category}" category.'
                ),
                metadata={
                    "claim": claim_name,
                    "transaction_count": len(category_txns),
                    "total_spend": total_spend,
                    "category": spend_category,
                },
            ))

    return signals
