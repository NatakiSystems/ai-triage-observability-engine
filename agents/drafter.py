"""
Drafter agent: writes the customer-facing reply.

OWNER: Mitchy

This replaces the human step of "look up the policy, write a reply."

This is the one agent that returns plain text rather than a structured object,
because a customer reply is prose. Everything else in the pipeline uses
structured output.

YOUR JOB:
  1. Assemble what the drafter sees: the ticket, the policy, and on a retry,
     the critic's notes about what was wrong last time.
  2. Tune prompts/drafter.md until the critic stops rejecting things for
     avoidable reasons.

The retry path is the interesting one. When the critic kicks a draft back,
this function gets called AGAIN with revision_notes filled in.
"""

from state import Ticket, TriageResult
from llm_client import call_text


def run_drafter(ticket: Ticket, triage: TriageResult, policy_text: str,
                revision_notes: list[str] | None = None) -> str:
    """  
    Draft a reply to one ticket.

    Args:
        ticket:         the original ticket.
        triage:         what the triage agent decided.
        policy_text:    the relevant policy, from tools/policy_lookup.
        revision_notes: strings from the critic. Empty on the first attempt.

    Returns:
        str: the drafted reply, ready for the critic to review.
    """
    revision_notes = revision_notes or []

    parts = [
        f"CUSTOMER: {ticket.customer_name}",
        f"SUBJECT: {ticket.subject}",
        f"MESSAGE: {ticket.body}",
        f"CATEGORY: {triage.category} (priority: {triage.priority})",
        f"RELEVANT POLICY:\n{policy_text}",
    ]

    # TODO (Mitchy): test that this actually changes the output. The most
    # common failure is the model politely ignoring the notes and handing back
    # a near-identical draft. If that happens, the fix is usually in
    # prompts/drafter.md, not here.
    if revision_notes:
        parts.append(
            "A reviewer rejected your previous draft for these reasons:\n"
            + "\n".join(f"- {note}" for note in revision_notes)
            + "\n\nRewrite the reply, fixing these specific problems."
        )

    result = call_text(
        prompt_name="drafter",
        user_message="\n\n".join(parts),
        agent_name="drafter",
        temperature=0.5,   # a little warmth: this is customer-facing writing
    )
    if not isinstance(result, str):
        raise TypeError(f"Expected a string from call_text(), got {type(result).__name__}")
    return result