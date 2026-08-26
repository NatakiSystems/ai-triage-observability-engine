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
        verdict.needs_human = True

    return verdict
"""
Task 6 - tune CONFIDENCE_FLOOR and measure the tradeoff.

OWNER: Julian (this measures agents/critic.py, which is mine)

Produces the pitch-slide table:

    Floor    Auto-sent    To human
    0.60         ...%         ...%
    0.70         ...%         ...%
    0.80         ...%         ...%

Run it:
    python scripts/sweep_floor.py --mock          # smoke test the harness only
    python scripts/sweep_floor.py                 # real run, this is the one
    python scripts/sweep_floor.py --limit 10      # smaller/cheaper real run

Writes logs/floor_sweep.json (raw per-ticket numbers) and prints the table.
Keep that JSON. When someone in the pitch asks where the table came from, the
answer is a file, not a memory.


WHY THIS RUNS THE PIPELINE ONCE, NOT THREE TIMES
------------------------------------------------
The floor is a post-hoc override. Look at run_critic in agents/critic.py: it
only ever flips needs_human to True. It cannot change triage confidence, the
draft, the retry loop, or the critic's own verdict. Nothing upstream of it
depends on it.

So three separate `python main.py` runs would differ for two reasons mixed
together: the floor moved, AND the model re-rolled every triage/draft/critic
call. That second source of variation lands straight in the numbers on the
slide. One pass, three floors computed from it, isolates the variable: same
tickets, same drafts, same critic verdicts, only the dial moves. It is also
1/3 the API spend.


WHY IT PATCHES THE FLOOR TO 0.0 FIRST
-------------------------------------
With the floor live, needs_human comes back already merged: for any ticket
under the floor you cannot tell whether the critic flagged it on the merits or
whether the floor flagged it. The raw critic signal is masked exactly where
the sweep needs it.

(Same reason you cannot reconstruct this table from an existing
logs/run_*.jsonl: the logged needs_human is post-override. A log captured at
0.70 can answer 0.70 and 0.80, but not 0.60 - the sub-0.70 tickets have
already been overwritten.)

So: run with the floor disabled, capture the unmasked critic verdict, reapply
each floor in arithmetic afterward.
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict

# Make the repo root importable when running as scripts/sweep_floor.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

FLOORS = [0.60, 0.70, 0.80]
RESULTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs", "floor_sweep.json",
)


@dataclass
class Outcome:
    """The three signals the floor acts on, per ticket."""
    ticket_id: str
    category: str
    confidence: float
    approved: bool          # critic's verdict on the writing
    needs_human: bool       # critic's OWN flag, floor override NOT applied
    attempts: int


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

def collect(limit=None):
    """Run every ticket through the real pipeline once, floor disabled."""
    import agents.critic as critic_mod
    import orchestrator
    from logging_utils import start_run
    from tools.ticket_source import load_tickets

    original_floor = critic_mod.CONFIDENCE_FLOOR
    critic_mod.CONFIDENCE_FLOOR = 0.0

    # The sweep is a measurement, not a production run - it must not dump work
    # into the human queue. Neutralise the enqueue for the duration.
    original_enqueue = orchestrator.add_to_queue
    orchestrator.add_to_queue = lambda run: None

    try:
        tickets = load_tickets(limit=limit)
        log_path = start_run()
        print(f"Sweeping {len(tickets)} tickets (floor disabled for capture).")
        print(f"Pipeline log: {log_path}\n")

        outcomes = []
        for ticket in tickets:
            run = orchestrator.process_ticket(ticket, log_path)
            outcomes.append(Outcome(
                ticket_id=ticket.ticket_id,
                category=run.triage.category,
                confidence=run.triage.confidence,
                approved=bool(run.verdict and run.verdict.approved),
                needs_human=bool(run.verdict and run.verdict.needs_human),
                attempts=run.attempts,
            ))
            print(f"  [{ticket.ticket_id}] conf={run.triage.confidence:.2f} "
                  f"approved={outcomes[-1].approved} "
                  f"critic_flag={outcomes[-1].needs_human}")
        return outcomes
    finally:
        critic_mod.CONFIDENCE_FLOOR = original_floor
        orchestrator.add_to_queue = original_enqueue


# ---------------------------------------------------------------------------
# Arithmetic - mirrors the approval gate in orchestrator.py
# ---------------------------------------------------------------------------

def auto_sent(o: Outcome, floor: float) -> bool:
    """Auto-sent iff the critic approved AND nothing routed it to a person.

    Mirrors orchestrator.py's gate:
        approved and not needs_human
    with the floor's override folded back in.
    """
    if not o.approved:
        return False
    if o.needs_human:
        return False
    return o.confidence >= floor


def sweep(outcomes, floors=FLOORS):
    n = len(outcomes)
    rows = []
    for floor in floors:
        sent = sum(auto_sent(o, floor) for o in outcomes)
        rows.append({
            "floor": floor,
            "auto_sent_n": sent,
            "to_human_n": n - sent,
            "auto_sent_pct": round(100 * sent / n, 1) if n else 0.0,
            "to_human_pct": round(100 * (n - sent) / n, 1) if n else 0.0,
        })
    return rows


def attribution(outcomes, floor):
    """Split the human-routed pile by WHY it went to a human.

    Only `below_floor_only` is the dial. The other two are there at any floor.
    Know this number before the pitch - if it is small, the honest framing is
    that the dial moves a narrow slice, and that is by design.
    """
    return {
        "draft_rejected": sum(1 for o in outcomes if not o.approved),
        "critic_flagged": sum(1 for o in outcomes if o.approved and o.needs_human),
        "below_floor_only": sum(
            1 for o in outcomes
            if o.approved and not o.needs_human and o.confidence < floor
        ),
    }


def render(rows, n):
    lines = [f"Confidence floor sweep  (n = {n} tickets)", "",
             f"{'Floor':<8}{'Auto-sent':>12}{'To human':>12}"]
    for r in rows:
        lines.append(f"{r['floor']:<8.2f}"
                     f"{r['auto_sent_pct']:>11.1f}%"
                     f"{r['to_human_pct']:>11.1f}%")
    return "\n".join(lines)


def warn_if_degenerate(outcomes, rows):
    """Catch the two ways this table comes out looking real but meaning nothing."""
    distinct = {round(o.confidence, 4) for o in outcomes}
    pcts = {r["auto_sent_pct"] for r in rows}

    if len(distinct) == 1:
        conf = distinct.pop()
        print("\n!! WARNING: every ticket has the same triage confidence "
              f"({conf}).")
        print("   Nothing can move between floors, so this table is flat by")
        print("   construction. This is what mock mode does - MOCK_TRIAGE in")
        print("   llm_client.py is hardcoded to confidence=0.93. The real")
        print("   table needs a real run.")
    elif len(pcts) == 1:
        print("\n!! WARNING: all three floors give the same automation rate.")
        print("   Real confidences, but none fall between 0.60 and 0.80, so")
        print("   the dial has nothing to grab. Check the spread printed")
        print("   below before putting this on a slide.")


def main():
    parser = argparse.ArgumentParser(description="Task 6 confidence floor sweep")
    parser.add_argument("--mock", action="store_true",
                        help="canned responses - smoke-tests the harness, "
                             "cannot produce a real table (see warning)")
    parser.add_argument("--limit", type=int, default=None,
                        help="only sweep the first N tickets")
    args = parser.parse_args()

    if args.mock:
        os.environ["NORTHSTAR_MOCK"] = "1"
        print(">> MOCK MODE: harness smoke test only.\n")
    elif not os.environ.get("LLM_API_KEY"):
        print("ERROR: no LLM_API_KEY set. Copy .env.example to .env and fill "
              "it in.")
        print("       --mock will exercise the harness but cannot produce the "
              "table.")
        sys.exit(1)

    outcomes = collect(limit=args.limit)
    if not outcomes:
        print("No tickets loaded.")
        sys.exit(1)

    rows = sweep(outcomes)

    payload = {
        "n_tickets": len(outcomes),
        "mock": bool(args.mock),
        "floors": FLOORS,
        "table": rows,
        "attribution": {f"{f:.2f}": attribution(outcomes, f) for f in FLOORS},
        "per_ticket": [asdict(o) for o in outcomes],
    }
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("\n" + "=" * 60)
    print(render(rows, len(outcomes)))
    print("=" * 60)

    print("\nWhy tickets went to a human:")
    print(f"{'Floor':<8}{'draft rejected':>16}{'critic flagged':>16}"
          f"{'below floor':>14}")
    for f in FLOORS:
        a = attribution(outcomes, f)
        print(f"{f:<8.2f}{a['draft_rejected']:>16}"
              f"{a['critic_flagged']:>16}{a['below_floor_only']:>14}")

    confs = sorted(o.confidence for o in outcomes)
    print(f"\nConfidence spread: min={confs[0]:.2f} "
          f"median={confs[len(confs)//2]:.2f} max={confs[-1]:.2f} "
          f"({len(set(confs))} distinct values)")

    warn_if_degenerate(outcomes, rows)

    print(f"\nRaw per-ticket outcomes -> {RESULTS_PATH}")
    if args.mock:
        print("MOCK RUN - do not put these numbers on the slide.")


if __name__ == "__main__":
    main()
