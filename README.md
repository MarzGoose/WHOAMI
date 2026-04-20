# WHOAMI

Empires have been built with your data. Let it now build yours.

It reads your AI conversations, iMessage/SMS history, social media exports, bank transaction exports and more locally — nothing leaves your machine except the final synthesis call to your AI API or local model — and produces a **context pack**: a structured, forensically-grounded identity profile designed to be handed to an AI as context for a WHOAMI interview driven by evidence and not a narrator.

---

## What it detects

WHOAMI looks for signals that are **impossible to self-report accurately** — patterns only visible in the data, not in your narrator's version of yourself:

| Signal type | What it finds |
|---|---|
| **Absence** | Topics that never appear across thousands of messages |
| **Contradiction** | Where your stated identity conflicts with your behaviour |
| **Frequency vs salience** | What recurs constantly but isn't felt as central |
| **Tone shifts** | Same topic, different emotional register across time |
| **Abandoned threads** | What you started and dropped without resolution |
| **Validation-seeking** | Structural patterns of seeking confirmation |
| **Help-seeking distribution** | Whether emotional content is absent from your AI use |

Signals are rated by confidence and data quality. The pack hedges weak signals and refuses synthesis when the evidence isn't there.

---

## Sources (Phase 0)

| Source | How |
|---|---|
| Claude conversations | `conversations.json` from Claude export |
| iMessage | Reads `~/Library/Messages/chat.db` directly (macOS) |
| Bank transactions | OFX export or CSV from your bank |

See [GETTING_YOUR_FILES.md](GETTING_YOUR_FILES.md) for export instructions.

---

## Quickstart

```bash
git clone https://github.com/MarzGoose/WHOAMI
cd WHOAMI
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python cli.py \
  --claude path/to/conversations.json \
  --imessage \
  --ofx path/to/bank.ofx \
  --name "Your Name" \
  --output output/my-pack.md
```

Requires an `ANTHROPIC_API_KEY` environment variable (or pass `--api-key`). The API is used only for the final pack synthesis and LLM-based contradiction extraction.

---

## Output

A markdown context pack — structured for handing directly to an AI:

```
# WHOAMI Context Pack — [Name]
Generated: YYYY-MM-DD
Signals: N | Sources: bank, claude, imessage

## Identity Signals
...

## Patterns Requiring Attention
...

## Open Questions
...

## For the AI Reading This Pack
...
```

A JSON sidecar is written alongside the markdown with raw signal data.

---

## Project status

Phase 0 — core pipeline complete. Parses three source types, detects seven signal categories, generates a calibrated context pack.

Phase 1 planned: Google Takeout, browser history, Apple Health, Spotify, social media exports.

---

## Design principle

> Questions answerable from self-report are already inside the narrator. Questions answered by *data* — frequency, timestamps, what's absent, what's contradicted across two conversations six weeks apart — bypass it.

WHOAMI is built on that distinction. Everything in the signal layer is designed to surface what self-report cannot.
