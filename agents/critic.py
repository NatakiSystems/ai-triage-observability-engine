"""
Critic agent: the supervisor's second look, before a reply ships.

OWNER: Julian

This is the most important agent in the system. It's what lets us argue that
quality survives the switch to agents.

Design note worth defending in the pitch: the critic returns TWO booleans, not
one. `approved` means the writing is fine. `needs_human` means a person should
see it regardless (legal threat, big refund, cancellation request). A reply can
be well written AND still need a human. Collapsing these into one flag was the
obvious first move and it was wrong.

YOUR JOB:
  1. Decide what "good" means, in prompts/critic.md.
  2. Decide what forces a human review no matter what.
  3. Tune CONFIDENCE_FLOOR with the team.
"""

from state import Ticket, TriageResult, CriticVerdict
from llm_client import call_structured


# TODO (Julian): tune this with the team. Below this triage confidence we send
# to a human no matter how good the draft looks. Raising it makes the system
# safer and less useful. That tradeoff is the whole pitch, so know your number.
CONFIDENCE_FLOOR = 0.70


def run_critic(ticket: Ticket, triage: TriageResult, policy_text: str,
               draft: str) -> CriticVerdict:
    """
    Review one drafted reply.

    Args:
        ticket:      the original ticket.
        triage:      the triage decision.
        policy_text: the policy the draft was supposed to follow.
        draft:       the reply to review.

    Returns:
        CriticVerdict, validated. If approved is False, `issues` should be
        non-empty and specific enough for the drafter to act on.
    """
    user_message = (
        f"ORIGINAL TICKET:\n{ticket.body}\n\n"
        f"CATEGORY: {triage.category}\n\n"
        f"POLICY THAT APPLIES:\n{policy_text}\n\n"
        f"DRAFTED REPLY TO REVIEW:\n{draft}"
    )

    verdict = call_structured(
        prompt_name="critic",
        user_message=user_message,
        schema=CriticVerdict,
        agent_name="critic",
        temperature=0.1,   # low: the critic should be consistent, not creative
    )

    # Deterministic override: low triage confidence always goes to a person.
    # This is a rule, not a judgement call, so we enforce it in code rather
    # than trusting the model to remember it every single time. Worth calling
    # out in the pitch - not every guardrail should be a prompt.
    if triage.confidence < CONFIDENCE_FLOOR:
        verdict = verdict.model_copy(update={"needs_human": True})

    return verdict
