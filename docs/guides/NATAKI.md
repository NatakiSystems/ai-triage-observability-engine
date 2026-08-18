# Nataki — Logging & Observability Engineer

**You own:** `agents/triage.py`, `logging_utils.py`, `approval_queue.py`, and the
"What We Keep From the Old Process" writeup.

**Your job in one sentence:** make everything the agents do visible, and build
the place where a human actually reviews what got flagged.

Two things worth knowing up front. The approval queue you build is **the thing
we demo live** — it's the most visible piece in the whole presentation. And the
audit trail is the core argument of the project: the supervisor stops reading
every reply, but nothing becomes invisible. That's your writeup.

---

## Task 1 — See what's already being logged (30 minutes)

```bash
python main.py --mock
```

Then look at what came out:

```bash
ls logs/
python -c "
import json, glob
path = sorted(glob.glob('logs/*.jsonl'))[-1]
for line in open(path):
    e = json.loads(line)
    print(f\"{e['event_type']:22s} {e['ticket_id']}\")
"
```

You'll see the full life of each ticket: `triage_complete`, `policy_retrieved`,
`draft_created`, `critic_verdict`, then `auto_sent` or `escalated_to_human`.

**JSONL means one JSON object per line.** Not one big JSON file. That matters
because you can read it line by line, load it into a spreadsheet, or `grep` it,
and a crash mid-run doesn't corrupt what was already written.

---

## Task 2 — Improve the triage agent

Open `agents/triage.py`. It's short, and that's on purpose: the validation lives
in the `TriageResult` schema in `state.py`, so you don't hand-write category
checks.

The one thing you control here is what the model sees:

```python
user_message = f"Subject: {ticket.subject}\n\nBody: {ticket.body}"
```

**Experiment, don't guess.** Once Julian's labeled set exists, run
`python scripts/evaluate.py` before and after each change and see what actually
moves the number. Things to try:

- Subject only, versus subject plus body
- Adding the customer name (does it help? probably not — test it)
- Truncating very long bodies to the first 500 characters

The other tuning surface is `prompts/triage.md`, which Mitchy owns. Coordinate
with her rather than both editing it.

---

## Task 3 — Add real metrics to the run summary

Open `logging_utils.py`. It's four plain functions, no classes:

- `start_run()` makes a new log file and hands back its path
- `log_event(log_path, ...)` writes one line to it
- `read_events(log_path)` reads the lines back
- `summarize(log_path)` turns them into numbers

`summarize()` already computes automation rate and average attempts. Your job is
the metric it's missing: **elapsed wall-clock time.**

In `main.py`, log one extra event at the start of the run:

```python
log_event(log_path, "run_started", "-", {})
```

Then in `summarize()`, take the timestamp of the first event and the last one,
and subtract them:

```python
from datetime import datetime

if events:
    started = datetime.fromisoformat(events[0]["timestamp"])
    ended = datetime.fromisoformat(events[-1]["timestamp"])
    elapsed_seconds = (ended - started).total_seconds()
else:
    elapsed_seconds = 0
```

Add `elapsed_seconds` and `seconds_per_ticket` to the dict that `summarize()`
returns.

Turnaround time is one of the four questions the pitch has to answer, so we
need a real number for it.

Test your changes without running the whole pipeline:

```python
import logging_utils as L

path = L.start_run()
L.log_event(path, "triage_complete", "T1", {"category": "billing"})
L.log_event(path, "draft_created", "T1", {"attempt": 1, "draft": "hi"})
L.log_event(path, "auto_sent", "T1", {"draft": "hi"})
print(L.summarize(path))
```

---

## Task 4 — Build the approval queue CLI (this is what we demo)

Open `approval_queue.py`, find `review_queue()`. Right now it prints the queue
and stops. Make it interactive, so a "supervisor" can actually work through it.

