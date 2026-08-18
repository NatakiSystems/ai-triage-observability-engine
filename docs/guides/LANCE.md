# Lance — Integration Engineer

**You own:** `tools/ticket_source.py`, `tools/policy_lookup.py`,
`data/tickets.csv`

**Your job in one sentence:** get data into the system reliably. Tickets in,
policy out, and neither one crashes when something is malformed.

Good news for a beginner: **your files never call an LLM.** No API key needed,
no cost, instant feedback, fully testable. You can do your entire job in mock
mode. That makes you the best-positioned person on the team to build confidence
before touching anything unpredictable.

---

## Task 1 — Read what you own (30 minutes)

```bash
python main.py --mock --limit 3
```

Then open both your files and read the docstrings at the top. Then try this in
a Python shell to see your code in isolation:

```bash
python3
```

```python
from tools.ticket_source import load_tickets
tickets = load_tickets(limit=2)
print(tickets[0])
print(tickets[0].subject)

from tools.policy_lookup import lookup_policy, load_policy_sections
print(load_policy_sections().keys())
print(lookup_policy("returns"))
```

Poking at functions directly in a shell, instead of running the whole program,
is a skill worth having. Use it constantly.

---

## Task 2 — Make ticket loading survive bad data

Right now a row with a missing column crashes the whole run. That's the single
most likely thing to break your demo, because you're about to add a lot of rows
by hand.

**Prove the bug first.** Open `data/tickets.csv` in a text editor, delete the
`received_at` value from one row, save, and run:

```bash
python main.py --mock --limit 5
```

You'll get a `KeyError`. Good. Now fix it in `tools/ticket_source.py`:

```python
for row_number, row in enumerate(reader, start=2):   # 2 because line 1 is headers
    try:
        tickets.append(Ticket(
            ticket_id=row["ticket_id"],
            customer_name=row["customer_name"],
            subject=row["subject"],
            body=row["body"],
            received_at=row["received_at"],
        ))
    except Exception as e:
        print(f"  WARNING: skipping row {row_number} in tickets.csv - {e}")
        continue

    if limit and len(tickets) >= limit:
        break
```

Run again. You should now see your warning, and the other tickets should process
normally. **Then put the deleted value back** so the data is clean.

**Why this matters for the pitch:** a real support inbox has malformed data in
it constantly. "We handle bad rows without dropping the batch" is a real
engineering answer to a real question.

---

## Task 3 — Grow the ticket set to ~30 (this is your biggest contribution)

We have 12. That's enough to run, not enough to measure. Julian needs volume to
compute accuracy, and the demo is more convincing with a realistic inbox.

Open `data/tickets.csv` and add rows. Keep the same five columns. **Keep IDs
sequential** (NS-1013, NS-1014...).

Aim for this mix:

| Kind | How many | Why |
|---|---|---|
| Clear billing | 5 | the easy case |
| Clear technical | 5 | the easy case |
| Clear returns | 5 | the easy case |
| Genuinely ambiguous | 4 | should produce LOW confidence, and route to a human |
| Legal threat / very angry | 2 | must trigger `needs_human` |
| Refund over $100 | 2 | must trigger `needs_human` |
| Doesn't fit any category | 2 | should classify as "other" |
| Vague one-liners | 3 | "it's broken. help." — tests the hard case |

Write them like real people write. Typos, missing details, run-on sentences, all
lowercase. A ticket set where every message is a clean paragraph will make our
accuracy look better than it is, and that's the kind of thing a grader notices.

**Careful with commas.** CSV uses commas as separators, so any field containing
a comma must be wrapped in double quotes:

```csv
NS-1013,Maya Chen,Refund please,"I ordered this on the 3rd, it never came.",2026-08-04T09:00:00
```

Verify after every batch you add:

```bash
python -c "from tools.ticket_source import load_tickets; t=load_tickets(); print(f'{len(t)} tickets loaded')"
```

