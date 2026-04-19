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
