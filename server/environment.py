import uuid
from typing import Any, Dict, List, Optional
from openenv.core.env_server import Environment

import sys
import os
# Ensure the project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import TriageAction, TriageObservation, TriageState

# ------------------------------------------------------------------ #
#  Task Definitions
# ------------------------------------------------------------------ #
TASKS: Dict[str, Dict[str, Any]] = {
    "easy": {
        "ticket_id": "TKT-1001",
        "subject": "I want a refund for my recent order",
        "body": "Hi Support,\nI purchased a wireless keyboard three days ago and it arrived with a cracked spacebar. I would like a full refund.\nThanks,\nJohn",
        "sender_email": "john@example.com",
        "ground_truth": {"category": "Refund", "urgency": "Low"},
        "reply_keywords": ["refund", "order", "process", "sorry"],
        "difficulty": "easy",
        "description": "Clear refund request for a damaged product.",
    },
    "medium": {
        "ticket_id": "TKT-2045",
        "subject": "App crashes on login & unexpected charge",
        "body": "Hello,\nI've been experiencing repeated crashes every time I try to log into the mobile app. Additionally, I noticed a $14.99 charge on my credit card that I did not authorize.\nRegards,\nMaria",
        "sender_email": "maria@example.com",
        "ground_truth": {"category": "TechSupport", "urgency": "High"},
        "reply_keywords": ["crash", "app", "charge", "investigate", "billing"],
        "difficulty": "medium",
        "description": "Technical issue combined with an unauthorized billing complaint.",
    },
    "hard": {
        "ticket_id": "TKT-3891",
        "subject": "GDPR data deletion & potential legal action",
        "body": "To Whom It May Concern,\nUnder Article 17 of the GDPR I am formally requesting the complete deletion of all personal data your company holds on me. If I do not receive written confirmation within 72 hours, my legal counsel will initiate proceedings.\nSincerely,\nDr. Petrova",
        "sender_email": "legal@petrova.eu",
        "ground_truth": {"category": "Legal", "urgency": "Critical"},
        "reply_keywords": ["gdpr", "data", "deletion", "legal", "compliance"],
        "difficulty": "hard",
        "description": "GDPR data deletion request with explicit legal threat.",
    },
}

# ------------------------------------------------------------------ #
#  Grader Utility
# ------------------------------------------------------------------ #
def grade_action(action: TriageAction, task: Dict[str, Any]) -> Dict[str, Any]:
    gt = task["ground_truth"]

    # Category & Urgency
    category_score = 0.40 if action.category.lower() == gt["category"].lower() else 0.0
    urgency_score = 0.40 if action.urgency.lower() == gt["urgency"].lower() else 0.0

    # Reply quality
    reply = action.suggested_reply.strip()
    reply_score = 0.0
    if len(reply) > 0:
        reply_score += 0.05
        if len(reply) >= 20: reply_score += 0.05
        keywords = task.get("reply_keywords", [])
        if keywords:
            hits = sum(1 for kw in keywords if kw.lower() in reply.lower())
            reply_score += round(0.10 * (hits / len(keywords)), 4)

    total_reward = round(category_score + urgency_score + min(reply_score, 0.20), 4)

    return {
        "total_reward": total_reward,
        "expected_category": gt["category"],
        "expected_urgency": gt["urgency"]
    }

# ------------------------------------------------------------------ #
#  Environment
# ------------------------------------------------------------------ #
class TriageEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = False
    
    # THE NUCLEAR OPTION: Global Class Memory
    # This completely bypasses OpenEnv's session manager bugs.
    _active_task = None
    _active_state = None

    def __init__(self) -> None:
        super().__init__()
        self._tasks = TASKS

    def close(self):
        pass

    def reset(self, seed=None, task_id=None, episode_id=None, **kwargs) -> TriageObservation:
        task_id = task_id or kwargs.get("task_id", "easy")
        if task_id not in self._tasks:
            task_id = "easy"

        # Lock the task into GLOBAL memory
        TriageEnvironment._active_task = self._tasks[task_id]
        TriageEnvironment._active_state = TriageState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            current_task_index=list(self._tasks.keys()).index(task_id),
            total_score=0.0
        )

        return TriageObservation(
            ticket_id=TriageEnvironment._active_task["ticket_id"],
            customer_message=f"Subject: {TriageEnvironment._active_task['subject']}\n\n{TriageEnvironment._active_task['body']}",
            difficulty=TriageEnvironment._active_task["difficulty"],
            done=False,
            reward=0.0,
            feedback="Classify this ticket by category and urgency, then draft a reply."
        )

    def step(self, action: Any, timeout_s=None, **kwargs) -> TriageObservation:
        # Read directly from GLOBAL memory
        if TriageEnvironment._active_task is None:
            return TriageObservation(
                ticket_id="N/A", done=True, reward=0.0,
                customer_message="", difficulty="",
                feedback="Error: No task loaded. Call reset() first."
            )

        if isinstance(action, dict):
            action = TriageAction(**action)

        TriageEnvironment._active_state.step_count += 1
        grading = grade_action(action, TriageEnvironment._active_task)

        return TriageObservation(
            ticket_id=TriageEnvironment._active_task["ticket_id"],
            customer_message="", 
            difficulty=TriageEnvironment._active_task["difficulty"],
            done=True,
            reward=grading["total_reward"],
            feedback=f"Score: {grading['total_reward']} | Expected: {grading['expected_category']} / {grading['expected_urgency']}"
        )

    @property
    def state(self) -> TriageState:
        return TriageEnvironment._active_state

    def list_tasks(self) -> List[Dict[str, str]]:
        return [{"task_id": tid, "difficulty": t["difficulty"], "description": t["description"], "ticket_id": t["ticket_id"]} for tid, t in self._tasks.items()]