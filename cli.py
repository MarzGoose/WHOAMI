#!/usr/bin/env python3
"""
WHOAMI — personal context pack generator.
Reads your digital exhaust files and produces an AI-ready context pack.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from normalise.db import (
    init_db, insert_messages, insert_transactions,
    fetch_messages, fetch_transactions,
)
from sources.claude_export.parser import ClaudeExportParser
from sources.bank_csv.parser import BankCSVParser
from signals.absence import detect_absence
from signals.frequency_salience import detect_frequency_salience
from signals.abandoned_threads import detect_abandoned_threads
from signals.tone_shifts import detect_tone_shifts
from signals.contradiction import detect_contradiction
from pack.generate import generate_pack


def run(args):
    db_path = args.db or "db/whoami.db"
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = init_db(db_path)

    # --- Ingest exhaust files ---
    if args.claude:
        print(f"  Parsing Claude export: {args.claude}")
        parser = ClaudeExportParser()
        messages = list(parser.parse(args.claude))
        insert_messages(conn, messages)
        print(f"  Loaded {len(messages)} messages.")

    if args.bank:
        print(f"  Parsing bank CSV: {args.bank}")
        parser = BankCSVParser()
        transactions = list(parser.parse(args.bank))
        insert_transactions(conn, transactions)
        print(f"  Loaded {len(transactions)} transactions.")

    # --- Extract signals ---
    print("\nExtracting signals...")
    all_messages = fetch_messages(conn)
    all_transactions = fetch_transactions(conn)
    signals = []

    absence = detect_absence(all_messages)
    print(f"  Absence: {len(absence)} signals")
    signals.extend(absence)

    freq_sal = detect_frequency_salience(all_messages)
    print(f"  Frequency/salience: {len(freq_sal)} signals")
    signals.extend(freq_sal)

    abandoned = detect_abandoned_threads(all_messages)
    print(f"  Abandoned threads: {len(abandoned)} signals")
    signals.extend(abandoned)

    tone = detect_tone_shifts(all_messages)
    print(f"  Tone shifts: {len(tone)} signals")
    signals.extend(tone)

    if all_transactions:
        contradiction = detect_contradiction(all_messages, all_transactions)
        print(f"  Contradictions: {len(contradiction)} signals")
        signals.extend(contradiction)

    print(f"\nTotal signals: {len(signals)}")

    if not signals:
        print("No signals found. Try adding more exhaust files.")
        sys.exit(0)

    # --- Generate pack ---
    print("\nGenerating context pack...")
    Path("output").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    output_path = args.output or f"output/whoami-pack-{timestamp}.md"

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Use --api-key or set the environment variable.")
        sys.exit(1)

    pack = generate_pack(
        signals,
        subject_name=args.name or "User",
        output_path=output_path,
        api_key=api_key,
    )

    print(f"\nPack written to: {output_path}")
    print(f"JSON sidecar:    {Path(output_path).with_suffix('.json')}")
    print("\n--- PACK PREVIEW (first 500 chars) ---")
    print(pack[:500])
    print("--------------------------------------")


def main():
    parser = argparse.ArgumentParser(
        description="WHOAMI: generate a context pack from your digital exhaust files."
    )
    parser.add_argument("--claude", metavar="PATH", help="Path to conversations.json (Claude export)")
    parser.add_argument("--bank", metavar="PATH", help="Path to bank transactions CSV")
    parser.add_argument("--name", metavar="NAME", help="Your name (used in pack header)", default="User")
    parser.add_argument("--output", metavar="PATH", help="Output path for the context pack (.md)")
    parser.add_argument("--db", metavar="PATH", help="SQLite database path (default: db/whoami.db)")
    parser.add_argument("--api-key", metavar="KEY", help="Anthropic API key (or set ANTHROPIC_API_KEY)")

    args = parser.parse_args()

    if not args.claude and not args.bank:
        parser.print_help()
        print("\nError: provide at least one exhaust file (--claude or --bank).")
        sys.exit(1)

    run(args)


if __name__ == "__main__":
    main()
