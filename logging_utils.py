"""
Logging and observability: the full agent exchange, written to disk.

OWNER: Nataki

The assignment calls full exchange logging non-negotiable, and it is also our
strongest answer to "what do we keep from the old process." The supervisor
stops reading every reply, but every reply is still inspectable, forever.

YOUR JOB:
  1. Write one JSON line per event to logs/run_<timestamp>.jsonl
  2. Write a human-readable run summary at the end.
  3. Track cost/token counts if we have time (nice-to-have for the pitch).

Why JSONL and not a .txt file: one JSON object per line means we can load the
whole run into a spreadsheet or a script later. A prose log is unreadable by
anything but a person.
"""

import json
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")


class RunLogger:
    """Logs one full pipeline run."""

    def __init__(self, run_id=None):
        os.makedirs(LOG_DIR, exist_ok=True)
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(LOG_DIR, f"run_{self.run_id}.jsonl")
        self.events = []

    def log(self, event_type, ticket_id, payload):
        """
        Record one event.

        Args:
            event_type: e.g. "triage_complete", "draft_created",
                        "critic_rejected", "escalated_to_human"
            ticket_id:  which ticket this is about.
            payload:    dict of whatever matters. Include the actual prompt
                        and reply text - that's the point of an audit trail.
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            "event_type": event_type,
            "ticket_id": ticket_id,
            **payload,
        }
        self.events.append(event)

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")

    def summary(self):
        """
        Build the end-of-run summary.

        TODO (Nataki): this is the number that goes on the pitch slide. Add
        average attempts per ticket, and total wall-clock time. If you get to
        token counting, total cost per ticket is the single most persuasive
        number we can show a stakeholder.
        """
        counts = {}
        for event in self.events:
            counts[event["event_type"]] = counts.get(event["event_type"], 0) + 1
        return {
            "run_id": self.run_id,
            "log_file": self.path,
            "total_events": len(self.events),
            "event_counts": counts,
        }
