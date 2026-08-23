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
    Interactive review loop. This is the human checkpoint demonstrated live.
    """
    queue = load_queue()
    if not queue:
        print("\nApproval queue is empty. Nothing waiting on a human.\n")
        return

    print(f"\n{len(queue)} replies waiting for human review.\n")
    decisions = []

    for i, item in enumerate(queue, start=1):
        ticket = item.get("ticket") or {}
        verdict = item.get("verdict") or {}

        print("=" * 68)
        print(f"[{i}/{len(queue)}] Ticket {ticket.get('ticket_id', 'Unknown')}")
        print(f"From:     {ticket.get('customer_name', 'Customer')}")
        print(f"Subject:  {ticket.get('subject', '(no subject)')}")
        print(f"\nCustomer wrote:\n {ticket.get('body', '(no body)')}")

        #Hightlight the flag rationale clearly for the human reviewer
        print(f"\nFLAGGED BECAUSE: {verdict.get('reasoning', 'Flagged for supervisor review')}")
        if verdict.get("issues"):
            print("Open issues:")
            for issue in verdict["issues"]:
                print(f" - {issue}")

        draft_text = item.get("draft", "(none)")
        print(f"\nDRAFTED REPLY (attempt {item.get('attempts', 1)}):")
        print(" " + draft_text.replace("\n", "\n "))
        print()

        choice = ""
        while choice not in ("a", "r", "s"):
            choice = input("[a]pprove, [r]eject, [s]kip > ").strip().lower()

        decision_map = {"a": "approved", "r": "rejected", "s": "skipped"}
        decisions.append({
            "ticket_id": ticket.get("ticket_id"),
            "decision": decision_map[choice]
        })
        print()

    print("=" * 68)
    approved_count = sum(1 for d in decisions if d["decision"] == "approved")
    rejected_count = sum(1 for d in decisions if d["decision"] == "rejected")
    skipped_count = sum(1 for d in decisions if d["decision"] == "skipped")

    print(f"Review session completed. Review {len(decisions)} tickets:")
    print(f" - {approved_count} approved")
    print(f" - {rejected_count} rejected")
    print(f" - {skipped_count} skipped\n")