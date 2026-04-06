# ============================================================
# Customer Support Ticket Triage — Typed Pydantic Models
# ============================================================
# Defines the Action, Observation, and State models for
# the Ticket Triage environment following the OpenEnv spec.
# ============================================================

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# ---------- Enumerations ----------

class TicketCategory(str, Enum):
    """Supported ticket categories for triage classification."""
    REFUND = "Refund"
    TECH_SUPPORT = "TechSupport"
    BILLING = "Billing"
    LEGAL = "Legal"


class TicketUrgency(str, Enum):
    """Urgency levels for ticket prioritization."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# ---------- Action ----------

class TriageAction(BaseModel):
    """
    Agent action: the triage decision for a customer support ticket.

    The agent reads a ticket (from the Observation) and outputs:
      - category  — what team should handle this ticket
      - urgency   — how quickly the ticket needs attention
      - suggested_reply — a draft response to the customer
    """

    category: str = Field(
        ...,
        description="The support category this ticket belongs to (Refund, TechSupport, Billing, Legal).",
    )
    urgency: str = Field(
        ...,
        description="The urgency level of the ticket (Low, Medium, High, Critical).",
    )
    suggested_reply: str = Field(
        ...,
        min_length=1,
        description="A draft reply to send to the customer addressing their concern.",
    )


# ---------- Observation ----------

class TriageObservation(BaseModel):
    """
    Environment observation: the customer support ticket presented to the agent.

    On `reset()` the environment returns a ticket to classify.
    On `step()` the environment returns grading feedback.
    """

    ticket_id: str = Field(
        ...,
        description="Unique identifier for this support ticket.",
    )
    customer_message: str = Field(
        default="",
        description="The full customer support message including subject and body.",
    )
    difficulty: str = Field(
        default="",
        description="Difficulty level of the task (easy, medium, hard).",
    )
    done: bool = Field(
        default=False,
        description="Whether this episode is finished (True after step).",
    )
    reward: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Grader score from 0.0 to 1.0 awarded after the agent submits its triage action.",
    )
    feedback: str = Field(
        default="",
        description="Grading feedback or instructions from the environment.",
    )


# ---------- State ----------

class TriageState(BaseModel):
    """
    Internal environment state tracking episode progression.
    """

    episode_id: str = Field(
        default="",
        description="UUID identifying the current episode.",
    )
    step_count: int = Field(
        default=0,
        ge=0,
        description="Number of steps taken in the current episode.",
    )
    current_task_index: Optional[int] = Field(
        default=None,
        description="Index of the currently loaded task.",
    )
    total_score: float = Field(
        default=0.0,
        description="Accumulated score across tasks.",
    )
