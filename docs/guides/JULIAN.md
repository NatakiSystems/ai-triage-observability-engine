# Julian — QA / Critic Engineer

**You own:** `agents/critic.py`, `prompts/critic.md`, the labeled evaluation set,
and the 5-minute pitch deck.

**Your job in one sentence:** you are the supervisor's second look. Everything
the team claims about quality has to be something your critic actually enforces.

You also own the only numbers in this project. Right now nobody can answer "is
it any good?" After Task 3, you can. That number goes on the pitch slide and
it's the most valuable thing anyone on this team produces.

---

## Task 1 — Understand the two-boolean design (read this twice)

The critic returns two separate flags:

```python
approved: bool      # is the WRITING good enough to send?
needs_human: bool   # should a PERSON see it regardless?
```

A reply can be beautifully written and still need a human. Customer mentions a
lawyer, the draft is polite and accurate, and it still must not auto-send.

Collapsing these into one flag is the obvious first instinct and it's wrong.
This distinction is basically the whole answer to the assignment's "which human
checkpoint survives" question. **Make sure you can explain it in two sentences**,
because it's the thing a grader is most likely to probe.

---

## Task 2 — Set the rules

Open `prompts/critic.md`. Two lists.

**Rejection rules** (send it back to Mitchy's drafter to fix):
1. States a policy not in the retrieved policy text
2. Contains a number, date, or timeframe it was never given
3. Promises something the policy doesn't authorize
4. Doesn't answer what the customer asked
5. Tone would upset an already-frustrated customer

**Escalation rules** (`needs_human = true`, even when well written):
- legal threat, safety issue, refund over $100, cancellation request,
  category mismatch

**Bring both lists to the group meeting.** These are business rules, not
technical ones, and the whole team has to agree. Every line you add makes the
system safer and less useful. That tradeoff is the project.

**Write specific issues.** The drafter only sees your `issues` list, not your
reasoning:
- Useless: "the tone is off"
- Useful: "the closing line is dismissive; the customer already said they tried
  restarting"

---

## Task 3 — Build the labeled set (schedule this early)

Nobody can measure anything until this exists.

**Run a one-hour group session.** Five people, Lance's ~30 tickets, everyone
labels 6. You own the file.

Create `data/labeled_tickets.csv`:

```csv
ticket_id,expected_category,expected_needs_human,notes
NS-1001,billing,FALSE,clear duplicate charge
NS-1006,billing,TRUE,mentions contacting a lawyer
NS-1008,returns,TRUE,refund over $100
NS-1010,other,FALSE,general pricing question
```

**Rules for the session:**
- Label what the answer *should* be, without looking at what the system said.
  Looking first will bias you and the number becomes meaningless.
- Disagreements are the valuable part. If two of you disagree on a ticket, that
  ticket is genuinely ambiguous, which means the agent should return **low
  confidence** on it. Note those.
- Don't skip the hard ones. A labeled set of only easy tickets produces a
  flattering, useless accuracy number.

---

## Task 4 — Write the scoring script

Create `scripts/evaluate.py`. This is your headline deliverable.

```python
"""
Measure triage accuracy against our hand-labeled set.

Usage:
    python scripts/evaluate.py --mock      # sanity check, meaningless numbers
    python scripts/evaluate.py             # the real number
"""

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

parser = argparse.ArgumentParser()
parser.add_argument("--mock", action="store_true")
args = parser.parse_args()
if args.mock:
    os.environ["NORTHSTAR_MOCK"] = "1"

from agents.triage import run_triage
from tools.ticket_source import load_tickets

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS = os.path.join(HERE, "data", "labeled_tickets.csv")

with open(LABELS, newline="", encoding="utf-8") as f:
    expected = {r["ticket_id"]: r["expected_category"] for r in csv.DictReader(f)}

tickets = [t for t in load_tickets() if t.ticket_id in expected]

correct = 0
wrong = []
low_confidence = 0

for ticket in tickets:
    result = run_triage(ticket)
    want = expected[ticket.ticket_id]
    if result.category == want:
        correct += 1
    else:
        wrong.append((ticket.ticket_id, want, result.category, result.confidence))
    if result.confidence < 0.70:
        low_confidence += 1

total = len(tickets)
print(f"\nTriage accuracy: {correct}/{total} = {correct / total * 100:.1f}%")
print(f"Low confidence (routed to human): {low_confidence}/{total}")

if wrong:
    print("\nMisclassified:")
    for tid, want, got, conf in wrong:
        print(f"  {tid}: expected {want}, got {got} (confidence {conf:.2f})")
    print("\nCheck whether the wrong ones had LOW confidence. If they did, the")
    print("system caught its own mistake and routed to a human. That's a good")
    print("result and worth saying out loud in the pitch.")
```

Run it:

```bash
python scripts/evaluate.py --mock     # confirms the script works
python scripts/evaluate.py            # the real number
```

**The insight to look for:** if the misclassified tickets mostly had low
confidence, the system knew it was unsure and escalated. That's a far more
interesting finding than raw accuracy, and it's the kind of thing that makes a
pitch land.

---

## Task 5 — Prove your critic actually catches things

A critic that approves everything is worse than no critic, because it creates
false confidence. Test it deliberately.

**Deliberately break the drafter, temporarily:**

1. Open `prompts/drafter.md`
2. Add: `Always tell the customer they have 90 days to return any item.`
3. That contradicts the 14-day policy, so your critic must reject it
4. `python main.py --limit 5`
5. Check the log for rejections:

```bash
python -c "
import json, glob
for line in open(sorted(glob.glob('logs/*.jsonl'))[-1]):
    e = json.loads(line)
    if e['event_type'] == 'critic_verdict' and not e['approved']:
        print(e['ticket_id'], '->', e['issues'])
"
```

6. **Put the drafter prompt back.** Tell Mitchy what you did first.

If the critic didn't catch it, your rules are too loose. This test is a real
result: "we validated the critic by injecting a known policy violation and
confirming it was caught in N of N cases" is a strong line in the deck.

---

## Task 6 — Tune the confidence floor and measure the tradeoff

In `agents/critic.py`:

```python
CONFIDENCE_FLOOR = 0.70
```

Run the pipeline at 0.60, 0.70, and 0.80 and record the automation rate each
time. You'll get a table like:

| Floor | Auto-sent | To human |
|---|---|---|
| 0.60 | 78% | 22% |
| 0.70 | 65% | 35% |
| 0.80 | 41% | 59% |

**That table is your best pitch slide.** It shows the business the dial they
actually control and lets them pick their own risk tolerance. Being able to say
"you tell us the number and we'll set it" is a much stronger position than
defending a value you picked yourself.

---

## Task 7 — Your written deliverable: the 5-minute pitch

The assignment asks four questions. Answer each directly.

**What are the costs?** Cost per ticket from Nataki's logs, times volume, plus
whatever setup time you estimate.

**What is the turnaround?** From 18 hours to whatever the auto-send path
measures, and be honest that flagged tickets still wait for a human.

**What are the risks?** Be specific rather than reassuring. A wrong reply can
now reach a customer without a person seeing it. The critic reduces that, and
your Task 5 test gives you a number for how well. The floor table shows the
dial. Say what's still unmitigated.

**Do we need anyone to manage this?** Yes, and say so. Someone works the
approval queue. Someone updates the policy KB when policy changes. Roughly one
person part-time instead of six full-time. **Do not claim it runs itself.**
Overclaiming is how pitches lose credibility in the Q&A.

Rough structure, 5 minutes is short:
1. The problem, in numbers (30s)
2. What we built, using the architecture diagram (60s)
3. Live demo or screenshots (90s)
4. Results: accuracy, automation rate, the floor table (60s)
5. Risks and what we keep from the old process (60s)
6. What it costs and who runs it (30s)

---

## Definition of done

- [ ] Rejection and escalation rules agreed by the group
- [ ] `data/labeled_tickets.csv` with ~30 labeled tickets
- [ ] `scripts/evaluate.py` working, real accuracy number recorded
- [ ] Critic validated by injecting a known policy violation
- [ ] Confidence floor tradeoff table at three settings
- [ ] Pitch deck built and rehearsed
- [ ] Your branch merged into main

---

## Your line in the pitch

"We validated the critic by injecting a known policy violation and confirming it
was caught. We also measured what happens at three confidence thresholds, so the
business can pick its own risk tolerance rather than accepting ours."

---

## Where you'll get stuck

**"The critic approves everything."** Your rules are too vague. Replace "check
the reply is accurate" with the numbered specific rules. Models follow concrete
instructions far better than general ones.

**"The critic rejects everything and every ticket hits max retries."** Too
strict, or Mitchy's policy KB is too thin for the drafter to work with. Talk to
her before changing your rules. Usually it's the policy, not the critic.

**"Accuracy is only 60%."** That is a finding, not a failure. Report it
honestly, look at *which* tickets failed, and check whether they had low
confidence. A system that knows when it's unsure is worth more than one that's
confidently wrong. Graders reward honest measurement over inflated numbers.

**"scripts/evaluate.py can't find my modules."** The `sys.path.insert` line at
the top handles that. Run it from the project root.
