# Mitchy — Prompt Engineer

**You own:** `prompts/triage.md`, `prompts/drafter.md`, `agents/drafter.py`,
`data/policy_kb.md`, and the Before/After one-pager.

**Your job in one sentence:** the agents do what you tell them, so you decide
what they're told and what they're allowed to know.

You need real API calls to do your job well. Mock responses are canned, so they
can't tell you whether a prompt is good. Get the API key from Enrique early.

---

## Task 1 — See what the drafter currently produces (30 minutes)

```bash
cp .env.example .env
# paste the key Enrique gives you
python main.py --limit 3
```

Then read the actual drafts in the log:

```bash
python -c "
import json, glob
path = sorted(glob.glob('logs/*.jsonl'))[-1]
for line in open(path):
    e = json.loads(line)
    if e['event_type'] == 'draft_created':
        print('=' * 60)
        print(f\"{e['ticket_id']} attempt {e['attempt']}\")
        print(e['draft'])
"
```

Read them like a customer would. Too formal? Too vague? Does it promise
something the policy didn't authorize? **Write down three specific complaints.**
Those are your first three fixes.

---

## Task 2 — Understand your two tuning surfaces

This trips people up, so read it carefully. Your prompts live in **two** places.

**1. `prompts/*.md`** — persona, rules, tone, what to do and not do. Normal
prompt writing.

**2. `Field(description=...)` in `state.py`** — LangChain sends these to the
model as part of the schema. They describe individual output fields.

```python
confidence: float = Field(
    ge=0.0, le=1.0,
    description="How certain you are, 0.0 to 1.0. Be honest - if the ticket "
                "could reasonably be two categories, say 0.6, not 0.95."
)
```

That description is doing prompt work. Rewriting it changes agent behaviour.

**`state.py` is Enrique's file.** Don't edit it directly, or you'll create a
merge conflict. Send him the exact replacement wording and let him commit it.
Annoying, but one file with one owner is what keeps this project from breaking.

**Rule of thumb:** how the agent *behaves* goes in the prompt file. What a
*field means* goes in the Field description.

---

## Task 3 — Expand the policy knowledge base

Open `data/policy_kb.md`. The drafter can only state policy that appears here.
If it's thin, the drafter either says "I'll pass you to a specialist" constantly
or invents things, and Julian's critic rejects it.

**Structural rule you cannot break:** the `## header` names must exactly match
the categories in `state.py` — `billing`, `technical`, `returns`, `other`. Lance's
lookup matches on those headers. Rename one and the policy silently goes missing.

Add specifics for each category. Real numbers, real timeframes. Every ticket
Lance writes should have a policy that answers it.

Verify after editing:

```python
from tools.policy_lookup import load_policy_sections
s = load_policy_sections()
print(list(s.keys()))          # must be exactly the four category names
print(len(s['billing']), 'chars of billing policy')
```

---

## Task 4 — Tune the drafter prompt, one change at a time

Open `prompts/drafter.md`. The workflow:

1. Change **one** thing
2. `python main.py --limit 3`
3. Read the drafts
4. Better or worse?
5. Repeat

**One change at a time.** Change three things and you won't know which one
helped. This is slow and it is the actual job.

Things worth trying:

- **Add examples.** Two or three "here's a ticket, here's a good reply" pairs
  usually beat any amount of rule-writing. This is the single highest-leverage
  change available to you.
- **Tighten rule 2** (never invent a number). It's the rule that breaks most
  often and the one Julian's critic will reject you for.
- **Test length.** Try "three to five sentences" versus "four to six" and see
  what the critic says.
- **Test the escalation path.** Feed it a ticket with no matching policy. Does
  it correctly say it's passing to a specialist, or does it make something up?
  Making something up is the worst failure mode we have.

Keep notes on what you tried. Some of it goes in the pitch.

---

## Task 5 — Make the retry path actually work

This is the piece most likely to be quietly broken, and it's the "retry logic"
bullet in the assignment rubric.

When Julian's critic rejects a draft, `run_drafter` gets called again with
`revision_notes` filled in. **The common failure is the model politely ignoring
the notes and returning a near-identical draft.**

Test it directly:

```python
from state import Ticket, TriageResult
from agents.drafter import run_drafter

ticket = Ticket(ticket_id="T1", customer_name="Dana", subject="Refund",
                body="I was charged twice for the same order.",
                received_at="2026-08-04T09:00:00")
triage = TriageResult(category="billing", priority="normal",
                      confidence=0.9, reasoning="test")
policy = "Duplicate charges are refunded in full within 60 days. Refunds take 3-5 business days."

first = run_drafter(ticket, triage, policy)
print("FIRST DRAFT:\n", first)

second = run_drafter(ticket, triage, policy,
                     revision_notes=["The reply never tells the customer how long the refund takes."])
print("\nREVISED DRAFT:\n", second)
```

The second draft must visibly fix the named problem. If it doesn't, strengthen
the revision instructions in `prompts/drafter.md`. Something like: *"You are
revising a rejected draft. Address every listed problem explicitly. Do not
rewrite parts that were not criticized."*

---

## Task 6 — Your written deliverable: the Before/After one-pager

Current process, from the assignment:
- 6 human agents
- reads every ticket, tags, looks up policy, drafts a reply
- supervisor reviews every reply
- **18 hour average resolution time**
- can't scale in seasonal spikes without temp hires

After, from our actual run. **Use real numbers from the logs, not guesses.**
Get these from Nataki's run summary:
- automation rate (what % went out without a human)
- average attempts per ticket
- cost per ticket
- wall-clock time per ticket

For staff hours, state your assumptions in the document. Something like: "at an
estimated 12 minutes of agent time per ticket and 3 minutes of supervisor
review, 100 tickets/day is roughly 25 staff-hours. At a 70% automation rate,
supervisor review drops to the flagged 30%."

**Include the risk column.** A one-pager that only shows savings reads as a
sales pitch. What we're trading: a wrong reply can now reach a customer without
a human seeing it. Say what mitigates that (the critic, the flag rules, the
audit log) and say plainly what it doesn't fully solve.

---

## Definition of done

- [ ] Policy KB covers every ticket category with real specifics
- [ ] Section headers exactly match the four category names
- [ ] Drafter prompt has worked examples in it
- [ ] Retry path verified: a revised draft visibly fixes the named problem
- [ ] Drafter correctly escalates when no policy matches instead of inventing
- [ ] Before/After one-pager written, with real numbers and a risk section
- [ ] Your branch merged into main

---

## Your line in the pitch

"The drafter can only state policy that was retrieved for it. When no policy
matches, it escalates instead of guessing. We tested that path deliberately
rather than assuming it."

---

## Where you'll get stuck

**"Policy comes back as NO POLICY FOUND."** A `##` header in `policy_kb.md`
doesn't match a category name exactly. Check spelling and capitalization.

**"My prompt change did nothing."** Two likely causes: the temperature is high
enough that you're seeing noise (run the same ticket 3 times to check), or the
behaviour you're trying to change lives in the Field description in `state.py`,
not the prompt file.

**"Every draft gets rejected by the critic."** Talk to Julian before changing
anything. It may be his rules that are too strict, not your prompt. This is a
conversation, not a solo debugging session.

**"It's slow."** Real API calls take a few seconds each. Use `--limit 3` while
you're iterating.
