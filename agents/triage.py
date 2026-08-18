"""
Triage agent: reads a ticket, decides its category and priority.

OWNER: Nataki

This replaces the human step of "read the ticket, tag it billing/technical/returns."

NOTE ON HOW SHORT THIS IS: the validation you'd normally hand-write here
(is the category real? is confidence actually a number between 0 and 1?) is
already handled by the TriageResult model in state.py. LangChain sends that
schema to the model and Pydantic enforces it on the way back. That's the
payoff for using structured output.

YOUR JOB:
  1. Decide what the model actually needs to see (see the TODO below).
  2. Tune prompts/triage.md and the Field descriptions in state.py until
     accuracy on Julian's labeled set is good.
"""

from state import Ticket, TriageResult
from llm_client import call_structured


def run_triage(ticket: Ticket) -> TriageResult:
    """
    Classify one ticket.

    Args:
        ticket: the Ticket to classify.

    Returns:
        TriageResult, already validated. category is guaranteed to be one of
        our four real categories, and confidence is guaranteed to be 0.0-1.0.
    """
    # TODO (Nataki): this user message is bare-bones. Try adding and removing
    # fields and measure what happens to accuracy. Does the model do better
    # with the customer name? The timestamp? For classification, less context
    # is often better, but test it rather than guessing.
    user_message = f"Subject: {ticket.subject}\n\nBody: {ticket.body}"

    return call_structured(
        prompt_name="triage",
        user_message=user_message,
        schema=TriageResult,
        agent_name="triage",
        temperature=0.1,   # low: same ticket should classify the same way twice
    )
