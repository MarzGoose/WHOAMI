from datetime import datetime, timezone
from sources.base import Message, Transaction
from signals.contradiction import detect_contradiction

def _msg(content, sender="human"):
    return Message(
        source="claude", source_id="m1", sender=sender,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        content=content, thread_id="t1",
    )

def _txn(description, amount=-50.0, month=1):
    return Transaction(
        source="bank", source_id=f"t{month}",
        timestamp=datetime(2024, month, 15, tzinfo=timezone.utc),
        amount=amount, description=description,
    )

def test_flags_impulse_claim_contradicted_by_late_night_purchases():
    messages = [_msg("I never buy things on impulse, I'm very deliberate")]
    # 8+ late-night hardware purchases = impulse pattern
    transactions = [
        Transaction(
            source="bank", source_id=f"t{i}",
            timestamp=datetime(2024, 1, i+1, 22, 30, tzinfo=timezone.utc),
            amount=-85.0,
            description="BUNNINGS WAREHOUSE",
        )
        for i in range(8)
    ]
    signals = detect_contradiction(messages, transactions)
    assert len(signals) >= 1
    assert signals[0].signal_type == "CONTRADICTION"

def test_no_contradiction_when_spending_matches_claim():
    messages = [_msg("I buy tools all the time, it's a hobby")]
    transactions = [_txn("BUNNINGS WAREHOUSE", month=i) for i in range(1, 6)]
    signals = detect_contradiction(messages, transactions)
    assert len(signals) == 0

def test_detects_frugality_claim_vs_high_spending():
    messages = [_msg("I'm very frugal and careful with money")]
    transactions = (
        [_txn("AMAZON MARKETPLACE", amount=-300.0, month=i) for i in range(1, 7)]
        + [_txn("EBAY PURCHASE", amount=-150.0, month=i) for i in range(1, 5)]
    )
    signals = detect_contradiction(messages, transactions)
    assert len(signals) >= 1
