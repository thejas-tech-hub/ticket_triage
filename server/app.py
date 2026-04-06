# ============================================================
# Customer Support Ticket Triage — FastAPI Application
# ============================================================
# Creates the HTTP server exposing the TriageEnvironment over
# REST & WebSocket, plus hackathon-required custom endpoints:
#   GET  /tasks     — list available tasks
#   GET  /grader    — grading rubric documentation
#   POST /baseline  — run built-in baseline agent
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Support both in-repo and standalone imports for the env server helper
try:
    from openenv.core.env_server.http_server import create_app
except ImportError:
    # If openenv-core is not installed, create a plain FastAPI app
    create_app = None  # type: ignore[assignment]

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import TriageAction, TriageObservation
from server.environment import TriageEnvironment


# ------------------------------------------------------------------ #
#  App Factory
# ------------------------------------------------------------------ #

def build_app() -> FastAPI:
    """Build the FastAPI application with environment + custom endpoints."""

    env = TriageEnvironment()
    used_openenv = False

    # Try to use the official create_app helper from openenv-core
    if create_app is not None:
        try:
            app = create_app(
                TriageEnvironment,
                TriageAction,
                TriageObservation,
                env_name="ticket_triage",
            )
            used_openenv = True
        except Exception:
            pass

    if not used_openenv:
        app = FastAPI(
            title="Customer Support Ticket Triage — OpenEnv",
            description="AI agent environment for triaging customer support tickets.",
            version="1.0.0",
        )

    # ---- Core REST endpoints ----
    # Only register manual routes if create_app was NOT used,
    # to avoid duplicate /reset and /step routes competing for state.

    @app.get("/health")
    async def health() -> Dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok"}

    if not used_openenv:
        @app.post("/reset")
        async def reset(task_id: str = "easy") -> Dict[str, Any]:
            """Reset the environment with a specific task."""
            obs = env.reset(task_id=task_id)
            return obs.model_dump()

        @app.post("/step")
        async def step(action: TriageAction) -> Dict[str, Any]:
            """Submit a triage action and receive graded feedback."""
            obs = env.step(action)
            return obs.model_dump()

        @app.get("/state")
        async def get_state() -> Dict[str, Any]:
            """Return current environment state."""
            return env.state.model_dump()

    # ---- Hackathon Custom Endpoints (always registered) ----

    @app.get("/tasks", response_class=JSONResponse)
    async def list_tasks() -> List[Dict[str, str]]:
        """
        **GET /tasks** — List all available triage tasks.

        Returns metadata (task_id, difficulty, description) for each task.
        """
        return env.list_tasks()

    @app.get("/grader", response_class=JSONResponse)
    async def grader_info() -> Dict[str, Any]:
        """
        **GET /grader** — Grading rubric documentation.

        Describes how the agent's triage action is scored.
        """
        return {
            "name": "TriageGrader",
            "version": "1.0",
            "max_score": 1.0,
            "components": {
                "category": {
                    "weight": 0.40,
                    "description": (
                        "Exact match of predicted category against ground truth. "
                        "Options: Refund, TechSupport, Billing, Legal."
                    ),
                },
                "urgency": {
                    "weight": 0.40,
                    "description": (
                        "Exact match of predicted urgency against ground truth. "
                        "Options: Low, Medium, High, Critical."
                    ),
                },
                "suggested_reply": {
                    "weight": 0.20,
                    "description": (
                        "Quality of the draft reply. Scored on: "
                        "(a) non-empty (+0.05), "
                        "(b) length >= 20 chars (+0.05), "
                        "(c) keyword relevance (up to +0.10)."
                    ),
                },
            },
            "partial_credit": True,
            "notes": (
                "Scores range from 0.0 (all wrong) to 1.0 (perfect). "
                "Partial credit is awarded independently for each component."
            ),
        }

    @app.post("/baseline", response_class=JSONResponse)
    async def run_baseline() -> Dict[str, Any]:
        """
        **POST /baseline** — Run a simple rule-based baseline against all tasks.

        Returns per-task and aggregate scores.
        """
        results: Dict[str, Any] = {}
        total_reward = 0.0

        # Simple heuristic baseline (no LLM required)
        heuristic_map = {
            "easy": TriageAction(
                category="Refund",
                urgency="Medium",
                suggested_reply=(
                    "Thank you for contacting us about your refund request. "
                    "We will process your order refund within 3-5 business days."
                ),
            ),
            "medium": TriageAction(
                category="TechSupport",
                urgency="High",
                suggested_reply=(
                    "We're sorry about the app crash and the unexpected charge. "
                    "Our team will investigate the issue and get back to you urgently."
                ),
            ),
            "hard": TriageAction(
                category="Legal",
                urgency="Critical",
                suggested_reply=(
                    "We take GDPR data deletion requests very seriously. "
                    "Our legal and privacy compliance team will ensure your data "
                    "is deleted in accordance with legal requirements."
                ),
            ),
        }

        for task_id, action in heuristic_map.items():
            env.reset(task_id=task_id)
            obs = env.step(action)
            results[task_id] = obs.model_dump()
            total_reward += obs.reward

        avg_reward = round(total_reward / len(heuristic_map), 4)
        return {
            "baseline_type": "heuristic",
            "per_task": results,
            "aggregate_score": avg_reward,
            "total_tasks": len(heuristic_map),
        }

    return app


# ---- Module-level app instance for uvicorn ----
app = build_app()


def main() -> None:
    """Entry point for direct execution."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
