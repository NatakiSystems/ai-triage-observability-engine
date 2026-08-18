# Enrique — Orchestrator Engineer & Repo Owner

**You own:** `orchestrator.py`, `state.py`, `main.py`, the repo, the
architecture diagram.

**Your job in one sentence:** decide who runs when, what each agent gets handed,
and where a ticket goes at the end. Plus keep `main` working so the team always
has solid ground to stand on.

You have the hardest technical piece and the coordination load. Some of your
tasks below are unblocking other people, so do those first even though they
aren't coding.

---

## Task 1 — Get the repo live (do this today, everyone is waiting)

1. Go to github.com, click **New repository**
2. Name: `northstar-triage`. **Public** (the assignment requires a public link).
   Do **not** check "Add a README" — we already have one.
3. Copy the URL it gives you.
4. In your terminal:

```bash
cd northstar-triage
git init
git add .
git commit -m "Initial scaffold: pipeline, agents, docs"
git branch -M main
git remote add origin https://github.com/<you>/northstar-triage.git
git push -u origin main
```

5. On github.com: **Settings → Collaborators → Add people**. Add all four
   teammates. They each get an email invite they have to accept.
6. Tag this known-good state so we can always come back to it:

```bash
git tag -a v0.1 -m "Working scaffold, mock mode, all stubs green"
git push origin v0.1
```

7. Post the repo link in the group chat along with the Day 0 instructions from
   `docs/START_HERE.md`.

**Check yourself:** open the repo URL in a private browser window. If you can
see the files without logging in, it's public and the submission link will work.

---

## Task 2 — Sort out the API key (unblocks Mitchy and Julian)

They cannot tune prompts against canned mock responses. They need real calls.

1. Confirm your DeepSeek key works:

```bash
cp .env.example .env
# paste your key into .env
python main.py --limit 2
```

You should see real replies, not text starting with "MOCK".

2. Decide with the group how everyone gets access. Two options:
   - **Shared key** (simplest): send it over DM, never in the repo, never in a
     screenshot. Everyone pastes it into their own local `.env`.
   - **Own keys**: DeepSeek is cheap and each person makes their own. Safer,
     slightly more setup friction.
3. Whichever you pick, say clearly in the chat: **`.env` never gets committed.**
   It's already in `.gitignore`, so this should be impossible, but say it anyway.

**Rough cost check:** 12 tickets is roughly 30 model calls. On DeepSeek that's
fractions of a cent. Nobody needs to be afraid of running it. Tell them that,
because people who are scared of the cost will avoid testing.

---

## Task 3 — Run the kickoff meeting (60–90 minutes)

Put `docs/architecture.png` on screen and walk the pipeline left to right. Then
get decisions on these three things. **Write the answers down** — they go in
the pitch, and "we discussed it" isn't the same as "we decided."

**Decision 1: what forces a human review?**
The current list is in `prompts/critic.md`. Legal threats, refunds over $100,
safety issues, cancellation requests, category mismatch. Does the group agree?
Each line you add makes the system safer and less useful. That tradeoff *is*
the project.

**Decision 2: how many retries?**
Currently `MAX_ATTEMPTS = 2` in `orchestrator.py`. First draft, one revision,
then escalate. Higher costs more and delays the ticket. Justify whatever
number you land on.

**Decision 3: what does the drafter get to see?**
Right now it gets the ticket and the policy, but **not** the triage agent's
reasoning. The reasoning is for the audit trail, so it can't bias the draft.
This is the "handoff design" bullet in the assignment. Make sure everyone can
explain it, because a grader may ask any one of you.

Also at this meeting: schedule the ticket-labeling hour from Julian's guide.

---

## Task 4 — Understand your own file

Open `orchestrator.py` and read `process_ticket()` top to bottom. It's about 80
lines and it's the spine of the whole project. Four sections:

1. Triage
2. Policy lookup
3. The draft/critique/retry loop
4. The approval gate

**Trace one ticket by hand.** Add prints and run with `--limit 1`:

```python
print(f">>> triage says: {run.triage}")
print(f">>> policy is {len(run.policy_text)} chars")
print(f">>> draft attempt {run.attempts}")
print(f">>> verdict: {run.verdict}")
```

