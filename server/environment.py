import uuid
from typing import Any, Dict, List, Optional
from openenv.core.env_server import Environment
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import TriageAction, TriageObservation, TriageState

TASKS: Dict[str, Dict[str, Any]] = {
    "easy": {"ticket_id": "TKT-1001", "subject": "I want a refund for my recent order", "body": "Hi Support,\nI purchased a wireless keyboard three days ago and it arrived with a cracked spacebar. I would like a full refund.\nThanks,\nJohn", "difficulty": "easy", "ground_truth": {"category": "Refund", "urgency": "Low"}, "reply_keywords": ["refund", "order"]},
    "medium": {"ticket_id": "TKT-2045", "subject": "App crashes on login", "body": "Hello,\nI've been experiencing repeated crashes every time I try to log into the mobile app. Additionally, I noticed an unauthorized charge.\nRegards,\nMaria", "difficulty": "medium", "ground_truth": {"category": "TechSupport", "urgency": "High"}, "reply_keywords": ["crash", "investigate"]},
    "hard": {"ticket_id": "TKT-3891", "subject": "GDPR data deletion", "body": "Under Article 17 of the GDPR I formally request deletion of my data. If I do not receive confirmation, my counsel will initiate proceedings.", "difficulty": "hard", "ground_truth": {"category": "Legal", "urgency": "Critical"}, "reply_keywords": ["gdpr", "legal"]}
}

def grade_action(action: TriageAction, task: Dict[str, Any]) -> Dict[str, Any]:
    gt = task["ground_truth"]
    cat_score = 0.40 if action.category.lower() == gt["category"].lower() else 0.0
    urg_score = 0.40 if action.urgency.lower() == gt["urgency"].lower() else 0.0
    reply = action.suggested_reply.strip()
    reply_score = 0.10 if len(reply) > 10 else 0.0
    return {"total_reward": round(cat_score + urg_score + reply_score, 4), "expected_category": gt["category"], "expected_urgency": gt["urgency"]}

class TriageEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self) -> None:
        super().__init__()
        self._tasks = TASKS
        self._active_task = None
        self._active_state = None

    def reset(self, seed=None, task_id=None, episode_id=None, **kwargs) -> TriageObservation:
        task_id = task_id or kwargs.get("task_id", "easy")
        if task_id not in self._tasks: task_id = "easy"
        self._active_task = self._tasks[task_id]
        self._active_state = TriageState(episode_id=episode_id or str(uuid.uuid4()), step_count=0, current_task_index=0, total_score=0.0)
        return TriageObservation(ticket_id=self._active_task["ticket_id"], customer_message=f"Subject: {self._active_task['subject']}\n\n{self._active_task['body']}", difficulty=self._active_task["difficulty"])

    def step(self, action: Any, timeout_s=None, **kwargs) -> TriageObservation:
        if self._active_task is None: return TriageObservation(ticket_id="N/A", done=True, reward=0.0)
        if isinstance(action, dict): action = TriageAction(**action)
        self._active_state.step_count += 1
        grading = grade_action(action, self._active_task)
        return TriageObservation(ticket_id=self._active_task["ticket_id"], done=True, reward=grading["total_reward"], feedback=f"Expected: {grading['expected_category']}")

    @property
    def state(self) -> TriageState: return self._active_state
    def list_tasks(self) -> List[Dict[str, str]]: return [{"task_id": tid, "difficulty": t["difficulty"]} for tid, t in self._tasks.items()]