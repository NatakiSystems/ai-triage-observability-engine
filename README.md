# Northstar Support Co. — Agentic Ticket Triage

Multi-agent prototype for The Knowledge House AI Business Solutions Engineering
Fellowship, Phase 2 final project.

**The problem:** six human agents read every ticket, tag it, look up policy, and
draft a reply. A supervisor reviews every reply before it ships. Quality is
high, customers trust it, and average resolution time is 18 hours.

**What we built:** an agent pipeline that does the reading, tagging, lookup, and
drafting, and a critic that stands in for the supervisor's second look. The
human checkpoint survives, but it moves from *every reply* to *flagged replies
only*, with a full audit trail behind every decision.

---

## Quick start

```bash
git clone <this repo>
cd northstar-triage
pip install -r requirements.txt

python main.py --mock          # runs the whole thing, no API key needed
```

**Install the pinned versions.** `requirements.txt` pins exact versions on
purpose. LangChain's API moves fast and most tutorials you'll find online are
written for versions that no longer exist. If we're all on the same versions, a
bug is a real bug instead of a version mismatch nobody can see. Don't bump them
mid-project without telling the group.

You should see 12 tickets process, some auto-sent, some escalated. If that
works, your environment is fine.

To run for real:

```bash
cp .env.example .env           # then paste your key into .env
python main.py --limit 3       # start small, it costs money
python main.py --review        # work the human approval queue
```

**Mock mode is not a toy.** Build and test your piece with `--mock` first. No
API key, no cost, no waiting. Only switch to real calls when your logic works.

---

## Who owns what

**One file, one owner.** If you need something changed in someone else's file,
message them. Don't edit it yourself — that's how merge conflicts happen.

| Owner | Files | What it does |
|---|---|---|
| **Enrique** | `orchestrator.py`, `state.py`, `main.py` | Wires the agents together, owns the approval gate logic and the retry loop |
| **Lance** | `tools/ticket_source.py`, `tools/policy_lookup.py`, `data/tickets.csv` | Gets data into the system: tickets in, policy out |
| **Mitchy** | `prompts/triage.md`, `prompts/drafter.md`, `agents/drafter.py`, `data/policy_kb.md` | The agents' instructions and the policy knowledge base |
| **Julian** | `agents/critic.py`, `prompts/critic.md` | The quality gate: what gets rejected, what gets a human |
| **Nataki** | `agents/triage.py`, `logging_utils.py`, `approval_queue.py` | Classification, the audit trail, and the human review CLI |
| *shared* | `llm_client.py` | LangChain setup + mock mode. Don't edit without telling the team. |

Written deliverables (see the checklist at the bottom) are split so the people
with lighter code loads carry more of the writing.

Every file you own has a docstring at the top explaining the job and `TODO
(YourName)` markers where the real work goes. Search for your name:

```bash
grep -rn "TODO (Mitchy)" .
```

---

## How it works

```
tickets.csv
    |
    v
[ TRIAGE AGENT ] ──> category, priority, confidence
    |
    v
[ policy_lookup ] ──> the relevant policy section
    |
    v
[ DRAFTER AGENT ] <────────────────┐
    |                              │ revision notes
    v                              │
[ CRITIC AGENT ] ──> rejected? ────┘  (max 2 attempts)
    |
    v
  APPROVAL GATE
    |
    ├──> approved + not flagged ──> auto-sent
    └──> flagged or out of retries ──> approval_queue.json ──> human
                                          |
                                          v
                                   python main.py --review
```

Everything that happens gets written to `logs/run_<timestamp>.jsonl`, one JSON
object per event, including the actual draft text at every attempt.

### Three design decisions worth defending in the pitch

**Handoff design.** The drafter receives the ticket body and the policy
section, but *not* the triage agent's reasoning. We decided the reasoning is for
the audit trail, not for the next agent, so it can't bias the draft.

**Retry budget of 2.** First draft, one revision, then escalate. Higher costs
more money and delays the ticket. This is a business decision, not a technical
one.

**LangChain for the model layer, plain Python for the control flow.** We use
`with_structured_output()` so triage and critic return validated objects instead
of strings we have to parse, and LangSmith for tracing. We deliberately did not
use `create_agent`: that hands the model control over which step runs next, and
our approval gate has to fire on every single ticket. Knowing when not to reach
for a tool is part of the design.

**The critic returns two booleans, not one.** `approved` means the writing is
fine. `needs_human` means a person should see it regardless — legal threats,
refunds over $100, cancellation requests. A reply can be well written and
*still* need a human. Collapsing these into one flag was the first thing we
tried and it was wrong.

---

## Deliverable checklist

- [ ] Architecture diagram (Enrique)
- [ ] Working prototype — 2+ agents, separate prompts, shared state, critic/retry, full logging (all)
- [ ] Before/After one-pager: time, cost, headcount (Mitchy)
- [ ] "What We Keep From the Old Process" (Nataki)
- [ ] 5-minute stakeholder pitch deck (Julian)
- [ ] Labeled evaluation set — 20 tickets, 4 each (group hour)
- [ ] Submit repo link to Canvas (one person)
- [ ] Submit public Docs/Slides links to Canvas (one person)

## Team

Enrique Quezada · Lance Gonzalez · Julian Seiferth · Mitchy Derose · Nataki Boykin

## Docs

**New to the project? Open `docs/START_HERE.md` first.**

- `docs/SETUP_FROM_ZERO.md` — **never programmed before? start here.** Installing everything, what a terminal is, your first commit
- `docs/GLOSSARY.md` — every term we use, in plain language
- `docs/START_HERE.md` — setup, order of work, and who does what
- `docs/guides/` — a step-by-step guide for each person, by name
- `docs/architecture.svg` / `.png` — the architecture diagram, drop straight into Slides
- `docs/GIT_GUIDE.md` — git for people who have never used it. Read before your first commit.
- `docs/CONCEPTS.md` — the handful of Python constructs in this repo you may not have seen yet
