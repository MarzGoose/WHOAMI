import csv
import hashlib
from datetime import datetime
from typing import Iterator
from sources.base import Transaction, BaseParser


COLUMN_ALIASES = {
    "date": ["date", "transaction date", "trans date", "value date"],
    "description": ["description", "narration", "details", "transaction details", "narrative", "memo"],
    "debit": ["debit", "debit amount", "withdrawals", "withdrawal"],
    "credit": ["credit", "credit amount", "deposits", "deposit"],
    "amount": ["amount", "net amount"],
}


def _detect_layout(headers: list[str]) -> dict[str, str | None]:
    normalised = {h.strip().lower(): h for h in headers}
    mapping = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalised:
                mapping[canonical] = normalised[alias]
                break
        else:
            mapping[canonical] = None

    if not mapping["date"]:
        raise ValueError(
            f"No date column found. Headers: {headers}\n"
            "Expected one of: date, transaction date, trans date, value date"
        )
    if not mapping["description"]:
        raise ValueError(
            f"No description column found. Headers: {headers}\n"
            "Expected one of: description, narration, details, narrative, memo"
        )
    if not mapping["debit"] and not mapping["credit"] and not mapping["amount"]:
        raise ValueError(
            f"No amount column found. Headers: {headers}\n"
            "Expected debit/credit columns or a single 'amount' column"
        )
    return mapping


class BankCSVParser(BaseParser):
    DATE_FORMATS = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d %b %Y"]

    def parse(self, path: str) -> Iterator[Transaction]:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError(f"Bank CSV at {path} appears to be empty.")
            try:
                layout = _detect_layout(list(reader.fieldnames))
            except ValueError as e:
                raise ValueError(f"Bank CSV format not recognised ({path}):\n{e}") from e

            for row in reader:
                timestamp = self._parse_date(row.get(layout["date"] or "", "").strip())
                if timestamp is None:
                    continue

                description = row.get(layout["description"] or "", "").strip()

                if layout["amount"]:
                    raw = row.get(layout["amount"] or "", "").strip().replace(",", "")
                    if not raw:
                        continue
                    amount = float(raw)
                else:
                    debit_raw = row.get(layout["debit"] or "", "").strip().lstrip("-").replace(",", "")
                    credit_raw = row.get(layout["credit"] or "", "").strip().replace(",", "")
                    if debit_raw:
                        amount = -abs(float(debit_raw))
                    elif credit_raw:
                        amount = abs(float(credit_raw))
                    else:
                        continue

                source_id = hashlib.md5(
                    f"{timestamp.isoformat()}{description}{amount}".encode()
                ).hexdigest()[:12]

                yield Transaction(
                    source="bank",
                    source_id=source_id,
                    timestamp=timestamp,
                    amount=amount,
                    description=description,
                    category=self._guess_category(description),
                )

    def _parse_date(self, date_str: str) -> datetime | None:
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def _guess_category(self, description: str) -> str:
        desc = description.upper()
        if any(kw in desc for kw in ["BUNNINGS", "TOOLS", "HARDWARE", "JAYCAR"]):
            return "hardware"
        if any(kw in desc for kw in ["COLES", "WOOLWORTHS", "IGA", "ALDI", "SUPERMARKET"]):
            return "groceries"
        if any(kw in desc for kw in ["NETFLIX", "SPOTIFY", "DISNEY", "AMAZON PRIME"]):
            return "subscriptions"
        if any(kw in desc for kw in ["SALARY", "PAYROLL", "WAGES"]):
            return "income"
        if any(kw in desc for kw in ["AMAZON", "EBAY", "ALIEXPRESS"]):
            return "online_retail"
        return "other"
