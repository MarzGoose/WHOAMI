# WHOAMI — Product Design Spec
**Date:** 2026-04-19
**Status:** Draft — awaiting user review
**Origin:** WHOAMI forensic identity project, Stream B (behavioural data mining)
**Domain target:** whoami.app

---

## What It Is

WHOAMI is a local desktop application that ingests a user's own data exports — their *exhaust files* — and produces a portable context pack: a structured identity document any AI can consume. It eliminates the friction of the 20–50 question intake interviews that have become standard in AI-assisted coaching, planning, and decision-making.

**Primary pitch (utility):** Skip the interview. Drop your files. Get better AI output.

**Side effect (insight):** The AI sees patterns in your data your narrator would never surface. Users come for the utility. The narrator-bypass happens anyway.

**Power pitch:** "Empires have been built with your data. Let it now build yours."

---

## Nomenclature

**Exhaust files** — internal term for the raw personal data exports a user feeds into WHOAMI (bank CSVs, Claude conversation JSON, Apple Health XML, iMessage database, browser history, Google Takeout ZIP). The term is not marketed. Users who notice it get it. Everyone else just sees "your files."

---

## The Two Problems It Solves

1. **Friction of collection.** The 20–50 question AI intake process is the most-abandoned step in AI-assisted work. Manual data exports are the alternative bottleneck — most people know they should gather this data and never do. WHOAMI reads local sources automatically.

2. **Method of extraction.** Raw data without a methodology is noise. The Signal Extractor applies a 9-method forensic framework so the output is evidence, not a data dump — and the AI interview agenda is set by that evidence, not by what the user thinks is worth discussing.

Solving collection without extraction = a filing cabinet.
Solving extraction without collection = a methodology document.

---

## Architecture — Three Layers

### Layer 1: Data Sources (exhaust files)

All collection is local. No API calls. No cloud. No credential capture.

| Source | Tier | Method |
|--------|------|--------|
| Claude / AI conversation exports | Free | JSON file drop (`conversations.json`) |
| iMessage | Paid | Reads `~/Library/Messages/chat.db` directly |
| Bank records | Paid | CSV drop folder |
| Apple Health | Paid | XML export file |
| Browser history | Paid | Reads local SQLite (Chrome/Safari/Firefox) |
| Google Takeout | Paid | ZIP drop folder — auto-extracted |
| Personal calendar | Paid | ICS / Google Calendar export |

The free tier (Claude/AI conversations) is chosen deliberately: conversation exports are uniquely rich in self-report statements, making them the ideal contradiction-detection partner for behavioural data. Enough to show the mirror works. Not enough to see the full picture.

### Layer 2: Python Core Engine

**Format Detector**
Identifies source type from file content (not just extension — same `.db` extension can be iMessage, browser history, or a different SQLite entirely). Normalises all sources to a common internal schema. This normalisation layer is the real moat — heterogeneous inputs into one coherent structure the AI can reason across is where serious products diverge from toy projects.

**Signal Extractor — 9 Methods**

