"""
Orchestrator: runs one ticket through the whole pipeline.

OWNER: Enrique

This is the manager-agent. It doesn't write anything itself. It decides who
runs when, what each agent gets handed, and where a ticket goes at the end.

The three decisions that live in this file, and that we defend in the pitch:
  1. HANDOFF DESIGN  - what does each agent receive? (full ticket? summary?)
  2. RETRY POLICY    - how many times does the critic get to kick it back?
  3. APPROVAL GATE   - what routes to a human vs ships automatically?
"""

from state import Ticket, TicketRun
from agents.triage import run_triage
from agents.drafter import run_drafter
from agents.critic import run_critic
from tools.policy_lookup import lookup_policy
from approval_queue import add_to_queue


# The retry budget. Two means: first draft, one revision, then give up and
# escalate. Higher costs more money and delays the ticket. This number is a
# business decision, not a technical one - be ready to justify it.
MAX_ATTEMPTS = 2


def process_ticket(ticket: Ticket, logger) -> TicketRun:
    """
    Run one ticket end to end.

    Args:
        ticket: the Ticket to process.
        logger: a RunLogger instance.

    Returns:
        TicketRun with final status set.
    """
    run = TicketRun(ticket=ticket)

    # --- Step 1: triage -----------------------------------------------------
    run.triage = run_triage(ticket)
    logger.log("triage_complete", ticket.ticket_id, {
        "category": run.triage.category,
        "priority": run.triage.priority,
        "confidence": run.triage.confidence,
        "reasoning": run.triage.reasoning,
    })

    # --- Step 2: retrieve policy -------------------------------------------
    # HANDOFF DECISION: the drafter gets the full ticket body plus the policy
    # section, but NOT the triage agent's reasoning. We decided the reasoning
    # is for the audit trail, not for the next agent, so it can't bias the
    # drafter. Worth flagging in the pitch as a deliberate choice.
    run.policy_text = lookup_policy(run.triage.category)
    logger.log("policy_retrieved", ticket.ticket_id, {
        "category": run.triage.category,
        "policy_chars": len(run.policy_text),
    })

    # --- Step 3: draft, critique, maybe retry -------------------------------
    while run.attempts < MAX_ATTEMPTS:
        run.attempts += 1

        run.draft = run_drafter(
            ticket=ticket,
            triage=run.triage,
            policy_text=run.policy_text,
            revision_notes=run.revision_notes,
        )
        logger.log("draft_created", ticket.ticket_id, {
            "attempt": run.attempts,
            "draft": run.draft,
        })

        run.verdict = run_critic(
            ticket=ticket,
            triage=run.triage,
            policy_text=run.policy_text,
            draft=run.draft,
        )
        logger.log("critic_verdict", ticket.ticket_id, {
            "attempt": run.attempts,
            "approved": run.verdict.approved,
            "needs_human": run.verdict.needs_human,
            "issues": run.verdict.issues,
            "reasoning": run.verdict.reasoning,
        })

        if run.verdict.approved:
            break

        # Rejected: hand the critic's complaints back to the drafter.
        run.revision_notes = run.verdict.issues

    # --- Step 4: THE APPROVAL GATE ------------------------------------------
    # This is the heart of the assignment. Three outcomes:
    #   auto_sent      - critic approved AND didn't flag for human review
    #   awaiting_human - flagged, or we burned the retry budget
    #   failed         - shouldn't happen, but log it if it does
    #
    # TODO (Enrique): talk through the middle branch with the team. Right now
    # ANY needs_human flag routes to a person. An alternative is a value
    # threshold (refunds over $50 only). Whichever we pick, the one-pager has
    # to justify it.
    if run.verdict and run.verdict.approved and not run.verdict.needs_human:
        run.status = "auto_sent"
        logger.log("auto_sent", ticket.ticket_id, {"draft": run.draft})
    else:
        run.status = "awaiting_human"
        add_to_queue(run)
        reason = ("flagged by critic" if run.verdict and run.verdict.needs_human
                  else f"not approved after {run.attempts} attempts")
        logger.log("escalated_to_human", ticket.ticket_id, {
            "reason": reason,
            "attempts": run.attempts,
            "draft": run.draft,
        })

    return run
