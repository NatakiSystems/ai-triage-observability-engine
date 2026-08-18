# START HERE

Everyone reads this page. Then you read your own guide in `docs/guides/`.

| You are | Your guide |
|---|---|
| Enrique | `docs/guides/ENRIQUE.md` |
| Lance | `docs/guides/LANCE.md` |
| Mitchy | `docs/guides/MITCHY.md` |
| Julian | `docs/guides/JULIAN.md` |
| Nataki | `docs/guides/NATAKI.md` |

---

## What we're building, in three sentences

Northstar Support has six people who read every support ticket, tag it, look up
the policy, write a reply, and get a supervisor to check it. It works, but a
ticket takes 18 hours. We're building agents to do the reading, tagging, lookup,
and drafting, keeping a human checkpoint only on the replies that actually need
one.

**The code already runs.** Nobody is starting from a blank file. Every piece
exists as a working stub, and your job is to replace your stub with the real
thing. If you get stuck, the project still runs, just with your stub in place.

---

## Never programmed before? Start there instead.

If you have never used a terminal, installed Python, or used git, do
**`docs/SETUP_FROM_ZERO.md`** first. It assumes nothing: installing Python and
VS Code, what a terminal is, how to move between folders, and a practice commit
with nothing at stake. Takes about 60-90 minutes.

Come back here when `python main.py --mock` works on your machine.

There's also **`docs/GLOSSARY.md`** — every term we use, in plain language. Look
things up there rather than guessing from context.

---

## Day 0: everyone does this, before anything else

Takes about 20 minutes if you've done this kind of setup before. If you
haven't, use `docs/SETUP_FROM_ZERO.md` instead.

```bash
# 1. Get the code
git clone https://github.com/<enrique>/northstar-triage.git
cd northstar-triage

# 2. Install exactly the pinned versions
pip install -r requirements.txt

# 3. Prove it works
python main.py --mock
```

You should see 12 tickets scroll past, some marked AUTO and some marked HUMAN,
then a summary. **If you see that, you are set up correctly.** If you don't,
post the entire error message in the group chat, not just the last line.

Then read, in this order:

1. `README.md` — 5 minutes
2. `docs/GLOSSARY.md` — skim it, then keep it open while you work
3. `docs/CONCEPTS.md` — 20 minutes, the Python and LangChain constructs in this
   repo you may not have seen before
4. `docs/GIT_GUIDE.md` — 15 minutes, before your first commit
5. Your own guide in `docs/guides/`

---

## Mock mode is your friend

```bash
python main.py --mock          # canned responses, no API key, free, instant
```

Build and test everything in mock mode first. Only switch to real API calls
when your logic already works. Real calls cost money and are slow, and you do
not want to be debugging a typo at 30 seconds a run.

---

## The one rule

**Never commit to `main`.** Work on your own branch, open a pull request,
Enrique merges it. Full instructions in `docs/GIT_GUIDE.md`.

---

## Order of work: who's blocked on whom

**Nobody is blocked right now.** Every stub returns something sensible, so all
five of us can work at the same time from day one. That's deliberate.

Two soft dependencies to be aware of:

- **Mitchy and Julian both need real API calls** to tune prompts. Mock responses
  are canned, so they can't tell you whether a prompt is any good. Enrique gets
  the shared API key sorted in Week 1.
- **Julian's labeled ticket set** makes everyone's tuning measurable. Once it
  exists, "did my change help?" has a real answer instead of a vibe. That's why
  the group labeling hour is early.

---

## Rough two-week shape

**Week 1 — make your piece real**
- Everyone: Day 0 setup, read your guide
- Enrique: repo live, collaborators added, API key distributed
- Group: one-hour ticket labeling session (see Julian's guide)
- Everyone: first PR merged, however small

**Week 2 — tune, measure, write**
- Everyone: your piece working against real API calls
- Julian: accuracy numbers for the deck
- Group: written deliverables
- Enrique: integration test, demo rehearsal

**Get one small PR merged in the first few days,** even a one-line comment fix.
The first PR is the scary one. Do it early, when nothing is at stake.

---

## Written deliverables

| Deliverable | Owner |
|---|---|
| Architecture diagram | Enrique (done, `docs/architecture.png`) |
| Before/After one-pager | Mitchy |
| "What We Keep From the Old Process" | Nataki |
| 5-minute stakeholder pitch deck | Julian |
| Labeled evaluation set | Julian (group hour) |

The people with the lightest code load carry more of the writing. That's on
purpose.

---

## When you're stuck

1. Run `python main.py --mock`. Does the project still work?
2. Add a `print()` to see what a variable actually contains. Not cheating.
3. Post in the group chat with: what you were trying to do, the command you
   ran, and the **entire** error message.
4. Nobody on this team has done this before. Asking early is faster than
   struggling quietly, and it is not a sign of anything.