```python
def review_queue():
    """Interactive review loop. This is the human checkpoint."""
    queue = load_queue()
    if not queue:
        print("Approval queue is empty. Nothing waiting on a human.")
        return

    print(f"\n{len(queue)} replies waiting for human review.\n")
    decisions = []

    for i, item in enumerate(queue, start=1):
        ticket = item["ticket"]
        verdict = item.get("verdict") or {}

        print("=" * 68)
        print(f"[{i}/{len(queue)}]  Ticket {ticket['ticket_id']}")
        print(f"From:     {ticket['customer_name']}")
        print(f"Subject:  {ticket['subject']}")
        print(f"\nCustomer wrote:\n  {ticket['body']}")
        print(f"\nFLAGGED BECAUSE: {verdict.get('reasoning', 'unknown')}")
        if verdict.get("issues"):
            print("Open issues:")
            for issue in verdict["issues"]:
                print(f"  - {issue}")
        print(f"\nDRAFTED REPLY (attempt {item.get('attempts', '?')}):")
        print("  " + item.get("draft", "(none)").replace("\n", "\n  "))
        print()

        choice = ""
        while choice not in ("a", "r", "s"):
            choice = input("  [a]pprove  [r]eject  [s]kip > ").strip().lower()

        decisions.append({
            "ticket_id": ticket["ticket_id"],
            "decision": {"a": "approved", "r": "rejected", "s": "skipped"}[choice],
        })
        print()

    approved = sum(1 for d in decisions if d["decision"] == "approved")
    print("=" * 68)
    print(f"Reviewed {len(decisions)}: {approved} approved, "
          f"{sum(1 for d in decisions if d['decision'] == 'rejected')} rejected, "
          f"{sum(1 for d in decisions if d['decision'] == 'skipped')} skipped")

    # TODO: write these decisions back into the log so the audit trail is
    # closed-loop. That's the strongest version of this feature: we can show
    # not just what the agent proposed, but what the human decided about it.
```

Test it:

```bash
python main.py --mock
python main.py --review
```

**The detail that makes the demo land:** showing *why* each one was flagged,
right above the draft. That's the difference between "here's a list" and "here's
a supervisor's actual working screen." Spend your polish time there.

---

## Task 5 — Turn on LangSmith tracing (30 minutes, high payoff)

This gives you a professional observability dashboard for free, with zero code
changes.

1. Sign up at smith.langchain.com
2. Create an API key
3. Add to your `.env`:

```
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key_here
LANGSMITH_PROJECT=northstar-triage
```

4. `python main.py --limit 5`
5. Open the LangSmith dashboard

You'll see every model call: the exact prompt sent, the response, how long it
took, how many tokens, and what it cost. **Take screenshots.** They go in the
deck and in your writeup.

**Get the cost-per-ticket number from here** and give it to Mitchy for the
Before/After one-pager and Julian for the pitch. That number is one of the four
questions the assignment requires an answer to.

Worth saying explicitly in your writeup: we have two complementary layers. Our
own JSONL log is the permanent audit record we control and could hand to a
compliance reviewer. LangSmith is the live debugging and cost view. Different
jobs.

---

## Task 6 — Your written deliverable: "What We Keep From the Old Process"

This is arguably the most important written piece, because it's the assignment's
central question. The framing it gives you is a progression:

**Full Approval → Exception-Only → Audit Trail**

Structure your argument like this:

**What the old process had.** A supervisor read every reply before it shipped.
100% human review. Slow, but a customer never received something no person had
seen.

**What we automated away.** Reading and tagging every ticket. Hand-searching the
policy doc. Writing the first draft. Reviewing the routine replies where the
critic found nothing and no flag rule fired.

**What we kept, and why.** A human still reviews every flagged reply. Not
because a person is better at grammar, but because the flag conditions mark the
cases where being wrong is expensive and hard to undo: legal exposure, large
refunds, safety, an already-angry customer. Those are irreversible in a way that
a slightly clumsy sentence isn't.

**What replaced the rest.** Every prompt, draft, verdict, and retry is logged.
The supervisor no longer reads every reply *in advance*, but any reply can be
reconstructed completely *afterward*. That's a different kind of oversight, not
an absence of it.

**Be honest about what we gave up.** A wrong reply can now reach a customer
without a human seeing it first. The critic reduces that risk and we measured
how much (get Julian's number). It doesn't eliminate it. A writeup that admits
this is more credible than one that doesn't, and a grader will notice which one
you wrote.

---

## Definition of done

- [ ] Run summary produces automation rate, avg attempts, and elapsed time
- [ ] Approval queue CLI is interactive and shows why each item was flagged
- [ ] LangSmith on, screenshots captured, cost-per-ticket shared with the team
- [ ] Triage tested against Julian's labeled set
- [ ] "What We Keep" writeup done, including what we gave up
- [ ] Your branch merged into main

---

## Your line in the pitch

"Every prompt, draft, verdict, and retry is recorded. The supervisor no longer
reads every reply in advance, but any reply can be reconstructed completely
afterward. We traded pre-approval for a full audit trail, deliberately."

---

## Where you'll get stuck

**"The log file is empty."** `log_event` only gets called when `main.py` runs
the pipeline. `--review` reads the queue, it doesn't create log events.

**"`input()` doesn't work."** It won't run inside a Jupyter notebook or some
IDE consoles. Run it from a real terminal.

**"`KeyError` when reading a log entry."** Different event types carry different
fields. A `triage_complete` event has no `draft` key. Use `event.get("draft")`
instead of `event["draft"]`.

**"LangSmith shows nothing."** Tracing only fires on real API calls. Mock mode
never touches the network, so there's nothing to trace.
