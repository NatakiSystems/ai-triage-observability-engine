"""
Northstar Support Co. - agentic ticket triage prototype.

OWNER: Enrique

Run it:
    python main.py --mock              # no API key needed, canned responses
    python main.py                     # real API calls
    python main.py --limit 5           # only process the first 5 tickets
    python main.py --review            # open the human approval queue
"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Northstar ticket triage pipeline")
    parser.add_argument("--mock", action="store_true",
                        help="use canned LLM responses, no API key needed")
    parser.add_argument("--limit", type=int, default=None,
                        help="only process the first N tickets")
    parser.add_argument("--review", action="store_true",
                        help="open the human approval queue instead of running")
    args = parser.parse_args()

    if args.mock:
        os.environ["NORTHSTAR_MOCK"] = "1"
        print(">> MOCK MODE: no API calls will be made.\n")

    # Imported after the mock flag is set, so the client picks it up.
    from logging_utils import RunLogger
    from orchestrator import process_ticket
    from tools.ticket_source import load_tickets
    from approval_queue import review_queue

    if args.review:
        review_queue()
        return

    if not args.mock and not os.environ.get("LLM_API_KEY"):
        print("ERROR: no LLM_API_KEY set. Copy .env.example to .env and fill it in,")
        print("       or run with --mock to try the pipeline without an API key.")
        sys.exit(1)

    tickets = load_tickets(limit=args.limit)
    print(f"Loaded {len(tickets)} tickets.\n")

    logger = RunLogger()
    results = []

    for ticket in tickets:
        print(f"[{ticket.ticket_id}] {ticket.subject[:55]}")
        run = process_ticket(ticket, logger)
        results.append(run)
        marker = "AUTO" if run.status == "auto_sent" else "HUMAN"
        print(f"    -> {run.triage.category:10s} | {marker:5s} | "
              f"{run.attempts} attempt(s)\n")

    auto = sum(1 for r in results if r.status == "auto_sent")
    human = len(results) - auto

    print("=" * 60)
    print(f"Processed:        {len(results)}")
    print(f"Auto-sent:        {auto}")
    print(f"Needs human:      {human}")
    if results:
        print(f"Automation rate:  {auto / len(results) * 100:.0f}%")
    print(f"Full log:         {logger.path}")
    print("=" * 60)
    print("\nRun `python main.py --review` to work the approval queue.")


if __name__ == "__main__":
    main()
