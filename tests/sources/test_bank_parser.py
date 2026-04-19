import pytest
from pathlib import Path
from sources.bank_csv.parser import BankCSVParser

FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample_bank.csv"

def test_parser_yields_transactions():
    parser = BankCSVParser()
    txns = list(parser.parse(str(FIXTURE)))
    assert len(txns) == 7

def test_debit_amounts_are_negative():
    parser = BankCSVParser()
    txns = list(parser.parse(str(FIXTURE)))
    bunnings = [t for t in txns if "BUNNINGS" in t.description]
    assert all(t.amount < 0 for t in bunnings)

def test_credit_amounts_are_positive():
    parser = BankCSVParser()
    txns = list(parser.parse(str(FIXTURE)))
    salary = [t for t in txns if "SALARY" in t.description]
    assert salary[0].amount > 0

def test_source_is_bank():
    parser = BankCSVParser()
    txns = list(parser.parse(str(FIXTURE)))
    assert all(t.source == "bank" for t in txns)

def test_timestamp_is_parsed():
    from datetime import datetime
    parser = BankCSVParser()
    txns = list(parser.parse(str(FIXTURE)))
    assert isinstance(txns[0].timestamp, datetime)
    assert txns[0].timestamp.year == 2024

def test_raises_clear_error_for_unknown_format(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("TransactionID,MysteryColumn,Value\n1,something,50\n")
    parser = BankCSVParser()
    with pytest.raises(ValueError, match="Bank CSV format not recognised"):
        list(parser.parse(str(bad_csv)))

def test_accepts_narration_column_variant(tmp_path):
    # Westpac uses "Narration" instead of "Description"
    csv_content = "Date,Narration,Debit,Credit,Balance\n15/01/2024,BUNNINGS WAREHOUSE,-85.40,,2150.60\n"
    csv_file = tmp_path / "westpac.csv"
    csv_file.write_text(csv_content)
    parser = BankCSVParser()
    txns = list(parser.parse(str(csv_file)))
    assert len(txns) == 1
    assert "BUNNINGS" in txns[0].description
