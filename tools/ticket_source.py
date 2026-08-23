# Reviewed by Lance - confirmed load_tickets() and structure, 8/19
"""
Ticket source: loads incoming tickets from our fake "support inbox".

OWNER: Lance

In the real world this would be a Zendesk API. For the prototype it's a CSV,
which is fine and worth saying out loud in the pitch: the interface is what
matters, not where the rows come from.

YOUR JOB:
  1. Load tickets from data/tickets.csv into Ticket objects.
  2. (Stretch) Add a SQLite version so we can say "real data source" honestly.
  3. Handle a malformed row without crashing the whole run.
"""

import csv
import os

from state import Ticket

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tickets.csv")


def load_tickets(limit=None):
    """
    Load tickets from the CSV.

    Args:
        limit: if set, only return the first N tickets. Useful for demos.

    Returns:
        list[Ticket]
    """
    tickets = []
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_number, row in enumerate(reader, start=2):
            try:
                # TODO (Lance): a row with a missing column will blow up here.
                # Wrap this in a try/except, skip bad rows, and print a warning.
                tickets.append(Ticket(
                    ticket_id=row["ticket_id"],
                    customer_name=row["customer_name"],
                    subject=row["subject"],
                    body=row["body"],
                    received_at=row["received_at"],
                ))
            except Exception as e:
                print(f" WARNING: skipping row {row_number} in tickets.csv - {e}")
                continue   

            if limit and len(tickets) >= limit:
                break
    return tickets
