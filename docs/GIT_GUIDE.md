# Git, for people who haven't used it

You need about six commands. That's it. Everything else you can look up later.

## The one rule

**Never commit directly to `main`.** You work on your own branch, you open a
pull request, Enrique merges it. That's the whole system, and it's what keeps
`main` working at all times.

Why this matters: if `main` breaks the night before the demo, we have nothing
to show. If your *branch* breaks, only you are stuck.

---

## First time only

```bash
git clone https://github.com/<enrique>/northstar-triage.git
cd northstar-triage
pip install -r requirements.txt
python main.py --mock
```

If that last command prints tickets, you're set up correctly.

---

## Every time you sit down to work

```bash
git checkout main          # go to the main branch
git pull                   # get everyone else's latest work
git checkout -b yourname/what-youre-doing
```

Branch names: `nataki/triage-agent`, `julian/critic-prompt`, `lance/csv-loader`.
Your name first so we can tell whose branch is whose at a glance.

**Always `git pull` on main before making a new branch.** Skipping this is the
number one cause of ugly merge conflicts.

---

## While you work

```bash
git status                 # what have I changed? run this constantly
git add .                  # stage everything you changed
git commit -m "Add JSON validation to triage agent"
git push -u origin nataki/triage-agent
```

Commit often. Small commits are easier to undo than one giant one.

Write commit messages that finish the sentence "this commit will...":
- Good: `Add fallback when model returns unknown category`
- Bad: `updates`, `fix`, `asdfgh`

The `-u origin <branch>` part is only needed the first time you push a new
branch. After that, plain `git push` works.

---

## When you're done with a piece

1. Go to the repo on github.com
2. You'll see a banner: "yourname/your-branch had recent pushes" → click
   **Compare & pull request**
3. Write a sentence about what you did
4. Click **Create pull request**
5. Tell the group chat
6. Enrique reviews and merges

Then start fresh: `git checkout main`, `git pull`, new branch.

---

## Things that will happen

**"I have uncommitted changes and I need to switch branches."**
```bash
git stash              # put your changes in a drawer
git checkout main
git stash pop          # take them back out
```

**"I committed to main by accident."**
Don't panic and don't try to fix it yourself. Message Enrique. It's recoverable
and it's much easier to fix before anyone else pulls.

**"Git is asking me to write a merge message in a weird editor."**
That's vim. Type `:wq` and press Enter.

**"I pulled and now there are `<<<<<<<` markers in my file."**
That's a merge conflict. The markers show your version and someone else's
version of the same lines. Delete the markers, keep the correct code, save,
then `git add` and `git commit`. If you're unsure which version is right, ask
before guessing.

**"I want to throw away my changes and start over."**
```bash
git checkout -- .          # discards uncommitted changes. Can't be undone.
```

---

## The thing that will actually cause a problem

**Never commit `.env`.** It has our API key in it. Once a key is in git
history it's compromised even if you delete the file afterward — the key has
to be rotated and every commit that touched it lives forever in the log.

`.env` is already in `.gitignore`, so this should be impossible. But if you
ever see `.env` in the output of `git status`, stop and message Enrique before
committing.

---

## Enrique's job (merging PRs)

```bash
git checkout main
git pull
git checkout their-branch
python main.py --mock          # does it still run?
```

If it runs, merge on github.com. If it doesn't, comment on the PR with the
error and let them fix it on their branch. **Do not fix it yourself on main.**

Once a week, or before any big deadline, tag a known-good state:

```bash
git tag -a v0.1 -m "Working pipeline, mock mode, all agents stubbed"
git push origin v0.1
```

That gives us a snapshot we can return to if something goes badly wrong later.
