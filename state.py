"""
Shared state for the Northstar triage pipeline.

OWNER: Enrique (Orchestrator)

This file is the CONTRACT between everyone's code. Every agent reads from and
writes to a TicketRun. If you need a new field, message Enrique rather than
editing this file yourself, so we don't get merge conflicts.

These are Pydantic models, not plain classes. That matters: LangChain's
`with_structured_output()` takes one of these and forces the model to return
data in exactly this shape. If the model tries to invent a category we didn't
ask for, Pydantic rejects it before it reaches our code.

Nothing in here calls an LLM or touches the network. It is just shapes.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# Literal means "only these exact strings are allowed, nothing else."
# This is the validation, right here. No if-statements needed.
Category = Literal["billing", "technical", "returns", "other"]
Priority = Literal["low", "normal", "high"]


class Ticket(BaseModel):
    """One incoming customer support ticket, loaded from data/tickets.csv."""
    ticket_id: str
    customer_name: str
    subject: str
    body: str
    received_at: str


class TriageResult(BaseModel):
    """
    What the triage agent decides about a ticket.

    The `description` on each field is not a comment - LangChain sends these
    to the model as part of the schema. Better descriptions here mean better
    output. This is a real place to tune the agent's behaviour.
    """
    category: Category = Field(
        description="The single best category for this ticket."
    )
    priority: Priority = Field(
        description="high if the customer is blocked, money is at risk, or "
                    "they are clearly upset. low for simple questions."
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="How certain you are, 0.0 to 1.0. Be honest - if the "
                    "ticket could reasonably be two categories, say 0.6, "
                    "not 0.95. Low confidence routes to a human, which is "
                    "the correct outcome for an ambiguous ticket."
    )
    reasoning: str = Field(
        description="One sentence explaining the choice, for the audit trail."
    )


class CriticVerdict(BaseModel):
    """What the critic agent decides about a drafted reply."""
    approved: bool = Field(
        description="True only if the reply is ready to send as written."
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Specific, actionable problems with the draft. Empty if "
                    "approved. 'The tone is off' is useless - 'the closing "
                    "line is dismissive when the customer already said they "
                    "tried restarting' is useful."
    )
    needs_human: bool = Field(
        description="True if a person must see this regardless of quality."
    )
    reasoning: str = Field(
        description="One or two sentences, for the audit trail."
    )


class TicketRun(BaseModel):
    """
    The full lifecycle of one ticket moving through the pipeline.

    The orchestrator creates one per ticket and hands it to each agent in
    turn. Each agent fills in its own section. At the end the whole object is
    logged, and that is our audit trail.
    """
    ticket: Ticket
    triage: Optional[TriageResult] = None
    policy_text: str = ""
    draft: str = ""
    attempts: int = 0
    verdict: Optional[CriticVerdict] = None
    status: Literal["pending", "auto_sent", "awaiting_human", "failed"] = "pending"
    revision_notes: list[str] = Field(default_factory=list)

    def to_dict(self):
        """Flatten to a plain dict so it can be written to the log as JSON."""
        return self.model_dump()
