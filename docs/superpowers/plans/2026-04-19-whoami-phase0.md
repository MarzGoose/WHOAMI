# WHOAMI Phase 0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI that reads a Claude `conversations.json` export, extracts forensic signals using 5 methods, and produces a Markdown context pack ready to paste into any AI.

**Architecture:** Three-layer pipeline — (1) source parser normalises raw exports into a common `Message` schema stored in SQLite, (2) signal extractors run five detection methods against the database, (3) a pack generator synthesises findings into a Markdown + JSON context pack. Bank CSV is added in the final tasks to enable contradiction detection across sources.

**Tech Stack:** Python 3.11+, SQLite (stdlib), pandas, anthropic SDK, pytest

---

## File Map

```
whoami/
├── requirements.txt
├── .gitignore
├── cli.py                              # Entry point: argparse CLI
├── sources/
│   ├── __init__.py
│   ├── base.py                         # Message dataclass + BaseParser ABC
│   ├── claude_export/
│   │   ├── __init__.py
│   │   └── parser.py                   # conversations.json → list[Message]
│   └── bank_csv/
│       ├── __init__.py
│       └── parser.py                   # bank CSV → list[Transaction]
├── normalise/
│   ├── __init__.py
│   ├── schema.sql                      # SQLite CREATE TABLE statements
│   └── db.py                           # DB connection, schema init, insert helpers
├── signals/
│   ├── __init__.py
│   ├── base.py                         # Signal dataclass
│   ├── absence.py                      # Method 1: topic absence
│   ├── frequency_salience.py           # Method 3: frequency vs salience
│   ├── abandoned_threads.py            # Method 5: abandoned threads
│   ├── tone_shifts.py                  # Method 4: tone shifts over time
│   └── contradiction.py               # Method 2: self-report vs transactions
├── pack/
│   ├── __init__.py
│   ├── llm.py                          # Anthropic API client (thin wrapper)
│   └── generate.py                     # Markdown + JSON pack generator
└── tests/
    ├── conftest.py                     # Shared fixtures
    ├── sources/
    │   ├── test_claude_parser.py
    │   └── test_bank_parser.py
    ├── normalise/
    │   └── test_db.py
    ├── signals/
    │   ├── test_absence.py
    │   ├── test_frequency_salience.py
    │   ├── test_abandoned_threads.py
    │   ├── test_tone_shifts.py
    │   └── test_contradiction.py
    └── pack/
        └── test_generate.py
```

---

## Task 1: Project setup

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `sources/__init__.py`, `normalise/__init__.py`, `signals/__init__.py`, `pack/__init__.py`
- Create: `sources/claude_export/__init__.py`, `sources/bank_csv/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
anthropic>=0.25.0
pandas>=2.2.0
pytest>=8.0.0
pytest-cov>=5.0.0
python-dateutil>=2.9.0
```

- [ ] **Step 2: Create .gitignore**

```
db/
exports/
output/
logs/
__pycache__/
*.pyc
.env
*.db
*.json.bak
```

- [ ] **Step 3: Create all empty `__init__.py` files**

```bash
mkdir -p sources/claude_export sources/bank_csv normalise signals pack tests/sources tests/normalise tests/signals tests/pack
touch sources/__init__.py sources/claude_export/__init__.py sources/bank_csv/__init__.py
touch normalise/__init__.py signals/__init__.py pack/__init__.py
touch tests/__init__.py tests/sources/__init__.py tests/normalise/__init__.py tests/signals/__init__.py tests/pack/__init__.py
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 5: Commit**

```bash
git init
git add .
git commit -m "chore: project scaffold"
```

---

## Task 2: Source collection guide

**Files:**
- Create: `GETTING_YOUR_FILES.md`

No TDD — this is documentation. It ships with the repo and removes all friction from the manual export step. The info-box pattern for lagged sources (Spotify, social media) is the key addition.

- [ ] **Step 1: Create GETTING_YOUR_FILES.md**

```markdown
# Getting Your Files — WHOAMI

WHOAMI reads your data locally. Some sources it fetches silently. Others need you to export them first.

---

## What WHOAMI Fetches Automatically

| Source | Method |
|--------|--------|
| Browser history | Local SQLite (Chrome, Safari, Firefox) — no action needed |
| iMessage | `~/Library/Messages/chat.db` — reads directly on macOS |

---

## Sources That Need Your Permission (one-time)

When WHOAMI requests a system permission, grant it once. It will not ask again.

---

## Sources You Export First

### Claude conversations

Settings → Privacy → Export Data → download ZIP → unzip → locate `conversations.json` → drop into WHOAMI.

---

### Google Takeout

takeout.google.com → select sources → ZIP format → download link → drop ZIP into WHOAMI (auto-extracted).

---

### Spotify

spotify.com/account/privacy → Download your data → Request extended streaming history.

> ℹ️ **Allow up to 30 days.** Spotify processes data requests in batches. Request yours now, then come back when it arrives. For best results, request before your first WHOAMI run.

---

### Instagram / Facebook

Instagram: Settings → Your activity → Download your information → JSON format.
Facebook: Settings → Your Facebook information → Download your information → JSON format.

> ℹ️ **Allow 24–48 hours.**

---

### Twitter / X

x.com → Settings → Your account → Download an archive of your data.

> ℹ️ **Allow 24 hours.**

---

### Bank records

**Preferred format: CSV** (not PDF — PDFs lose structure and reduce accuracy).

- CommBank: Accounts → Transaction History → Export → CSV
- ANZ: Internet Banking → Accounts → Export Transactions → CSV
- NAB: Internet Banking → Accounts → Transaction List → Download → CSV
- Westpac: Internet Banking → Account Summary → Export → CSV

---

### iMessage (on a different machine)

WHOAMI reads `~/Library/Messages/chat.db` directly on the Mac where your messages live — **no export needed** on the same machine.

If running WHOAMI on a different machine:

```bash
sqlite3 ~/Library/Messages/chat.db .dump > messages_export.sql
```