If the number is lower than what you added, a row is malformed. Your Task 2
warning will tell you which line.

---

## Task 4 — Handle the policy lookup miss

In `tools/policy_lookup.py`, decide what happens when a category has no policy
section. Two things to fix:

**Normalize the input** so a stray capital or space doesn't cause a miss:

```python
def lookup_policy(category):
    sections = load_policy_sections()
    key = (category or "").strip().lower()
    return sections.get(key, "NO POLICY FOUND for this category. Escalate to a human agent.")
```

**Test the miss path deliberately:**

```python
from tools.policy_lookup import lookup_policy
print(lookup_policy("nonsense"))       # should return the escalate message
print(lookup_policy("  BILLING  "))    # should still find the billing policy
```

**Then talk to Julian.** When the policy is missing, the drafter writes from
nothing, which is exactly what his critic should catch. One of you has to own
that case. Agree out loud who does, and write it down.

---

## Task 5 (stretch, worth real credit) — SQLite version

The assignment likes "one tool wired to a real data source." A CSV is defensible,
but SQLite is a database, ships with Python, needs no install, and makes the
claim stronger.

Create `tools/build_db.py`:

```python
"""One-time script: load tickets.csv into a SQLite database."""
import csv
import os
import sqlite3

HERE = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(HERE, "data", "tickets.db")
CSV_PATH = os.path.join(HERE, "data", "tickets.csv")

conn = sqlite3.connect(DB_PATH)
conn.execute("DROP TABLE IF EXISTS tickets")
conn.execute("""
    CREATE TABLE tickets (
        ticket_id     TEXT PRIMARY KEY,
        customer_name TEXT,
        subject       TEXT,
        body          TEXT,
        received_at   TEXT
    )
""")

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    rows = [
        (r["ticket_id"], r["customer_name"], r["subject"], r["body"], r["received_at"])
        for r in csv.DictReader(f)
    ]

conn.executemany("INSERT INTO tickets VALUES (?,?,?,?,?)", rows)
conn.commit()
print(f"Loaded {len(rows)} tickets into {DB_PATH}")
```

Run it once:

```bash
python tools/build_db.py
```

Then add a loader alongside the CSV one in `ticket_source.py`:

```python
def load_tickets_from_db(limit=None):
    """Same as load_tickets, but reads from SQLite."""
    import sqlite3
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tickets.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM tickets ORDER BY received_at"
    if limit:
        query += f" LIMIT {int(limit)}"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [Ticket(**dict(row)) for row in rows]
```

**Keep both.** Same interface, two sources, which is exactly the point you make
in the pitch: swapping the CSV for Zendesk's API later touches only this file.

Add `data/tickets.db` to `.gitignore` — it's generated, not source.

---

## Definition of done

- [ ] A malformed CSV row prints a warning and gets skipped, run continues
- [ ] ~30 tickets covering every category plus the edge cases in Task 3
- [ ] `lookup_policy` handles a missing category and messy capitalization
- [ ] You and Julian have agreed who owns the missing-policy case
- [ ] (Stretch) SQLite loader working, same interface as the CSV one
- [ ] Your branch merged into main

---

## Your line in the pitch

"The pipeline reads from a SQLite database through a single interface. Swapping
in a real helpdesk API touches one file and nothing else. Malformed records are
logged and skipped rather than dropping the whole batch."

---

## Where you'll get stuck

**`KeyError: 'received_at'`** — a CSV row is missing a column, or the header row
got edited. Your Task 2 fix turns this into a warning.

**A row with a comma in it splits into extra columns** — wrap that field in
double quotes.

**`FileNotFoundError`** — you're running from the wrong folder. Always run from
the project root, the folder with `main.py` in it.

**Excel mangles the CSV** — it likes to reformat dates and strip quotes. Use a
plain text editor (VS Code, Notepad++, TextEdit in plain mode) instead.
