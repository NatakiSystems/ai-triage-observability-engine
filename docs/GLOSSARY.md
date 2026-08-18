# Glossary

Every term we use in the guides, in plain language. Look things up here instead
of guessing from context.

---

## The tools

**Terminal** (also: command line, shell, console) — a window where you type
commands instead of clicking. Open it in VS Code with **Ctrl + `**.

**VS Code** — the editor we write code in. It has the terminal built in, which
is why we use it.

**Directory** — a folder. Same thing. Programmers say directory.

**Path** — a folder's address, like `Desktop/northstar-triage/agents/critic.py`.

**Repository** (repo) — the project folder, with its whole history tracked by
git.

**Library / package / dependency** — code someone else wrote that we use.
`pip install` downloads them. LangChain and Pydantic are ours.

**`pip`** — the tool that installs Python libraries. On a Mac you type `pip3`.

---

## git and GitHub

**git** — the tool that tracks changes. Runs on your computer.

**GitHub** — the website that hosts the shared copy. git is the tool, GitHub is
the place.

**clone** — download the project to your computer for the first time.

**branch** — your own private copy of the project to work in. Nothing you do on
your branch affects anyone else until it's merged.

**`main`** — the official branch. It must always work. Never commit to it
directly.

**commit** — save a snapshot of your changes, with a note describing them.

**stage** (`git add`) — mark which changes you want in your next commit.

**push** — send your commits up to GitHub.

**pull** — download everyone else's commits to your computer.

**pull request** (PR) — asking for your branch to be merged into `main`.
Enrique reviews and merges.

**merge** — combine your branch's work into `main`.

**merge conflict** — two people changed the same lines and git can't decide
which version wins. You'll see `<<<<<<<` markers in the file. It's a question,
not a disaster.

---

## Python

**Variable** — a name for a value. `count = 5`.

**Function** — a named block of code you can run. `run_triage(ticket)` calls the
function `run_triage` and hands it a ticket.

**Argument / parameter** — the values you hand a function. In
`load_tickets(limit=5)`, `limit=5` is an argument.

**Return** — what a function hands back when it's done.

**Import** — bring in code from another file. `from state import Ticket`.

**Module** — a single `.py` file.

**String** — text. Always in quotes: `"billing"`.

**Integer / float** — a whole number / a decimal number.

**Boolean** — `True` or `False`.

**List** — an ordered collection: `["billing", "technical"]`.

**Dictionary** (dict) — labeled values: `{"category": "billing"}`.

**Class** — a blueprint for an object. `RunLogger` is a class; `logger` is one
made from it.

**Object / instance** — a specific thing made from a class.

**Docstring** — the `"""triple-quoted text"""` at the top of a file or function
explaining what it does.

**Exception / error / traceback** — what you get when something breaks. The
traceback is the list of lines above the error, and it tells you where it
happened.

**`try` / `except`** — "attempt this; if it breaks, do that instead" rather than
crashing.

---

## This project

**Agent** — one AI worker with one job and its own instructions. We have three:
triage, drafter, critic.

**System prompt** — the instructions telling an agent who it is and what to do.
Ours live in `prompts/`.

**Orchestrator** — the code that decides which agent runs when. Ours is
`orchestrator.py`. It's regular Python, not an AI.

**Shared state** — the object passed between agents so each one can see what the
last one did. Ours is `TicketRun` in `state.py`.

**Handoff** — what gets passed from one agent to the next. Deciding what to
include, and what to leave out, is a design decision we defend in the pitch.

**Critic** — the agent that reviews the drafter's work before it ships. Stands
in for the human supervisor.

**Retry loop** — when the critic rejects a draft, the drafter tries again with
the critic's notes. Ours allows 2 attempts.

**Approval gate** — the decision point at the end: does this reply go out
automatically, or does a human see it first?

**Escalate** — send to a human instead of auto-sending.

**Audit trail** — the complete record of everything that happened, so any
decision can be reconstructed later. Ours is `logs/*.jsonl`.

**Mock mode** — `--mock` uses fake canned responses instead of calling the real
AI. Free, instant, no key needed.

**Stub** — a placeholder function that returns something reasonable so the
project runs before the real version is written. Most of your job is replacing
stubs.

---

## AI terms

**LLM** (large language model) — the AI itself. We're using DeepSeek.

**API** — how our code talks to the AI over the internet.

**API key** — the password that proves we're allowed to use it. **Never commit
it.** It lives in `.env`, which git ignores.

**Token** — roughly a word-piece. Models charge per token, so tokens are how
cost gets measured.

**Temperature** — how random the model's output is. `0.1` is consistent and
predictable, `0.9` is creative and varied. Triage and critic run low; the
drafter runs a bit warmer.

**Structured output** — making the model return a strict data shape instead of
free text. LangChain's `with_structured_output()` does this, and it's why our
agent files are so short.

**Hallucination** — the model confidently inventing something false. In our
project, the drafter inventing a policy that doesn't exist. The critic's main
job is catching this.

**LangChain** — the library we use to talk to the model.

**Pydantic** — the library that defines and validates our data shapes.
`state.py` is all Pydantic.

**JSONL** — a file with one JSON object per line. Our log format. Easy to read
line by line, and a crash mid-run doesn't corrupt what's already written.
