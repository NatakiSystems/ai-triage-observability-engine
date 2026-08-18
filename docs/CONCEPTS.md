# The handful of things in this codebase you might not have seen yet

If you've done an intro Python course, you know everything here *except*
roughly seven constructs. Here they are, explained in terms of our actual code.
Read this once and the whole repo opens up.

---

## 1. Pydantic models — a labeled container that checks itself

**Where:** `state.py`

You already know dictionaries:

```python
ticket = {"ticket_id": "NS-1001", "subject": "Charged twice"}
print(ticket["subect"])       # typo -> KeyError at runtime, maybe hours later
```

A Pydantic model is the same idea, with the field names and their types locked
in ahead of time:

```python
class Ticket(BaseModel):
    ticket_id: str
    customer_name: str
    subject: str

ticket = Ticket(ticket_id="NS-1001", customer_name="Dana", subject="Charged twice")
print(ticket.subject)         # dot instead of brackets
print(ticket.subect)          # typo -> your editor underlines it before you run
```

`BaseModel` is the Pydantic base class. Inheriting from it is what gives you
the validation.

**The part that matters for us.** Look at `TriageResult`:

```python
Category = Literal["billing", "technical", "returns", "other"]

class TriageResult(BaseModel):
    category: Category
    confidence: float = Field(ge=0.0, le=1.0, description="...")
```

`Literal[...]` means only those exact four strings are allowed. `ge=0.0, le=1.0`
means confidence must be between zero and one. If the model tries to return
`"refunds"` or `1.7`, Pydantic rejects it immediately with a clear error naming
the field.

That validation is **the reason our agent files are so short.** Nataki doesn't
have to write "if category not in CATEGORIES" checks in `triage.py`, because
the check already happened.

**`Field(description=...)` is not a comment.** LangChain sends those
descriptions to the model as part of the request. Rewriting a description is
one of the most effective ways to change how the agent behaves. That's a real
tuning knob, not documentation.

## 2. `str`, `-> TriageResult`, `Optional[...]` — type hints

**Where:** everywhere, in function signatures

```python
def run_triage(ticket: Ticket) -> TriageResult:
```

This reads as: "takes a `Ticket`, gives back a `TriageResult`."

**Python does not enforce any of this.** It's documentation that your editor
can read. If you delete every type hint in the project, the code runs
identically. They're there so you can tell what a function wants without
reading its body.

`Optional[TriageResult]` means "a TriageResult, or `None`." We use it in
`TicketRun` because when a ticket is first created, triage hasn't run yet, so
that field starts empty.

---

## 3. `Field(default_factory=list)` — a fix for one specific Python trap

**Where:** `state.py`, in `TicketRun` and `CriticVerdict`

```python
revision_notes: list[str] = Field(default_factory=list)
```

The trap: if you write `revision_notes: list = []`, Python creates **one** list
and shares it across every object you ever make. Ticket 1's revision notes would
show up in Ticket 2. This is a famous Python gotcha and it produces bugs that
take hours to find.

`default_factory=list` means "make a fresh empty list for each one."

`list[str]` means "a list of strings" — Pydantic will reject a list with a
number in it.

**What you need to do:** nothing. Just don't change it to `= []`.

## 4. `os.path.dirname(__file__)` — finding files reliably

**Where:** `tools/policy_lookup.py`, `logging_utils.py`, `llm_client.py`

```python
KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "policy_kb.md")
```

Ugly, but it solves a real problem. If you write `open("data/policy_kb.md")`,
that path is relative to **wherever you were standing when you ran the
command**, not to where the file lives. Run the script from a different folder
and it breaks.

Reading it inside out:
- `__file__` — the full path of the file this line is written in
- `os.path.dirname(...)` — chop off the filename, leaving the folder
- wrapped twice — go up two folders (from `tools/` to the project root)
- `os.path.join(root, "data", "policy_kb.md")` — build the path, using the
  right slash for Windows or Mac

**What you need to do:** copy the pattern if you add a new data file. Don't
hand-write paths with slashes in them.

---

## 5. Classes and `self` — `RunLogger`

**Where:** `logging_utils.py`. Nataki, this one's yours.

A class is a blueprint. `RunLogger` is a blueprint for a thing that remembers
where it's writing and what it's written so far.

```python
class RunLogger:
    def __init__(self, run_id=None):        # runs once, when you create one
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(LOG_DIR, f"run_{self.run_id}.jsonl")
        self.events = []

    def log(self, event_type, ticket_id, payload):
        ...
        self.events.append(event)            # reaches the SAME list every time
```

`self` means "this particular logger." When `main.py` does
`logger = RunLogger()`, that object now carries its own `run_id`, `path`, and
`events` list around with it. Every call to `logger.log(...)` appends to *that*
logger's list.

Why not just a function? Because a plain function would forget the filename and
the running event list between calls. We'd have to pass them in every time. The
class holds them for us.

**Rule of thumb:** inside a class, any variable you want to survive between
method calls needs `self.` in front of it.

---

## 6. `**payload` — merging one dict into another

**Where:** `logging_utils.py`

```python
event = {
    "timestamp": ...,
    "event_type": event_type,
    **payload,          # <- unpack whatever's in payload, right here
}
```

If `payload` is `{"category": "billing", "confidence": 0.9}`, those two keys get
poured into `event` alongside the fixed ones. It saves writing a loop.

It's why every agent can log completely different fields without us having to
predict them in advance.

---

## 7. `with_structured_output()` — the LangChain piece that matters

**Where:** `llm_client.py`, used by `agents/triage.py` and `agents/critic.py`

```python
model = get_model(temperature).with_structured_output(TriageResult)
result = model.invoke([("system", prompt), ("human", user_message)])
# result is a TriageResult object. Not a string. Not a dict.
```

Without this, talking to a model looks like: get a string back, hope it's JSON,
strip the ```` ```json ```` fences the model added anyway, `json.loads` it, pray
the keys are what you expected, convert the types by hand. Every one of those
steps is a place a beginner project crashes at 11pm.

`with_structured_output(TriageResult)` sends our Pydantic class to the API as a
schema and hands back a real, validated `TriageResult`. The parsing step is gone
entirely.

The drafter doesn't use it, because a customer reply is prose, not a data
structure. It uses `call_text()` instead. That asymmetry is intentional.

---

## What we deliberately did NOT use

**`create_agent`.** LangChain can build an agent loop where the *model* decides
which tool to call next. We didn't, and this is worth saying out loud in the
pitch rather than hiding.

Our pipeline is a fixed sequence: triage, then policy, then draft, then critic,
every time. A model-driven loop could decide to skip the critic on some runs.
"Every reply gets reviewed before it ships" is the core promise of our business
case, and explicit orchestration is what guarantees it.

Knowing when *not* to reach for a tool is a real engineering skill. We used
LangChain for structured outputs, model configuration, and tracing, where it
genuinely removes work. We kept the control flow in plain Python, where it
genuinely matters that the sequence can't vary.

**Also not here:** `async`/`await`, inheritance beyond `BaseModel`, decorators,
deeply nested comprehensions.

---

## When you're stuck

1. Run `python main.py --mock` and see if the pipeline still works
2. Add a `print()` — it's not cheating, it's how everyone debugs
3. Paste the whole error message into a chat with the group, not just the last
   line. The stack trace above the error usually names the file and line.
