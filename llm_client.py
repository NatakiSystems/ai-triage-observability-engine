"""
Shared LLM layer, built on LangChain. Every agent calls the model through here.

OWNER: nobody / shared infrastructure. Don't edit without telling the team.

Why this file exists: if all five agents each wrote their own model call, we'd
have five different bugs. One client means one place to fix things, one place
to swap models, and one place to add mock mode.

WHAT LANGCHAIN BUYS US HERE
---------------------------
1. `with_structured_output(SomeModel)` - the model returns a validated Pydantic
   object instead of a string we have to hope is JSON. No more parsing, no more
   "the model wrapped it in ```json fences again" crashes. This is the single
   biggest reliability win in the project.
2. One model interface. Swap DeepSeek for OpenAI by changing two lines in .env.
3. LangSmith tracing for free. Set two env vars and every call shows up in a
   web UI with timings and token counts. See .env.example.

WHAT WE DELIBERATELY DID NOT USE
--------------------------------
`create_agent`. That builds a loop where the MODEL decides which tool to call
next. Our pipeline is a fixed sequence: triage, policy, draft, critic, every
time. A model-driven loop could skip the critic on some runs, and "every reply
gets reviewed" is the core promise of our business case. Explicit orchestration
guarantees it. This is a defensible design decision, not a gap - say so in the
pitch.

MOCK MODE
---------
Run with --mock and this returns canned responses instead of calling the API.
Build and test your piece in mock mode first: no API key, no cost, no waiting.
The canned responses rotate so a mock run exercises all three outcomes
(auto-sent, retried, escalated).
"""

import os
import time

from state import TriageResult, CriticVerdict


# --------------------------------------------------------------------------
# Mock responses
# --------------------------------------------------------------------------

_MOCK_ROTATION = {
    "triage": [
        TriageResult(category="billing", priority="normal", confidence=0.93,
                     reasoning="MOCK: clear billing question."),
        TriageResult(category="technical", priority="high", confidence=0.88,
                     reasoning="MOCK: customer is blocked by a login failure."),
        TriageResult(category="returns", priority="normal", confidence=0.61,
                     reasoning="MOCK: could be returns or billing, low confidence."),
        TriageResult(category="other", priority="low", confidence=0.77,
                     reasoning="MOCK: general question, no clear category."),
    ],
    "critic": [
        CriticVerdict(approved=True, issues=[], needs_human=False,
                      reasoning="MOCK: reply matches policy and tone."),
        CriticVerdict(approved=False,
                      issues=["MOCK: reply states a 30-day return window but policy says 14 days."],
                      needs_human=False,
                      reasoning="MOCK: policy mismatch, sending back for revision."),
        CriticVerdict(approved=True, issues=[], needs_human=True,
                      reasoning="MOCK: customer mentioned legal action, routing to a human."),
    ],
    "drafter": [
        "MOCK DRAFT: Hi there, thanks for reaching out. I've looked into the "
        "charge on your account and confirmed it was a duplicate. I've issued a "
        "refund, which should appear in 3-5 business days.\n\nBest,\nNorthstar Support",
        "MOCK DRAFT (revised): Hi there, thanks for your patience. I've corrected "
        "the details in my previous note and confirmed the timeline against our "
        "policy.\n\nBest,\nNorthstar Support",
    ],
}

_mock_counter = {}


def is_mock():
    return os.environ.get("NORTHSTAR_MOCK") == "1"


def _next_mock(agent_name):
    options = _MOCK_ROTATION.get(agent_name)
    if not options:
        return f"MOCK RESPONSE: no canned reply set for '{agent_name}'."
    index = _mock_counter.get(agent_name, 0)
    _mock_counter[agent_name] = index + 1
    return options[index % len(options)]


# --------------------------------------------------------------------------
# The model
# --------------------------------------------------------------------------

def get_model(temperature=0.3):
    """
    Build a LangChain chat model pointed at whatever's in .env.

    Args:
        temperature: 0.0 is deterministic, 1.0 is creative. Keep triage and
                     critic low (0.1) so they're consistent. The drafter can
                     be warmer (0.5) since it's writing to a person.

    Returns:
        ChatOpenAI configured for our provider.
    """
    # Imported here rather than at the top so mock mode runs with nothing
    # installed except pydantic.
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=os.environ.get("MODEL", "deepseek-chat"),
        base_url=os.environ.get("BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ.get("LLM_API_KEY"),
        temperature=temperature,
        timeout=60,
        max_retries=3,      # LangChain handles the backoff for us
    )


def call_structured(prompt_name, user_message, schema, agent_name, temperature=0.1):
    """
    Ask the model for a validated object rather than free text.

    This is the good one. `with_structured_output(schema)` sends the Pydantic
    model to the API as a JSON schema and returns an instance of that class.
    If the model returns something malformed, you get a clear ValidationError
    instead of a mystery crash three functions later.

    Args:
        prompt_name:  which file in prompts/ to use as the system prompt
        user_message: the ticket / draft / task content
        schema:       a Pydantic class from state.py (e.g. TriageResult)
        agent_name:   "triage" | "critic" - used for mock lookup and logging
        temperature:  keep this low for structured tasks

    Returns:
        An instance of `schema`.
    """
    if is_mock():
        time.sleep(0.1)     # pretend latency so the demo feels real
        return _next_mock(agent_name)

    model = get_model(temperature).with_structured_output(schema)
    return model.invoke([
        ("system", load_prompt(prompt_name)),
        ("human", user_message),
    ])


def call_text(prompt_name, user_message, agent_name, temperature=0.5):
    """
    Ask the model for plain text. Used by the drafter, since a customer reply
    is prose, not a data structure.

    Returns:
        str: the model's reply.
    """
    if is_mock():
        time.sleep(0.1)
        return _next_mock(agent_name)

    model = get_model(temperature)
    response = model.invoke([
        ("system", load_prompt(prompt_name)),
        ("human", user_message),
    ])
    return response.content


def load_prompt(name):
    """Read a system prompt from prompts/. e.g. load_prompt('triage')"""
    path = os.path.join(os.path.dirname(__file__), "prompts", f"{name}.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
