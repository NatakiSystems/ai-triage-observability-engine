"""
Shared LLM layer, built on LangChain. Every agent calls the model through here.

OWNER: nobody / shared infrastructure. Don't edit without telling the team.

Why this file exists: if all five agents each wrote their own model call, we'd
have five different bugs. One file means one place to fix things, one place to
swap models, and one place to add mock mode.

WHAT LANGCHAIN BUYS US
----------------------
1. `with_structured_output(SomeModel)` - the model returns a validated Pydantic
   object instead of a string we have to hope is JSON. No parsing, no stripping
   code fences. This is the biggest reliability win in the project.
2. One model interface. Swap DeepSeek for OpenAI by changing two lines in .env.
3. LangSmith tracing for free. Set two env vars, no code changes. See
   .env.example.

WHAT WE DELIBERATELY DID NOT USE
--------------------------------
`create_agent`. That builds a loop where the MODEL decides which tool to call
next. Our pipeline is a fixed sequence: triage, policy, draft, critic, every
time. A model-driven loop could skip the critic on some runs, and "every reply
gets reviewed" is the core promise of our business case. Explicit orchestration
guarantees it.

MOCK MODE
---------
Run with --mock and this returns canned responses instead of calling the API.
Build and test your piece in mock mode first: no API key, no cost, no waiting.
"""

import os
import time

from langchain_openai import ChatOpenAI

from state import TriageResult, CriticVerdict


# --------------------------------------------------------------------------
# Mock responses: fixed fake answers, used when --mock is on.
# --------------------------------------------------------------------------

MOCK_TRIAGE = TriageResult(
    category="billing",
    priority="normal",
    confidence=0.93,
    reasoning="MOCK: canned triage result.",
)
# To see the escalation path in mock mode, drop the confidence above to 0.5
# (below CONFIDENCE_FLOOR in agents/critic.py) and run again. Everything will
# route to the human queue instead of auto-sending.

MOCK_CRITIC = CriticVerdict(
    approved=True,
    issues=[],
    needs_human=False,
    reasoning="MOCK: canned critic verdict.",
)

MOCK_DRAFT = (
    "MOCK DRAFT: Hi there, thanks for reaching out. I've looked into the charge "
    "on your account and confirmed it was a duplicate. I've issued a refund, "
    "which should appear in 3-5 business days.\n\nBest,\nNorthstar Support"
)


def is_mock():
    """True when the --mock flag was passed to main.py."""
    return os.environ.get("NORTHSTAR_MOCK") == "1"


# --------------------------------------------------------------------------
# The model
# --------------------------------------------------------------------------

def get_model(temperature):
    """
    Build a LangChain chat model pointed at whatever's in .env.

    Args:
        temperature: 0.0 is consistent, 1.0 is creative. Triage and critic run
                     low (0.1) so they behave the same way twice. The drafter
                     runs warmer (0.5) since it's writing to a person.

    Returns:
        ChatOpenAI configured for our provider.
    """
    return ChatOpenAI(
        model=os.environ.get("MODEL", "deepseek-chat"),
        base_url=os.environ.get("BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ.get("LLM_API_KEY"),
        temperature=temperature,
        timeout=60,
        max_retries=3,      # LangChain handles the waiting-and-retrying for us
    )


def call_structured(prompt_name, user_message, schema, agent_name, temperature):
    """
    Ask the model for a validated object rather than free text.

    `with_structured_output(schema)` sends our Pydantic class to the API as a
    schema and returns an instance of that class. If the model returns
    something malformed we get a clear error naming the field, instead of a
    mystery crash three functions later.

    Args:
        prompt_name:  which file in prompts/ to use as the system prompt
        user_message: the ticket / draft / task content
        schema:       a Pydantic class from state.py (e.g. TriageResult)
        agent_name:   "triage" or "critic" - which canned mock answer to use
        temperature:  keep this low for structured tasks

    Returns:
        An instance of `schema`.
    """
    if is_mock():
        time.sleep(0.1)     # pretend latency so the demo feels real
        return MOCK_TRIAGE if agent_name == "triage" else MOCK_CRITIC

        # method="function_calling" matters. LangChain's default is a strict JSON
    # schema format that OpenAI supports and DeepSeek does not - you get a
    # 400 "This response_format type is unavailable now". Function calling is
    # supported by both, and it still sends our Pydantic schema (including the
    # Field descriptions) so we keep validation and the tuning surface.
    model = get_model(temperature).with_structured_output(
        schema, method="function_calling"
    )
    return model.invoke([
        ("system", load_prompt(prompt_name)),
        ("human", user_message),
    ])


def call_text(prompt_name, user_message, agent_name, temperature):
    """
    Ask the model for plain text. Used by the drafter, because a customer reply
    is prose, not a data structure.

    Returns:
        str: the model's reply.
    """
    if is_mock():
        time.sleep(0.1)
        return MOCK_DRAFT

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
