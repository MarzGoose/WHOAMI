import re
from datetime import datetime, timezone
from typing import Iterator
from sources.base import Transaction, BaseParser

INTERNAL_TRANSFER_MARKERS = ["internal transfer", "transfer to", "transfer from"]

DATE_RE = re.compile(r"<DTPOSTED>\s*(\d{8})")
AMOUNT_RE = re.compile(r"<TRNAMT>\s*([+-]?\d+\.?\d*)")
MEMO_RE = re.compile(r"<MEMO>\s*(.+)")
FITID_RE = re.compile(r"<FITID>\s*(.+)")
TRNTYPE_RE = re.compile(r"<TRNTYPE>\s*(\w+)")
STMTTRN_RE = re.compile(r"<STMTTRN>(.*?)</STMTTRN>", re.DOTALL)

CATEGORY_KEYWORDS = {
    "groceries":    ["woolworths", "coles", "aldi", "iga", "supermarket", "supabarn", "harris farm"],
    "dining":       ["doordash", "ubereats", "menulog", "mcdonald", "kfc", "subway", "cafe", "restaurant", "pizza"],
    "transport":    ["uber", "lime", "opal", "transit", "fuel", "petrol", "parking", "7-eleven"],
    "online_retail":["amazon", "ebay", "marketplace", "aliexpress", "wish"],
    "hardware":     ["bunnings", "hardware", "mitre 10", "total tools"],
    "utilities":    ["electricity", "gas", "water", "internet", "telstra", "optus", "vodafone", "spotify", "netflix"],
    "health":       ["chemist", "pharmacy", "doctor", "medical", "dental", "fitness", "gym"],
    "savings":      ["savings", "maximiser", "term deposit"],
}


def _parse_date(date_str: str) -> datetime:
    return datetime(
        int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]),
        tzinfo=timezone.utc,
    )


def _guess_category(memo: str) -> str:
    lower = memo.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return category
    return ""


def _is_internal_transfer(memo: str) -> bool:
    lower = memo.lower()
    return any(marker in lower for marker in INTERNAL_TRANSFER_MARKERS)


class OFXParser(BaseParser):
    def __init__(self, account_name: str = ""):
        self.account_name = account_name

    def parse(self, path: str) -> Iterator[Transaction]:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()

        account = self.account_name or _infer_account_name(path)

        for block in STMTTRN_RE.finditer(content):
            txn_text = block.group(1)

            date_m = DATE_RE.search(txn_text)
            amount_m = AMOUNT_RE.search(txn_text)
            memo_m = MEMO_RE.search(txn_text)
            fitid_m = FITID_RE.search(txn_text)

            if not (date_m and amount_m and memo_m):
                continue

            memo = memo_m.group(1).strip()
            if _is_internal_transfer(memo):
                continue

            amount = float(amount_m.group(1))
            if amount == 0:
                continue

            source_id = fitid_m.group(1).strip() if fitid_m else f"{date_m.group(1)}-{amount}"

            yield Transaction(
                source="bank",
                source_id=f"{account}:{source_id}",
                timestamp=_parse_date(date_m.group(1)),
                amount=amount,
                description=memo,
                category=_guess_category(memo),
                metadata={"account": account},
            )


def _infer_account_name(path: str) -> str:
    import os
    return os.path.splitext(os.path.basename(path))[0]