Or use [iMazing](https://imazing.com) for a guided export.

---

## Optional: Volunteer Additional Sources

In WHOAMI's Sources screen, point to any folder and WHOAMI will attempt to read supported file types (CSV, JSON, XML, plain text) from it. Useful for Documents, custom export folders, or any local data you want included.

---

## For Best Results

Request Spotify and social media exports **before** your first run. WHOAMI can already run on Claude conversations, iMessage, and bank data while you wait.
```

- [ ] **Step 2: Commit**

```bash
git add GETTING_YOUR_FILES.md
git commit -m "docs: source collection guide"
```

---

## Task 3: Base schemas — Message, Transaction, Signal dataclasses

**Files:**
- Create: `sources/base.py`
- Create: `signals/base.py`

- [ ] **Step 1: Write failing test**

```python
# tests/sources/test_base.py
from datetime import datetime, timezone
from sources.base import Message

def test_message_requires_fields():
    msg = Message(
        source="claude",
        source_id="abc123",
        timestamp=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        sender="human",
        content="Hello world",
        thread_id="conv001",
    )
    assert msg.source == "claude"
    assert msg.content == "Hello world"
    assert msg.metadata == {}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/sources/test_base.py -v
```

Expected: `ImportError: cannot import name 'Message'`

- [ ] **Step 3: Implement sources/base.py**

```python
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Iterator


@dataclass
class Message:
    source: str
    source_id: str
    timestamp: datetime
    sender: str
    content: str
    thread_id: str
    metadata: dict = field(default_factory=dict)


@dataclass
class Transaction:
    source: str
    source_id: str
    timestamp: datetime
    amount: float
    description: str
    category: str = ""
    metadata: dict = field(default_factory=dict)


class BaseParser(ABC):
    @abstractmethod
    def parse(self, path: str) -> Iterator:
        """Yield normalised records from a source file."""
        ...
```

- [ ] **Step 4: Implement signals/base.py**

```python
from dataclasses import dataclass, field


@dataclass
class Signal:
    signal_type: str   # ABSENCE | CONTRADICTION | FREQUENCY_SALIENCE | TONE_SHIFT | ABANDONED
    confidence: str    # HIGH | MEDIUM | LOW
    sources: list[str]
    finding: str
    evidence: str
    metadata: dict = field(default_factory=dict)
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/sources/test_base.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add sources/base.py signals/base.py tests/sources/test_base.py
git commit -m "feat: add Message, Transaction, Signal dataclasses"
```

---

## Task 4: SQLite schema and database module

**Files:**
- Create: `normalise/schema.sql`
- Create: `normalise/db.py`
- Create: `tests/normalise/test_db.py`

- [ ] **Step 1: Write failing test**

```python
# tests/normalise/test_db.py
import sqlite3
import tempfile
import os
from datetime import datetime, timezone
from sources.base import Message, Transaction
from normalise.db import init_db, insert_messages, insert_transactions, fetch_messages

def test_init_creates_tables():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        conn = init_db(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "messages" in tables
        assert "transactions" in tables
        assert "signals" in tables
    finally:
        os.unlink(db_path)

def test_insert_and_fetch_messages():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        conn = init_db(db_path)
        msgs = [
            Message(
                source="claude",
                source_id="m1",
                timestamp=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                sender="human",
                content="I never buy things on impulse",
                thread_id="conv1",
            )
        ]
        insert_messages(conn, msgs)
        fetched = fetch_messages(conn)
        assert len(fetched) == 1
        assert fetched[0].content == "I never buy things on impulse"
    finally:
        os.unlink(db_path)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/normalise/test_db.py -v
```

Expected: `ImportError: cannot import name 'init_db'`

- [ ] **Step 3: Create normalise/schema.sql**

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_id TEXT,
    timestamp TEXT NOT NULL,
    sender TEXT NOT NULL,
    content TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_id TEXT,
    timestamp TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    category TEXT DEFAULT '',
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_type TEXT NOT NULL,
    confidence TEXT NOT NULL,
    sources TEXT NOT NULL,
    finding TEXT NOT NULL,
    evidence TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);
```

- [ ] **Step 4: Implement normalise/db.py**

```python
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from sources.base import Message, Transaction
from signals.base import Signal


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    schema = (Path(__file__).parent / "schema.sql").read_text()
    conn.executescript(schema)
    conn.commit()
    return conn


def insert_messages(conn: sqlite3.Connection, messages: list[Message]) -> None:
    conn.executemany(
        "INSERT INTO messages (source, source_id, timestamp, sender, content, thread_id, metadata) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                m.source, m.source_id, m.timestamp.isoformat(),
                m.sender, m.content, m.thread_id, json.dumps(m.metadata),
            )
            for m in messages
        ],
    )
    conn.commit()


def insert_transactions(conn: sqlite3.Connection, transactions: list[Transaction]) -> None:
    conn.executemany(
        "INSERT INTO transactions (source, source_id, timestamp, amount, description, category, metadata) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                t.source, t.source_id, t.timestamp.isoformat(),
                t.amount, t.description, t.category, json.dumps(t.metadata),
            )
            for t in transactions
        ],
    )
    conn.commit()


def insert_signals(conn: sqlite3.Connection, signals: list[Signal]) -> None:
    conn.executemany(
        "INSERT INTO signals (signal_type, confidence, sources, finding, evidence, metadata, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                s.signal_type, s.confidence, json.dumps(s.sources),
                s.finding, s.evidence, json.dumps(s.metadata),
                datetime.now(timezone.utc).isoformat(),
            )
            for s in signals
        ],
    )
    conn.commit()


def fetch_messages(conn: sqlite3.Connection, source: str | None = None) -> list[Message]:
    from dateutil.parser import parse as parse_dt
    query = "SELECT source, source_id, timestamp, sender, content, thread_id, metadata FROM messages"
    params = ()
    if source:
        query += " WHERE source = ?"
        params = (source,)
    rows = conn.execute(query, params).fetchall()
    return [
        Message(
            source=row[0], source_id=row[1],
            timestamp=parse_dt(row[2]),
            sender=row[3], content=row[4],
            thread_id=row[5], metadata=json.loads(row[6]),
        )
        for row in rows
    ]


def fetch_transactions(conn: sqlite3.Connection) -> list[Transaction]:
    from dateutil.parser import parse as parse_dt
    rows = conn.execute(
        "SELECT source, source_id, timestamp, amount, description, category, metadata FROM transactions"
    ).fetchall()
    return [
        Transaction(
            source=row[0], source_id=row[1],
            timestamp=parse_dt(row[2]),
            amount=row[3], description=row[4],
            category=row[5], metadata=json.loads(row[6]),
        )
        for row in rows
    ]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/normalise/test_db.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add normalise/ tests/normalise/
git commit -m "feat: SQLite schema and db helpers"
```

---

## Task 5: Claude export parser

**Files:**
- Create: `sources/claude_export/parser.py`
- Create: `tests/sources/test_claude_parser.py`
- Create: `tests/fixtures/sample_conversations.json`

- [ ] **Step 1: Create test fixture**

Create `tests/fixtures/sample_conversations.json`:

```json
[
  {
    "uuid": "conv001",
    "name": "Gut health and beans",
    "created_at": "2024-01-15T10:30:00.000000+00:00",
    "updated_at": "2024-01-15T11:45:00.000000+00:00",
    "chat_messages": [
      {
        "uuid": "msg001",
        "text": "I never buy things on impulse, I'm very deliberate with money",
        "sender": "human",
        "created_at": "2024-01-15T10:30:00.000000+00:00",
        "attachments": [],
        "files": []
      },
      {
        "uuid": "msg002",
        "text": "That's interesting. Tell me more about your approach.",
        "sender": "assistant",
        "created_at": "2024-01-15T10:30:30.000000+00:00",
        "attachments": [],
        "files": []
      }
    ]
  },
  {
    "uuid": "conv002",
    "name": "Project planning",
    "created_at": "2024-03-10T09:00:00.000000+00:00",
    "updated_at": "2024-03-10T09:15:00.000000+00:00",
    "chat_messages": [
      {
        "uuid": "msg003",
        "text": "I want to start learning woodworking",
        "sender": "human",
        "created_at": "2024-03-10T09:00:00.000000+00:00",
        "attachments": [],
        "files": []
      }
    ]
  }
]
```

- [ ] **Step 2: Write failing test**

```python
# tests/sources/test_claude_parser.py
from pathlib import Path
from sources.claude_export.parser import ClaudeExportParser

FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample_conversations.json"

def test_parser_yields_messages():
    parser = ClaudeExportParser()
    messages = list(parser.parse(str(FIXTURE)))
    assert len(messages) == 3  # 2 from conv001, 1 from conv002

def test_parser_sets_correct_source():
    parser = ClaudeExportParser()
    messages = list(parser.parse(str(FIXTURE)))
    assert all(m.source == "claude" for m in messages)

def test_parser_sets_thread_id_to_conversation_uuid():
    parser = ClaudeExportParser()
    messages = list(parser.parse(str(FIXTURE)))
    assert messages[0].thread_id == "conv001"
    assert messages[2].thread_id == "conv002"

def test_parser_preserves_sender():
    parser = ClaudeExportParser()
    messages = list(parser.parse(str(FIXTURE)))
    assert messages[0].sender == "human"
    assert messages[1].sender == "assistant"

def test_parser_stores_conversation_name_in_metadata():
    parser = ClaudeExportParser()
    messages = list(parser.parse(str(FIXTURE)))
    assert messages[0].metadata["conversation_name"] == "Gut health and beans"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/sources/test_claude_parser.py -v
```

Expected: `ImportError`

- [ ] **Step 4: Implement sources/claude_export/parser.py**

```python
import json
from datetime import datetime
from dateutil.parser import parse as parse_dt
from typing import Iterator
from sources.base import Message, BaseParser


class ClaudeExportParser(BaseParser):
    def parse(self, path: str) -> Iterator[Message]:
        with open(path, encoding="utf-8") as f:
            conversations = json.load(f)

        for conv in conversations:
            thread_id = conv["uuid"]
            conv_name = conv.get("name", "")
            for msg in conv.get("chat_messages", []):
                text = msg.get("text", "").strip()
                if not text:
                    continue
                yield Message(
                    source="claude",
                    source_id=msg["uuid"],
                    timestamp=parse_dt(msg["created_at"]),
                    sender=msg["sender"],
                    content=text,
                    thread_id=thread_id,
                    metadata={"conversation_name": conv_name},
                )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/sources/test_claude_parser.py -v
```

Expected: PASS (5 tests)

- [ ] **Step 6: Commit**

```bash
mkdir -p tests/fixtures
git add sources/claude_export/parser.py tests/sources/test_claude_parser.py tests/fixtures/
git commit -m "feat: Claude export parser"
```

---

## Task 6: Signal — Absence detection

**Files:**
- Create: `signals/absence.py`
- Create: `tests/signals/test_absence.py`

Absence detection scans all human messages for a predefined list of life-domain topics. Domains with zero or near-zero occurrence across a substantial message corpus are flagged as absent.

- [ ] **Step 1: Write failing test**

```python
# tests/signals/test_absence.py
from datetime import datetime, timezone
from sources.base import Message
from signals.absence import detect_absence

def _msg(content, sender="human"):
    return Message(
        source="claude", source_id="x", sender=sender,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        content=content, thread_id="t1",
    )

def test_flags_domain_with_zero_mentions():
    messages = [_msg("I love programming") for _ in range(20)]
    signals = detect_absence(messages, min_messages=5)
    topics = [s.metadata["topic"] for s in signals]
    assert "money" in topics

def test_does_not_flag_domain_that_appears():
    messages = [_msg("I need to check my bank account and finances")]
    messages += [_msg("random other content") for _ in range(19)]
    signals = detect_absence(messages, min_messages=5)
    topics = [s.metadata["topic"] for s in signals]
    assert "money" not in topics

def test_returns_high_confidence_for_zero_mentions():
    messages = [_msg("coding all day") for _ in range(30)]
    signals = detect_absence(messages, min_messages=5)
    money_signals = [s for s in signals if s.metadata["topic"] == "money"]
    assert money_signals[0].confidence == "HIGH"

def test_skips_assistant_messages():
    # Assistant messages about money should not count as user mentions
    messages = [_msg("Here's how finances work", sender="assistant") for _ in range(5)]
    messages += [_msg("I like coding", sender="human") for _ in range(20)]
    signals = detect_absence(messages, min_messages=5)
    topics = [s.metadata["topic"] for s in signals]
    assert "money" in topics

def test_returns_empty_list_for_small_corpus():
    messages = [_msg("hello")]
    signals = detect_absence(messages, min_messages=10)
    assert signals == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/signals/test_absence.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement signals/absence.py**

```python
from sources.base import Message
from signals.base import Signal

LIFE_DOMAINS = {
    "money": ["money", "finance", "finances", "budget", "savings", "debt", "income",
              "salary", "bank", "spend", "spending", "cost", "afford", "expensive"],
    "family": ["family", "mum", "mom", "dad", "father", "mother", "sister", "brother",
               "parent", "parents", "child", "children", "kids"],
    "relationships": ["relationship", "partner", "girlfriend", "boyfriend", "wife", "husband",
                      "marriage", "dating", "love", "lonely", "friend", "friendship"],
    "health": ["health", "sick", "illness", "doctor", "medication", "pain", "body",
               "sleep", "diet", "exercise", "mental health", "anxiety", "depression"],
    "work": ["work", "job", "career", "boss", "colleague", "workplace", "employ",
             "salary", "promotion", "fired", "hired", "business"],
    "faith": ["god", "faith", "church", "prayer", "spiritual", "bible", "theology",
              "belief", "worship", "religion"],
    "future": ["future", "goal", "plan", "dream", "ambition", "hope", "retire",
               "five years", "someday", "eventually"],
    "past": ["regret", "mistake", "wish i had", "should have", "used to", "back then",
             "childhood", "grew up"],
}


def detect_absence(messages: list[Message], min_messages: int = 20) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    if len(human_messages) < min_messages:
        return []

    corpus = " ".join(m.content.lower() for m in human_messages)
    total = len(human_messages)
    signals = []

    for domain, keywords in LIFE_DOMAINS.items():
        mentions = sum(1 for m in human_messages
                       if any(kw in m.content.lower() for kw in keywords))
        rate = mentions / total

        if rate == 0:
            confidence = "HIGH"
        elif rate < 0.02:
            confidence = "MEDIUM"
        else:
            continue

        signals.append(Signal(
            signal_type="ABSENCE",
            confidence=confidence,
            sources=["claude"],
            finding=f'Topic "{domain}" appears in {mentions} of {total} messages ({rate:.1%}).',
            evidence=f"Keywords scanned: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}. "
                     f"Zero matches across {total} human messages.",
            metadata={"topic": domain, "mention_count": mentions, "message_total": total},
        ))

    return signals
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/signals/test_absence.py -v
```

Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add signals/absence.py tests/signals/test_absence.py
git commit -m "feat: absence signal detector"
```

---

## Task 7: Signal — Frequency vs salience

**Files:**
- Create: `signals/frequency_salience.py`
- Create: `tests/signals/test_frequency_salience.py`

Frequency vs salience detects topics the user returns to constantly without describing them as central concerns. A topic is "high frequency" if it appears in >10% of messages. It is "low salience" if the user never explicitly names it as important.

- [ ] **Step 1: Write failing test**

```python
# tests/signals/test_frequency_salience.py
from datetime import datetime, timezone
from sources.base import Message
from signals.frequency_salience import detect_frequency_salience

def _msg(content, sender="human"):
    return Message(
        source="claude", source_id="x", sender=sender,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        content=content, thread_id="t1",
    )

def test_flags_high_frequency_low_salience_topic():
    # "tools" appears constantly but user never says it's important
    messages = [_msg("I went to Bunnings to look at tools") for _ in range(15)]
    messages += [_msg("I care most about my family and faith") for _ in range(5)]
    signals = detect_frequency_salience(messages, min_messages=10)
    topics = [s.metadata["topic"] for s in signals]
    assert "tools" in topics

def test_does_not_flag_topic_described_as_important():
    messages = [_msg("Tools are the most important thing to me") for _ in range(3)]
    messages += [_msg("I love tools, they are central to my life") for _ in range(3)]
    messages += [_msg("random stuff") for _ in range(14)]
    signals = detect_frequency_salience(messages, min_messages=10)
    topics = [s.metadata["topic"] for s in signals]
    assert "tools" not in topics

def test_returns_correct_signal_type():
    messages = [_msg("bought more hardware again") for _ in range(15)]
    messages += [_msg("other stuff") for _ in range(5)]
    signals = detect_frequency_salience(messages, min_messages=10)
    assert all(s.signal_type == "FREQUENCY_SALIENCE" for s in signals)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/signals/test_frequency_salience.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement signals/frequency_salience.py**

```python
from sources.base import Message
from signals.base import Signal

TRACKED_TOPICS = {
    "tools": ["tool", "tools", "hardware", "bunnings", "equipment", "gear"],
    "money": ["money", "spend", "spending", "buy", "bought", "purchase", "cost"],
    "work": ["work", "job", "project", "client", "meeting", "deadline"],
    "health": ["health", "sleep", "tired", "energy", "gym", "exercise", "diet"],
    "family": ["mum", "mom", "dad", "family", "kids", "children"],
    "learning": ["learn", "study", "course", "reading", "book", "research"],
}

SALIENCE_MARKERS = [
    "important", "central", "core", "fundamental", "key", "main", "primary",
    "most", "love", "passion", "care about", "matter", "matters", "focus",
]


def detect_frequency_salience(messages: list[Message], min_messages: int = 20) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    if len(human_messages) < min_messages:
        return []

    total = len(human_messages)
    signals = []

    for topic, keywords in TRACKED_TOPICS.items():
        topic_messages = [
            m for m in human_messages
            if any(kw in m.content.lower() for kw in keywords)
        ]
        frequency = len(topic_messages) / total
        if frequency < 0.10:
            continue

        # Check if topic is ever described as important/central
        salience_messages = [
            m for m in topic_messages
            if any(marker in m.content.lower() for marker in SALIENCE_MARKERS)
        ]
        if salience_messages:
            continue

        signals.append(Signal(
            signal_type="FREQUENCY_SALIENCE",
            confidence="HIGH" if frequency > 0.25 else "MEDIUM",
            sources=["claude"],
            finding=(
                f'"{topic}" appears in {len(topic_messages)} of {total} messages '
                f'({frequency:.0%}) but is never described as important or central.'
            ),
            evidence=(
                f"Frequency: {frequency:.0%}. "
                f"Salience markers checked: {', '.join(SALIENCE_MARKERS[:5])}... — none found near topic mentions."
            ),
            metadata={
                "topic": topic,
                "frequency": frequency,
                "mention_count": len(topic_messages),
                "message_total": total,
            },
        ))

    return signals
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/signals/test_frequency_salience.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add signals/frequency_salience.py tests/signals/test_frequency_salience.py
git commit -m "feat: frequency vs salience signal detector"
```

---

## Task 8: Signal — Abandoned threads

**Files:**
- Create: `signals/abandoned_threads.py`
- Create: `tests/signals/test_abandoned_threads.py`

Abandoned threads are topics that appear in one or two conversation threads and are never returned to. A topic is "abandoned" if (a) it was raised by the user, (b) the conversation ended without resolution markers, and (c) the topic never recurs across other threads.

- [ ] **Step 1: Write failing test**

```python
# tests/signals/test_abandoned_threads.py
from datetime import datetime, timezone
from sources.base import Message
from signals.abandoned_threads import detect_abandoned_threads

def _msg(content, thread_id="t1", sender="human", day=1):
    return Message(
        source="claude", source_id=f"{thread_id}-{day}",
        sender=sender,
        timestamp=datetime(2024, day if day <= 28 else 1, 1, tzinfo=timezone.utc),
        content=content, thread_id=thread_id,
    )

def test_flags_topic_raised_once_and_dropped():
    messages = (
        [_msg("I want to start learning woodworking", thread_id="conv1")]
        + [_msg("other topics about coding") for _ in range(20)]
    )
    signals = detect_abandoned_threads(messages)
    findings = [s.finding for s in signals]
    assert any("woodworking" in f.lower() or "learn" in f.lower() for f in findings)

def test_does_not_flag_topic_returned_to():
    messages = (
        [_msg("I want to start learning woodworking", thread_id="conv1")]
        + [_msg("more about woodworking progress", thread_id="conv2")]
        + [_msg("my woodworking project is coming along", thread_id="conv3")]
    )
    signals = detect_abandoned_threads(messages)
    # woodworking appears in 3 threads so should NOT be flagged
    findings = " ".join(s.finding.lower() for s in signals)
    assert "woodworking" not in findings

def test_returns_correct_signal_type():
    messages = [_msg("I was thinking about starting a podcast", thread_id="c1")]
    messages += [_msg("other stuff", thread_id=f"c{i}") for i in range(2, 20)]
    signals = detect_abandoned_threads(messages)
    assert all(s.signal_type == "ABANDONED" for s in signals)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/signals/test_abandoned_threads.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement signals/abandoned_threads.py**

```python
from collections import defaultdict
from sources.base import Message
from signals.base import Signal

# Intent phrases that suggest a project or plan being started
INTENT_PHRASES = [
    "i want to", "i'm going to", "i plan to", "i was thinking about",
    "i should", "i need to start", "i've been meaning to",
    "i was considering", "i might", "thinking of starting",
    "want to learn", "want to try", "want to build",
]


def detect_abandoned_threads(messages: list[Message]) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]

    # Find messages containing intent phrases
    intent_messages = [
        m for m in human_messages
        if any(phrase in m.content.lower() for phrase in INTENT_PHRASES)
    ]

    if not intent_messages:
        return []

    # For each intent message, extract a short topic summary (first 6 words after intent phrase)
    def extract_topic(content: str) -> str:
        content_lower = content.lower()
        for phrase in INTENT_PHRASES:
            idx = content_lower.find(phrase)
            if idx != -1:
                after = content[idx + len(phrase):].strip()
                words = after.split()[:6]
                return " ".join(words).rstrip(".,!?")
        return content[:40]

    # Count how many distinct threads each topic appears in
    topic_threads: dict[str, set[str]] = defaultdict(set)
    topic_examples: dict[str, str] = {}

    for m in intent_messages:
        topic = extract_topic(m.content)
        topic_key = topic[:30].lower()
        topic_threads[topic_key].add(m.thread_id)
        topic_examples[topic_key] = topic

    signals = []
    for topic_key, threads in topic_threads.items():
        if len(threads) == 1:
            signals.append(Signal(
                signal_type="ABANDONED",
                confidence="MEDIUM",
                sources=["claude"],
                finding=(
                    f'Intent raised once and never returned to: '
                    f'"{topic_examples[topic_key]}"'
                ),
                evidence=(
                    f"Appeared in 1 conversation thread. "
                    f"No subsequent references to this topic found across {len(human_messages)} messages."
                ),
                metadata={"topic": topic_examples[topic_key], "thread_count": 1},
            ))

    return signals
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/signals/test_abandoned_threads.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add signals/abandoned_threads.py tests/signals/test_abandoned_threads.py
git commit -m "feat: abandoned threads signal detector"
```

---

## Task 9: Signal — Tone shifts

**Files:**
- Create: `signals/tone_shifts.py`
- Create: `tests/signals/test_tone_shifts.py`

Tone shifts detect topics the user discusses with noticeably different emotional register at different points in time. Uses a simple keyword-based sentiment score (positive/negative/neutral) rather than a heavy NLP library.

- [ ] **Step 1: Write failing test**

```python
# tests/signals/test_tone_shifts.py
from datetime import datetime, timezone
from sources.base import Message
from signals.tone_shifts import detect_tone_shifts

def _msg(content, month=1, sender="human"):
    return Message(
        source="claude", source_id=f"m{month}",
        sender=sender,
        timestamp=datetime(2024, month, 1, tzinfo=timezone.utc),
        content=content, thread_id=f"t{month}",
    )

def test_detects_topic_with_shifting_sentiment():
    messages = (
        [_msg("I love my work, it's amazing and fulfilling", month=1) for _ in range(5)]
        + [_msg("work is fine", month=3) for _ in range(2)]
        + [_msg("work is exhausting and draining, terrible experience", month=6) for _ in range(5)]
    )
    signals = detect_tone_shifts(messages)
    assert len(signals) >= 1
    assert any(s.signal_type == "TONE_SHIFT" for s in signals)

def test_no_signal_for_consistent_topic():
    messages = [_msg("work is good today", month=i) for i in range(1, 7)]
    signals = detect_tone_shifts(messages)
    assert len(signals) == 0

def test_uses_only_human_messages():
    messages = (
        [_msg("I love my work so much", month=1, sender="human") for _ in range(5)]
        + [_msg("work is terrible and draining", month=6, sender="assistant") for _ in range(5)]
    )
    signals = detect_tone_shifts(messages)
    # Assistant messages about work should not trigger a tone shift
    assert len(signals) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/signals/test_tone_shifts.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement signals/tone_shifts.py**

```python
from collections import defaultdict
from sources.base import Message
from signals.base import Signal

POSITIVE_WORDS = {
    "love", "amazing", "great", "excellent", "fantastic", "wonderful", "enjoy",
    "happy", "good", "brilliant", "exciting", "fulfilling", "rewarding", "grateful",
    "thankful", "proud", "thriving", "blessed", "inspired",
}
NEGATIVE_WORDS = {
    "hate", "terrible", "awful", "horrible", "dread", "exhausting", "draining",
    "boring", "frustrating", "angry", "depressed", "stuck", "trapped", "miserable",
    "pointless", "meaningless", "struggling", "overwhelmed", "hopeless",
}

DOMAIN_KEYWORDS = {
    "work": ["work", "job", "career", "boss", "office", "client", "project", "meeting"],
    "family": ["family", "mum", "mom", "dad", "parent", "sibling", "kids"],
    "health": ["health", "body", "sleep", "energy", "pain", "sick", "well"],
    "money": ["money", "finances", "budget", "savings", "debt"],
    "relationships": ["relationship", "partner", "friend", "people", "social"],
}


def _sentiment_score(text: str) -> float:
    words = set(text.lower().split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def detect_tone_shifts(messages: list[Message], min_period_messages: int = 3) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    if len(human_messages) < 6:
        return []

    # Split messages into two halves by time
    sorted_msgs = sorted(human_messages, key=lambda m: m.timestamp)
    mid = len(sorted_msgs) // 2
    early = sorted_msgs[:mid]
    late = sorted_msgs[mid:]

    signals = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        early_domain = [m for m in early if any(k in m.content.lower() for k in keywords)]
        late_domain = [m for m in late if any(k in m.content.lower() for k in keywords)]

        if len(early_domain) < min_period_messages or len(late_domain) < min_period_messages:
            continue

        early_score = sum(_sentiment_score(m.content) for m in early_domain) / len(early_domain)
        late_score = sum(_sentiment_score(m.content) for m in late_domain) / len(late_domain)
        delta = late_score - early_score

        if abs(delta) < 0.4:
            continue

        direction = "more negative" if delta < 0 else "more positive"
        signals.append(Signal(
            signal_type="TONE_SHIFT",
            confidence="HIGH" if abs(delta) > 0.6 else "MEDIUM",
            sources=["claude"],
            finding=(
                f'Tone around "{domain}" has become {direction} over time '
                f'(early score: {early_score:+.2f}, late score: {late_score:+.2f}).'
            ),
            evidence=(
                f"Early period: {len(early_domain)} messages, avg sentiment {early_score:+.2f}. "
                f"Late period: {len(late_domain)} messages, avg sentiment {late_score:+.2f}. "
                f"Delta: {delta:+.2f}."
            ),
            metadata={
                "domain": domain,
                "early_score": early_score,
                "late_score": late_score,
                "delta": delta,
            },
        ))

    return signals
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/signals/test_tone_shifts.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add signals/tone_shifts.py tests/signals/test_tone_shifts.py
git commit -m "feat: tone shift signal detector"
```

---

## Task 10: Bank CSV parser

**Files:**
- Create: `sources/bank_csv/parser.py`
- Create: `tests/sources/test_bank_parser.py`
- Create: `tests/fixtures/sample_bank.csv`

Australian banks export CSVs in slightly different formats. This parser handles the most common pattern: Date, Description, Debit, Credit, Balance columns. It normalises to `Transaction` objects.

- [ ] **Step 1: Create test fixture**

Create `tests/fixtures/sample_bank.csv`:

```csv
Date,Description,Debit,Credit,Balance
15/01/2024,BUNNINGS WAREHOUSE AUBURN,-85.40,,2150.60
16/01/2024,SALARY ACME PTY LTD,,3500.00,5650.60
22/01/2024,BUNNINGS WAREHOUSE AUBURN,-42.90,,5607.70
05/02/2024,NETFLIX,-15.99,,5591.71
10/02/2024,BUNNINGS WAREHOUSE AUBURN,-127.50,,5464.21
28/02/2024,BUNNINGS WAREHOUSE AUBURN,-63.20,,5401.01
15/03/2024,AMAZON MARKETPLACE,-210.00,,5191.01
```

- [ ] **Step 2: Write failing tests**

```python
# tests/sources/test_bank_parser.py
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
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/sources/test_bank_parser.py -v
```

Expected: `ImportError`

- [ ] **Step 4: Implement sources/bank_csv/parser.py**

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/sources/test_bank_parser.py -v
```

Expected: PASS (7 tests)

- [ ] **Step 6: Commit**

```bash
git add sources/bank_csv/parser.py tests/sources/test_bank_parser.py tests/fixtures/sample_bank.csv
git commit -m "feat: bank CSV parser with format detection"
```

---

## Task 11: Signal — Contradiction (self-report vs transactions)

**Files:**
- Create: `signals/contradiction.py`
- Create: `tests/signals/test_contradiction.py`

Contradiction detection mines human messages for first-person claims ("I don't...", "I never...", "I always...") then cross-references with transaction data to find behavioural contradictions.

- [ ] **Step 1: Write failing test**

```python
# tests/signals/test_contradiction.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/signals/test_contradiction.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement signals/contradiction.py**

```python
from datetime import time
from sources.base import Message, Transaction
from signals.base import Signal

# Claims that suggest restraint or deliberateness with spending
RESTRAINT_CLAIMS = [
    ("impulse", ["impulse", "impulsive"], "hardware"),
    ("frugal", ["frugal", "careful with money", "save money", "don't spend much"], "online_retail"),
    ("minimalist", ["minimalist", "don't need much", "don't buy much"], "online_retail"),
]

LATE_NIGHT_HOUR_START = 21  # 9pm


def _is_late_night(txn: Transaction) -> bool:
    return txn.timestamp.hour >= LATE_NIGHT_HOUR_START


def detect_contradiction(
    messages: list[Message],
    transactions: list[Transaction],
) -> list[Signal]:
    human_messages = [m for m in messages if m.sender == "human"]
    corpus = " ".join(m.content.lower() for m in human_messages)
    signals = []

    for claim_name, claim_keywords, spend_category in RESTRAINT_CLAIMS:
        claim_found = any(kw in corpus for kw in claim_keywords)
        if not claim_found:
            continue

        # Find supporting transactions that contradict the claim
        category_txns = [t for t in transactions if t.category == spend_category and t.amount < 0]
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/signals/test_contradiction.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add signals/contradiction.py tests/signals/test_contradiction.py
git commit -m "feat: contradiction signal detector (self-report vs transactions)"
```

---

## Task 12: LLM client and context pack generator

**Files:**
- Create: `pack/llm.py`
- Create: `pack/generate.py`
- Create: `tests/pack/test_generate.py`

The pack generator synthesises all signals into a Markdown context pack using the Claude API. The LLM client is a thin wrapper around the Anthropic SDK.

- [ ] **Step 1: Write failing test (no API call — mocked)**

```python
# tests/pack/test_generate.py
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from signals.base import Signal
from pack.generate import generate_pack

SAMPLE_SIGNALS = [
    Signal(
        signal_type="ABSENCE",
        confidence="HIGH",
        sources=["claude"],
        finding='Topic "money" appears in 0 of 200 messages (0.0%).',
        evidence="Zero matches across 200 human messages.",
        metadata={"topic": "money"},
    ),
    Signal(
        signal_type="CONTRADICTION",
        confidence="HIGH",
        sources=["claude", "bank"],
        finding="States no impulse purchasing — 8 late-night hardware transactions recorded.",
        evidence="Claim keywords found. 8 transactions after 9pm in hardware category.",
        metadata={"claim": "impulse", "late_night_count": 8},
    ),
]

def test_generate_pack_returns_markdown_string():
    with patch("pack.generate.LLMClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "# WHOAMI Context Pack\n\nTest content."
        mock_cls.return_value = mock_instance

        result = generate_pack(SAMPLE_SIGNALS, subject_name="John")

    assert isinstance(result, str)
    assert len(result) > 50

def test_generate_pack_includes_signal_count():
    with patch("pack.generate.LLMClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "# WHOAMI Context Pack\n\n2 signals found."
        mock_cls.return_value = mock_instance

        result = generate_pack(SAMPLE_SIGNALS, subject_name="John")

    assert result is not None

def test_generate_pack_writes_json_sidecar(tmp_path):
    with patch("pack.generate.LLMClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "# WHOAMI Context Pack\n\nContent."
        mock_cls.return_value = mock_instance

        output_path = tmp_path / "pack.md"
        generate_pack(SAMPLE_SIGNALS, subject_name="John", output_path=str(output_path))

    assert output_path.exists()
    json_path = output_path.with_suffix(".json")
    assert json_path.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/pack/test_generate.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement pack/llm.py**

```python
import os
import anthropic


class LLMClient:
    def __init__(self, api_key: str | None = None):
        self._client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    def complete(self, prompt: str, max_tokens: int = 4096) -> str:
        message = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
```

- [ ] **Step 4: Implement pack/generate.py**

```python
import json
from datetime import datetime, timezone
from pathlib import Path
from signals.base import Signal
from pack.llm import LLMClient


PACK_PROMPT_TEMPLATE = """You are a forensic identity analyst. Below are {signal_count} signals extracted from {subject_name}'s personal data. These signals were detected automatically from their digital exhaust files — data generated without narrator curation.

Your task: produce a structured WHOAMI context pack. This is a portable identity document designed to give any AI immediate, calibrated understanding of this person — replacing the need for a lengthy intake interview.

SIGNALS:
{signals_text}

Produce the context pack in this format:

# WHOAMI Context Pack — {subject_name}
Generated: {date}
Signals: {signal_count} | Sources: {sources}

## Identity Signals

[For each signal, write a clear, forensic, non-judgmental statement of what the data shows. Present contradictions as open findings, not conclusions. Do not resolve or explain away conflicts.]

## Patterns Requiring Attention

[List 3-5 patterns that cut across multiple signals. Note confidence level. Flag anything that appears in both conversation data and behavioural data.]

## Open Questions

[3-5 questions this data raises that self-report cannot answer. These are interview prompts for follow-up.]

## For the AI Reading This Pack

[One paragraph briefing the downstream AI on how to use this pack — what to probe, what to avoid assuming, what the subject's narrator is likely to over-represent.]

Write forensically. No flattery. No resolution of contradictions. Present evidence, not verdicts."""


def generate_pack(
    signals: list[Signal],
    subject_name: str = "User",
    output_path: str | None = None,
    api_key: str | None = None,
) -> str:
    signals_text = "\n\n".join(
        f"[{s.signal_type} | {s.confidence}]\n"
        f"Finding: {s.finding}\n"
        f"Evidence: {s.evidence}\n"
        f"Sources: {', '.join(s.sources)}"
        for s in signals
    )

    all_sources = sorted({src for s in signals for src in s.sources})

    prompt = PACK_PROMPT_TEMPLATE.format(
        signal_count=len(signals),
        subject_name=subject_name,
        signals_text=signals_text,
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        sources=", ".join(all_sources),
    )

    client = LLMClient(api_key=api_key)
    pack_text = client.complete(prompt)

    if output_path:
        Path(output_path).write_text(pack_text, encoding="utf-8")
        json_path = Path(output_path).with_suffix(".json")
        json_path.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "subject_name": subject_name,
                    "signal_count": len(signals),
                    "signals": [
                        {
                            "signal_type": s.signal_type,
                            "confidence": s.confidence,
                            "sources": s.sources,
                            "finding": s.finding,
                            "evidence": s.evidence,
                            "metadata": s.metadata,
                        }
                        for s in signals
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    return pack_text
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/pack/test_generate.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add pack/ tests/pack/
git commit -m "feat: LLM client and context pack generator"
```

---

## Task 13: CLI entry point

**Files:**
- Create: `cli.py`

The CLI wires all layers together. It accepts paths to exhaust files, runs the pipeline, and writes the context pack to the output directory.

- [ ] **Step 1: Implement cli.py**

```python
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
```

- [ ] **Step 2: Make CLI executable and test help output**

```bash
chmod +x cli.py
python cli.py --help
```

Expected output includes: `--claude`, `--bank`, `--name`, `--output`

- [ ] **Step 3: Commit**

```bash
git add cli.py
git commit -m "feat: CLI entry point"
```

---

## Task 14: End-to-end integration test

**Files:**
- Create: `tests/test_integration.py`

This test runs the full pipeline against the fixture files without calling the real API (mocked). It confirms all layers connect correctly.

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from normalise.db import init_db, insert_messages, insert_transactions, fetch_messages
from sources.claude_export.parser import ClaudeExportParser
from sources.bank_csv.parser import BankCSVParser
from signals.absence import detect_absence
from signals.frequency_salience import detect_frequency_salience
from signals.abandoned_threads import detect_abandoned_threads
from signals.contradiction import detect_contradiction
from pack.generate import generate_pack

CLAUDE_FIXTURE = Path(__file__).parent / "fixtures" / "sample_conversations.json"
BANK_FIXTURE = Path(__file__).parent / "fixtures" / "sample_bank.csv"


def test_full_pipeline_claude_only():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = init_db(db_path)

    # Ingest
    messages = list(ClaudeExportParser().parse(str(CLAUDE_FIXTURE)))
    insert_messages(conn, messages)
    assert len(fetch_messages(conn)) == 3

    # Extract (small corpus — absence requires min_messages=5 to return results on 3 messages)
    all_messages = fetch_messages(conn)
    absence = detect_absence(all_messages, min_messages=2)
    abandoned = detect_abandoned_threads(all_messages)
    signals = absence + abandoned
    assert isinstance(signals, list)

    os.unlink(db_path)


def test_full_pipeline_with_bank():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = init_db(db_path)

    messages = list(ClaudeExportParser().parse(str(CLAUDE_FIXTURE)))
    insert_messages(conn, messages)

    transactions = list(BankCSVParser().parse(str(BANK_FIXTURE)))
    insert_transactions(conn, transactions)
    assert len(transactions) == 7

    all_messages = fetch_messages(conn)
    from normalise.db import fetch_transactions
    all_txns = fetch_transactions(conn)
    signals = detect_contradiction(all_messages, all_txns)
    assert isinstance(signals, list)

    os.unlink(db_path)


def test_pack_generation_with_mocked_llm():
    from signals.base import Signal

    signals = [
        Signal(
            signal_type="ABSENCE",
            confidence="HIGH",
            sources=["claude"],
            finding='Topic "money" appears in 0 of 3 messages.',
            evidence="Zero matches.",
            metadata={"topic": "money"},
        )
    ]

    with patch("pack.generate.LLMClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "# WHOAMI Context Pack\n\nTest pack content."
        mock_cls.return_value = mock_instance

        result = generate_pack(signals, subject_name="John")

    assert "WHOAMI" in result or "Test" in result
```

- [ ] **Step 2: Run all tests**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests PASS. Note the total count.

- [ ] **Step 3: Run with coverage**

```bash
pytest tests/ --cov=. --cov-report=term-missing --cov-omit="tests/*"
```

Expected: Coverage report shows >70% across all modules.

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: end-to-end integration test"
```

---

## Task 15: Smoke test against real data

This task has no test file — it is a manual validation step. Run the CLI against John's actual `conversations.json` and evaluate whether the context pack surfaces real signal.

- [ ] **Step 1: Export Claude conversations**

In claude.ai: Settings → Privacy → Export Data. Download the ZIP, extract `conversations.json`. Place it at `exports/conversations.json`.

- [ ] **Step 2: Set API key**

```bash
export ANTHROPIC_API_KEY=your_key_here
```

- [ ] **Step 3: Run the pipeline**

```bash
python cli.py \
  --claude exports/conversations.json \
  --name "John" \
  --output output/john-pack-v1.md
```

Expected: Terminal shows signal counts, pack written to `output/john-pack-v1.md`.

- [ ] **Step 4: Evaluate the pack**

Open `output/john-pack-v1.md`. Paste into a fresh Claude conversation. Ask:
> "Using only the context pack above, what do you know about me? What questions would you ask that you couldn't answer from this pack alone?"

Evaluate against success criterion: **does the pack surface at least three patterns not consciously known or reported?**

- [ ] **Step 5: Write handover note**

```bash
mkdir -p handovers
```

Create `handovers/2026-04-19.md` documenting:
- What the smoke test found
- Which signals fired
- What felt accurate vs. surprising
- What the next session should improve

- [ ] **Step 6: Final commit**

```bash
git add output/.gitkeep handovers/
git commit -m "chore: smoke test complete — handover written"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| Local-first, no API calls for data | All parsers read local files only — ✓ |
| Claude export parser | Task 4 ✓ |
| Bank CSV parser | Task 9 ✓ |
| SQLite normalisation | Task 3 ✓ |
| Absence detection (Method 1) | Task 5 ✓ |
| Contradiction detection (Method 2) | Task 10 ✓ |
| Frequency vs salience (Method 3) | Task 6 ✓ |
| Tone shifts (Method 4) | Task 8 ✓ |
| Abandoned threads (Method 5) | Task 7 ✓ |
| Context pack as Markdown + JSON | Task 11 ✓ |
| Claude API for pack generation | Task 11 ✓ |
| CLI entry point | Task 12 ✓ |
| End-to-end test | Task 13 ✓ |
| Exhaust files nomenclature | Used in CLI help text ✓ |
| Source collection guide (export instructions, info boxes for lagged sources, iMessage terminal command) | Task 2 ✓ |
| Bank CSV format detection (column layout auto-detect, clear error on unrecognised format) | Task 10 ✓ |
| Methods 6–9 (cross-stream convergence, linguistic distancing, baseline anomalies, temporal clustering) | **Deferred to Phase 1** — require multiple sources or NLP libraries not in Phase 0 scope |

**Deferred methods note:** Methods 6–9 are intentionally excluded from this plan. Cross-stream convergence requires at least 3 sources; linguistic distancing requires spaCy; baseline anomalies and temporal clustering require longer time-series data than Phase 0 fixtures can provide. All are Phase 1 additions once the core pipeline is validated.

**Placeholder scan:** None found. All steps contain complete code.

**Type consistency:** `Message`, `Transaction`, `Signal` dataclasses defined in Task 2 and used consistently across all signal and pack tasks. `fetch_messages` / `fetch_transactions` / `insert_messages` / `insert_transactions` defined in Task 3 and imported consistently in Tasks 12 and 13.