| # | Method | What It Targets |
|---|--------|----------------|
| 1 | Absence | Topics that never appear across all sources |
| 2 | Contradiction | Self-report statements vs behavioural data. Statements mined automatically from conversation/message history — the narrator's own words used as evidence against the narrator's behaviour |
| 3 | Frequency vs salience | What recurs constantly but isn't felt as central |
| 4 | Tone shifts | Same topic, different emotional register across time or by recipient |
| 5 | Abandoned threads | Started and dropped without explanation — subscriptions, projects, conversations |
| 6 | Cross-stream convergence | When independent sources agree: high confidence. When they conflict: the conflict is the finding |
| 7 | Linguistic distancing | Passive voice, third-person self-reference, heavy hedging around specific topics |
| 8 | Baseline anomalies | Deviation from the subject's own established pattern — not unusual in general, unusual for them |
| 9 | Temporal clustering | Behaviour changes around dates. Three sub-layers: public/cultural calendar (auto-loaded via `holidays`/`workalendar`), personal calendar (from user's own calendar data), emergent clustering (anomalies around unknown dates, flagged for user context) |

Each signal is output with: signal type, confidence level (High/Medium/Low), sources involved, and a plain-language description.

**Expert Toggle Panel**
Accessible but not default. Users can enable/disable signal types and data sources before running. Tool warns when high-signal categories (Absence, Contradiction, Cross-stream convergence) are toggled off.

### Layer 3: Output + Analysis

**Default — Context Pack**
Two artefacts produced locally:
1. A human-readable Markdown identity document (~5,000–20,000 tokens) — structured, AI-ready, designed to be pasted directly into Claude, ChatGPT, or any AI to replace the intake interview
2. A local vector store (Chroma or LanceDB) for downstream AI to query for detail

No interpretation baked in — raw evidence only. AI-agnostic from day one.

**Optional — In-app Analysis**
User pastes an API key (Claude/GPT/Gemini). Analysis runs inside the app against the context pack.

**Advanced — Local Model**
Ollama integration. 100% offline. For privacy-maximalists.

**One-click — Interview Agenda**
Generates targeted questions derived from the signals. Data-first → interview-second. The AI interview agenda is set by cold evidence, not by what the user thinks is worth discussing.

---

## UI Design

### Philosophy: Minimal
Almost nothing on screen. One number (signals found from last run). One button (Run). Everything else one click away. Feels like a serious instrument, not a wellness app.

### Key Screens

**Main screen:** Signal count from last run, Run button, quiet links to Sources and Expert mode.

**Results screen:** Three-panel layout.
- Left: Signal type navigation with counts (filter by type or source)
- Centre: Signal feed — cards colour-coded by type, each showing the finding, the evidence, and which sources it spans
- Right: Action panel — Copy context pack, Open in AI, Generate interview agenda, Export (.md / .json)

**Sources screen:** Connected source list with status. Drag-drop zone for exhaust files. One-time setup for local database paths (iMessage, browser history).

**Expert mode:** Toggle panel for signal types and sources. Confidence threshold slider. Warning system for suppressed high-signal categories.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Desktop shell | Electron (cross-platform: macOS, Windows, Linux) |
| Core engine | Python 3.11+ |
| Data parsing | pandas, sqlite3, xml.etree, json (stdlib), mbox (Gmail) |
| NLP (linguistic distancing) | spaCy |
| Calendar events | `holidays` / `workalendar` libraries |
| Database | SQLite for normalised schema |
| Vector store | Chroma (simpler) or LanceDB (more performant) |
| LLM interface | Anthropic Claude API (`anthropic` Python SDK) for normalisation assistance |
| LLM decisions | Structured JSON logs — all entity resolution and deduplication decisions auditable |
| IPC bridge | Electron ↔ Python subprocess |
| CLI | Python core run standalone — no Electron needed |

---

## Business Model

**Free tier:** Claude / AI conversation history only.

**Paid tier:** Full multi-source combination — the convergence is where the real signal lives.

**Freemium conversion triggers (ranked):**
1. Staleness — free = one snapshot; paid = auto-refresh as new exhaust files land
2. Export automation — paid connectors fetch files on schedule; free requires manual drop
3. Source-count ceiling — insight density is non-linear; users feel the ceiling after their first pack
4. Output specialisation — purpose-built packs for financial planning, career decisions, therapy intake

**Open core:**
- CLI + parsers: open source on GitHub (prior art, developer credibility, community contributions to parsers)
- Desktop app: proprietary paid product

Two marketing channels: GitHub for developers, TikTok/Instagram for everyone else. One codebase.

---

## Ship Strategy

**Phase 0 — Personal prototype (weeks 1–10, part-time):**
Single user (John). Python scripts only. No UI. No installer. Target: Claude conversations.json → Markdown context pack → paste into fresh Claude session → evaluate calibration improvement. Success criterion: pack surfaces at least three patterns not consciously known or reported. This build IS the WHOAMI Stream B instrument — personal and product goals share the same codebase.

**Phase 1 — Core expansion:**
Add iMessage, bank CSV, Apple Health, Google Takeout. Signal extractor reaches full 9-method framework. Still single-user.

**Phase 2 — CLI (conditional on Phase 0 delivering):**
Python CLI. Push to GitHub. Establishes prior art. 3–5 external test users. Prove willingness-to-pay before investing in UI.

**Phase 3 — Desktop app:**
Electron shell. Minimal UI. Freemium launch. Trademark filing (USPTO + IP Australia, class 042).

---

## Repository Layout

```
whoami/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── sources/                     # Layer 1: one module per source
│   ├── claude_export/
│   ├── google_takeout/
│   ├── bank_csv/
│   ├── imessage/
│   ├── apple_health/
│   └── browser_history/
├── normalise/                   # Layer 2: schema and merging
│   ├── schema.sql
│   ├── entity_resolution.py
│   └── deduplication.py
├── pack/                        # Layer 3: context pack generation
│   ├── generate_markdown.py
│   └── build_vector_store.py
├── db/                          # SQLite files (gitignored)
├── exports/                     # raw exhaust files (gitignored)
├── output/                      # generated context packs (gitignored)
├── logs/                        # LLM-decision audit logs (gitignored)
└── handovers/                   # session handover notes
```

---

## Operating Principles for Development Sessions

1. Every source gets its own ingestion module. Never fold two parsers together.
2. Schema changes require a migration script. No silent field renames.
3. All LLM-assisted decisions (entity resolution, deduplication, semantic tagging) are logged in structured JSON for audit.
4. Don't optimise Phase 0 for production. Optimise for throughput of insight.
5. Before adding a new source: what question does this source answer that no existing source can? If nothing, defer.
6. End each significant session with a handover note in `/handovers/YYYY-MM-DD.md`.

---

## What This Is Not

- Not a wellness app
- Not a self-help tool
- Not a journaling product
- Not a dashboard of metrics
- Not a scraper (collector with permission only)
- Not a companion (no chat interface, no personality)

---

## Relationship to WHOAMI Forensic Identity Project

WHOAMI the product automates Stream B (Behavioural Data Mining) from the WHOAMI forensic identity protocol and creates the infrastructure for Stream A (Conversation Extractions) at scale. The forensic methodology — evidence classification, confidence levels, contradiction as signal — is the intellectual foundation of the Signal Extractor.

The forensic project developed the methodology. The product eliminates the friction of applying it.
