"""
Logging and observability: the full agent exchange, written to disk.

OWNER: Nataki

The assignment calls full exchange logging non-negotiable, and it's also our
strongest answer to "what do we keep from the old process." The supervisor
stops reading every reply, but every reply stays inspectable, forever.

Four plain functions:
    start_run()      -> makes a new log file, returns its path
    log_event(...)   -> writes one line to it
    read_events(...) -> reads the lines back
    summarize(...)   -> turns those lines into the numbers for our deck

Why JSONL and not a .txt file: one JSON object per line means we can load the
whole run into a spreadsheet or a script later, and a crash mid-run doesn't
corrupt what was already written. A prose log is unreadable by anything but a
person.

YOUR JOB:
  1. Add the metrics we need to summarize() - see the TODO there.
  2. Track cost per ticket if you get LangSmith running (see .env.example).
"""

import json
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")


def start_run():
    """
    Begin a new run. Creates the logs folder if needed and picks a filename
    based on the current time, so runs never overwrite each other.

    Returns:
        str: the path of the log file to write to. Pass this to log_event.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(LOG_DIR, f"run_{run_id}.jsonl")


def log_event(log_path, event_type, ticket_id, payload):
    """
    Record one thing that happened, as a single line in the log file.

    Args:
        log_path:   from start_run()
        event_type: "triage_complete", "draft_created", "critic_verdict",
                    "auto_sent", "escalated_to_human"
        ticket_id:  which ticket this is about
        payload:    dict of whatever matters for this event. Include the actual
                    prompt and reply text - that's the point of an audit trail.
    """
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "ticket_id": ticket_id,
    }
    event.update(payload)      # pour the payload's keys in alongside the fixed ones

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")


def read_events(log_path):
    """
    Read a log file back into a list of dicts.

    Returns:
        list[dict]: one per logged event, in the order they happened.
    """
    if not os.path.exists(log_path):
        return []

    events = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def summarize(log_path):
    """
    Turn a run's log into the numbers we put on the pitch slide.

    Returns:
        dict of counts and rates.
    """
    events = read_events(log_path)

    counts = {}
    attempts_per_ticket = {}

    for event in events:
        event_type = event["event_type"]
        counts[event_type] = counts.get(event_type, 0) + 1

        if event_type == "draft_created":
            ticket_id = event["ticket_id"]
            attempt = event.get("attempt", 1)
            if attempt > attempts_per_ticket.get(ticket_id, 0):
                attempts_per_ticket[ticket_id] = attempt

    total = counts.get("triage_complete", 0)
    auto = counts.get("auto_sent", 0)

    if attempts_per_ticket:
        avg_attempts = sum(attempts_per_ticket.values()) / len(attempts_per_ticket)
    else:
        avg_attempts = 0

    # Calculate elapsed wall-clock time and speed per ticket
    if events:
        started = datetime.fromisoformat(events[0]["timestamp"])
        ended = datetime.fromisoformat(events[-1]["timestamp"])
        elapsed_seconds = max(0.0, (ended - started).total_seconds())
    else:
        elapsed_seconds = 0.0

    seconds_per_ticket = round(elapsed_seconds / total, 2) if total else 0.0

    return {
        "log_file": log_path,
        "tickets_processed": total,
        "auto_sent": auto,
        "escalated_to_human": counts.get("escalated_to_human", 0),
        "automation_rate": round(auto / total * 100, 1) if total else 0,
        "avg_attempts_per_ticket": round(avg_attempts, 2),
        "elapsed_seconds": round(elapsed_seconds, 2),
        "seconds_per_ticket": seconds_per_ticket,
        "event_counts": counts,
    }