```bash
python main.py --mock --limit 1
```

Watching the object fill up step by step is the fastest way to actually
understand this. Delete the prints when you're done.

---

## Task 5 — The retry loop is yours to make correct

This is the trickiest logic in the project. Currently:

```python
while run.attempts < MAX_ATTEMPTS:
    run.attempts += 1
    run.draft = run_drafter(..., revision_notes=run.revision_notes)
    run.verdict = run_critic(...)
    if run.verdict.approved:
        break
    run.revision_notes = run.verdict.issues
```

**Verify these three behaviours** in mock mode (the mock critic rejects on its
second call, so this is testable for free):

1. An approved draft breaks out after 1 attempt
2. A rejected draft comes back with `attempts == 2`
3. A draft rejected twice ends up `awaiting_human`, not silently sent

Confirm #3 especially. A bug that ships an unapproved reply is the one failure
that would sink the pitch.

**One improvement worth making:** `revision_notes` currently gets overwritten
each attempt. Consider appending instead, so the drafter sees the whole history
of complaints. Try both, see which produces better revisions.

---

## Task 6 — The approval gate

Bottom of `process_ticket()`. Three outcomes: `auto_sent`, `awaiting_human`,
`failed`.

Right now **any** `needs_human` flag routes to a person. The alternative the
assignment hints at is tiering: auto-send low-value replies, batch-approve
medium ones, individually review high-value ones.

You don't have to build tiering. But you do have to be able to say why you
didn't, and "we chose the conservative version for v1 because a wrong reply
costs more than a slow one" is a perfectly good answer.

**Make sure the log records the reason.** Every escalation writes
`escalated_to_human` with a `reason` field. That's what proves the gate is
working when someone asks.

---

## Task 7 — Merging pull requests (your weekly rhythm)

When someone opens a PR:

```bash
git checkout main
git pull
git checkout their-branch-name
python main.py --mock          # does it still run?
```

- **Runs fine** → merge it on github.com, tell them in chat
- **Broken** → comment on the PR with the error, let them fix it on their
  branch. **Do not fix it yourself on main.** Fixing their code for them is
  faster once and slower every time after.

Merge little and often. A PR sitting open for four days is a merge conflict
waiting to happen.

Tag a new known-good state after any big merge:

```bash
git tag -a v0.2 -m "Real API calls working end to end"
git push origin v0.2
```

---

## Task 8 — Integration test before the demo (do NOT skip)

Two days before you present:

```bash
git checkout main
git pull
rm -rf logs/*.jsonl logs/approval_queue.json
python main.py                 # full run, real API, all 12 tickets
python main.py --review        # work the queue like a supervisor would
```

Watch for: does it finish without crashing, do the numbers look believable, does
the approval queue actually contain the tickets you'd expect a human to see.

Then **rehearse the demo once, out loud, with the terminal you'll actually use.**
Whoever demos should have run the exact commands at least twice before.

---

## Your written deliverable

The architecture diagram is done (`docs/architecture.png`). Your other job is
being able to explain the three design decisions from Task 3 when the grader
asks. Practice saying each in two sentences.

---

## Definition of done

- [ ] Repo public, all four collaborators added, link posted
- [ ] API key working, distributed, cost explained to the team
- [ ] Kickoff meeting held, three decisions written down
- [ ] Retry loop verified for all three behaviours
- [ ] Approval gate logs a reason for every escalation
- [ ] All teammate PRs merged, `main` runs clean
- [ ] Full integration test passed with real API
- [ ] Demo rehearsed at least twice

---

## Where you'll get stuck

**"Someone committed to main by accident."** Recoverable, and much easier before
anyone else pulls. Don't let them try to fix it alone.

**"Two PRs conflict."** Merge the smaller one first, then ask the second person
to `git checkout main && git pull && git merge main` on their branch and resolve
it there. Conflicts get resolved on branches, never on main.

**"My teammate's branch breaks the pipeline."** That's the system working. Main
is fine, that's the whole point of branches. Comment and move on.
