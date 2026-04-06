import requests
from models import TriageAction, TriageObservation

class TriageEnvClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.http = requests.Session()  # Persistent session for cookies

    def reset(self, task_id: str = "easy") -> TriageObservation:
        payload = {
            "task_id": task_id,
            "kwargs": {"task_id": task_id}
        }
        resp = self.http.post(f"{self.base_url}/reset", json=payload)
        resp.raise_for_status()
        data = resp.json()

        # Capture session/episode ID for session tracking
        self.session_id = data.get("session_id") or data.get("episode_id")

        if "observation" in data:
            return TriageObservation(**data["observation"])
        return TriageObservation(**data)

    def step(self, action: TriageAction) -> TriageObservation:
        payload = {"action": action.model_dump()}
        if hasattr(self, "session_id") and self.session_id:
            payload["session_id"] = self.session_id
            payload["episode_id"] = self.session_id

        resp = self.http.post(f"{self.base_url}/step", json=payload)
        resp.raise_for_status()
        data = resp.json()

        if "observation" in data:
            return TriageObservation(**data["observation"])
        return TriageObservation(**data)

    def list_tasks(self):
        resp = self.http.get(f"{self.base_url}/tasks")
        resp.raise_for_status()
        return resp.json()

    def close(self):
        self.http.close()