import json
import re
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

# Flat set of all claim keywords for pre-filtering before LLM call
_ALL_CLAIM_KEYWORDS = {kw for _, kws, _, _ in RESTRAINT_CLAIMS for kw in kws}

FIRST_PERSON = ["i am", "i'm", "i've", "i don't", "i never", "i try", "i always",
                "i tend", "i'm not", "im not", "i consider myself", "i'm pretty",
                "i'm quite", "i'm very", "not really", "i wouldn't say"]


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


def _find_self_claim_sentence(msg_content: str, keywords: list[str]) -> str | None:
    """Return verbatim sentence containing a first-person self-claim, or None."""
    sentences = re.split(r'(?<=[.!?])\s+|\n', msg_content)
    for sentence in sentences:
        s_lower = sentence.lower()
        for kw in keywords:
            idx = s_lower.find(kw)
            if idx == -1:
                continue
            window = s_lower[max(0, idx - 60):idx + len(kw) + 30]
            if any(fp in window for fp in FIRST_PERSON):
                return sentence.strip()
    return None


def _extract_claims_llm(human_messages: list[Message], api_key: str) -> list[dict]:
    """Use Claude Haiku to extract self-referential spending/identity claims with verbatim quotes."""
    import anthropic

    # Pre-filter: only pass messages containing a candidate keyword — reduces token cost
    candidates = [
        m for m in human_messages
        if any(kw in m.content.lower() for kw in _ALL_CLAIM_KEYWORDS)
    ]

    if not candidates:
        return []

    sample = candidates[:200]
    numbered = "\n".join(f"[{i + 1}] {m.content}" for i, m in enumerate(sample))

    prompt = f"""You are a forensic analyst reviewing conversation messages to find self-describing financial identity claims.

Find messages where the speaker explicitly describes their own spending behavior or financial identity.

ONLY include first-person present-tense identity claims with clear self-framing:
- "I'm not impulsive with purchases"
- "I'm pretty frugal"
- "I don't really buy much"
- "I'm a minimalist"

DO NOT include:
- Technical or metaphorical uses (e.g. "the system needs to be frugal with memory")
- Statements about other people
- Aspirational statements ("I want to be more frugal")
- Vague mentions without clear first-person identity framing

For each qualifying claim, identify:
- claim_type: one of "impulse", "frugal", or "minimalist"
- verbatim: the exact quote from the message (complete sentence)

Messages:
{numbered}

Respond with JSON only — no explanation, no markdown fences:
{{"claims": [{{"claim_type": "impulse|frugal|minimalist", "verbatim": "exact quote"}}]}}

If no qualifying claims found: {{"claims": []}}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        result = json.loads(raw)
        return result.get("claims", [])
    except Exception:
        return []


def detect_contradiction(
    messages: list[Message],
    transactions: list[Transaction],
    api_key: str | None = None,
) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    signals = []

    # --- Claim detection: LLM path if api_key provided, keyword fallback otherwise ---
    # Maps claim_name -> verbatim quote string
    claims_found: dict[str, str] = {}

    if api_key:
        for c in _extract_claims_llm(human_messages, api_key):
            ctype = c.get("claim_type", "")
            verbatim = c.get("verbatim", "").strip()
            if ctype and verbatim and ctype not in claims_found:
                claims_found[ctype] = verbatim
    else:
        # Keyword fallback: requires first-person window, returns verbatim sentence
        for claim_name, claim_keywords, _, _ in RESTRAINT_CLAIMS:
            for m in human_messages:
                sentence = _find_self_claim_sentence(m.content, claim_keywords)
                if sentence:
                    claims_found[claim_name] = sentence
                    break

    # --- Contradiction check against transaction data ---
    for claim_name, _claim_keywords, spend_category, desc_keywords in RESTRAINT_CLAIMS:
        verbatim = claims_found.get(claim_name)
        if verbatim is None:
            continue

        category_txns = [
            t for t in transactions
            if _matches_category(t, spend_category, desc_keywords) and t.amount < 0
        ]
        late_txns = [t for t in category_txns if _is_late_night(t)]

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
                    f'Verbatim claim: "{verbatim}". '
                    f'Counter-evidence: {len(late_txns)} transactions after 9pm '
                    f'in category "{spend_category}".'
                ),
                metadata={
                    "claim": claim_name,
                    "verbatim": verbatim,
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
                    f'Verbatim claim: "{verbatim}". '
                    f'{len(category_txns)} transactions in "{spend_category}" category.'
                ),
                metadata={
                    "claim": claim_name,
                    "verbatim": verbatim,
                    "transaction_count": len(category_txns),
                    "total_spend": total_spend,
                    "category": spend_category,
                },
            ))

    return signals
