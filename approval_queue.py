"""
Approval queue: where flagged replies wait for a human.

OWNER: Nataki

This IS the human checkpoint. Everything else in the project is an argument
about what lands in this file and what doesn't.

YOUR JOB:
  1. Write flagged tickets to logs/approval_queue.json
  2. Build a small CLI so a "supervisor" can page through them and
     approve/reject. This is what we demo live.
"""

import json
import os

QUEUE_PATH = os.path.join(os.path.dirname(__file__), "logs", "approval_queue.json")


def add_to_queue(run):
    """
    Add a TicketRun to the human review queue.

    Args:
        run: a TicketRun whose status is "awaiting_human".
    """
    queue = load_queue()
    queue.append(run.to_dict())
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, default=str)


def load_queue():
    """Return the current queue as a list of dicts."""
    if not os.path.exists(QUEUE_PATH):
        return []
    with open(QUEUE_PATH, encoding="utf-8") as f:
        return json.load(f)


def review_queue():
    """
    Interactive review loop for the demo.

    TODO (Nataki): print each queued reply, show WHY it was flagged, and let
    the reviewer type a/r/s (approve, reject, skip). Record the decision back
    into the log so we can show the audit trail is closed-loop.
    """
    queue = load_queue()
    if not queue:
        print("Approval queue is empty. Nothing waiting on a human.")
        return

    print(f"\n{len(queue)} replies waiting for human review.\n")
    for item in queue:
        print("-" * 60)
        print(f"Ticket {item['ticket']['ticket_id']}: {item['ticket']['subject']}")
        verdict = item.get("verdict") or {}
        print(f"Flagged because: {verdict.get('reasoning', 'unknown')}")
        print(f"\nDraft reply:\n{item.get('draft', '(none)')}\n")
    print("-" * 60)
    print("TODO (Nataki): add the approve/reject input loop here.")
