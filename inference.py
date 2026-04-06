# ============================================================
# Customer Support Ticket Triage — HTTP Inference Script
# ============================================================
# Demonstrates end-to-end interaction with the FastAPI server
# using pure HTTP requests (no direct environment imports).
#
# Usage:
#   1. Start the server:  uvicorn server.app:app --port 8000
#   2. Run inference:     python inference.py
# ============================================================

import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def run_task(task_id: str) -> dict:
    """
    Run a single triage task against the FastAPI server over HTTP.

    1. POST /reset?task_id=<id>  — load the ticket into the environment
    2. POST /step                — submit a heuristic triage action and get graded feedback

    Returns the graded observation dict from the /step response.
    """

    # ── Step 1: Reset the environment ─────────────────────────
    reset_resp = requests.post(f"{BASE_URL}/reset", params={"task_id": task_id})
    reset_resp.raise_for_status()
    observation = reset_resp.json()

    ticket_id = observation.get("ticket_id", "unknown")
    customer_message = observation.get("customer_message", "")
    print(f"   Ticket ID : {ticket_id}")
    print(f"   Message   : {customer_message[:80]}...")

    # ── Step 2: Build a simple heuristic action ───────────────
    # (In production, an LLM agent would generate this action)
    action = _heuristic_action(task_id, customer_message)

    # ── Step 3: Submit the action via /step ────────────────────
    step_resp = requests.post(f"{BASE_URL}/step", json=action)
    step_resp.raise_for_status()
    result = step_resp.json()

    reward = result.get("reward", 0.0)
    feedback = result.get("feedback", "")
    print(f"   ★ Reward  : {reward}")
    print(f"   Feedback  : {feedback}")

    return result


def _heuristic_action(task_id: str, message: str) -> dict:
    """
    Simple keyword-based heuristic to produce a triage action.
    This shows the agent logic is decoupled from the environment.
    """
    message_lower = message.lower()

    if "refund" in message_lower or "return" in message_lower:
        return {
            "category": "Refund",
            "urgency": "Medium",
            "suggested_reply": (
                "Thank you for reaching out about your refund request. "
                "We will process your refund within 3-5 business days."
            ),
        }
    elif "crash" in message_lower or "bug" in message_lower or "error" in message_lower:
        return {
            "category": "TechSupport",
            "urgency": "High",
            "suggested_reply": (
                "We're sorry about the technical issue you're experiencing. "
                "Our engineering team is investigating and will follow up shortly."
            ),
        }
    elif "gdpr" in message_lower or "legal" in message_lower or "lawyer" in message_lower:
        return {
            "category": "Legal",
            "urgency": "Critical",
            "suggested_reply": (
                "We take data privacy and legal compliance very seriously. "
                "Our legal team will review your request and respond within 24 hours."
            ),
        }
    else:
        return {
            "category": "Billing",
            "urgency": "Low",
            "suggested_reply": (
                "Thank you for contacting support. "
                "We'll review your inquiry and get back to you soon."
            ),
        }


def main():
    print("=" * 60)
    print("  Customer Support Ticket Triage — HTTP Inference")
    print(f"  Server: {BASE_URL}")
    print("=" * 60)

    # ── Verify server is running ──────────────────────────────
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        health.raise_for_status()
        print(f"  ✓ Server is healthy: {health.json()}\n")
    except requests.ConnectionError:
        print("  ✗ ERROR: Cannot connect to server.")
        print(f"    Start it with: uvicorn server.app:app --port 8000")
        sys.exit(1)

    # ── Fetch available tasks ─────────────────────────────────
    tasks_resp = requests.get(f"{BASE_URL}/tasks")
    tasks_resp.raise_for_status()
    tasks = tasks_resp.json()
    print(f"  Found {len(tasks)} tasks\n")

    # ── Run each task ─────────────────────────────────────────
    total_score = 0.0

    for task in tasks:
        task_id = task["task_id"]
        difficulty = task.get("difficulty", "?")
        print(f"── Task: {task_id} ({difficulty}) ──")

        result = run_task(task_id)
        total_score += float(result.get("reward", 0.0))
        print()

    # ── Summary ───────────────────────────────────────────────
    print("=" * 60)
    print(f"  AGGREGATE SCORE: {total_score:.4f}  ({len(tasks)} tasks)")
    print("=" * 60)


if __name__ == "__main__":
    main()
