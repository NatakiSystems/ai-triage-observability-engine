"""
Triage agent: reads a ticket, decides its category and priority.

OWNER: Nataki

This replaces the human step of "read the ticket, tag it billing/technical/returns."
"""

from state import Ticket, TriageResult
from llm_client import call_structured


def run_triage(ticket: Ticket) -> TriageResult:
    """
    Classify one ticket into category, priority, and confidence.
    """
    # Clean whitespace and format the exact payload sent to the LLM
    subject = (ticket.subject or "").strip()
    body = (ticket.body or "").strip()[:500] #truncate to 500 characters to avoid sending too much text to the LLM

    user_message = f"Subject: {ticket.subject}\n\nBody: {ticket.body}"

    return call_structured(
        prompt_name="triage",
        user_message=user_message,
        schema=TriageResult,
        agent_name="triage",
        temperature=0.1,   # low: same ticket should classify the same way twice
    )