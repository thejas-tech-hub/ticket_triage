import os
import sys
import json
import requests
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
SERVER_URL = "http://localhost:7860"

def main():
    if not API_KEY:
        print("ERROR: HF_TOKEN environment variable is not set. Export it first.")
        sys.exit(1)

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    session = requests.Session()
    
    print("Fetching tasks from environment...")
    try:
        tasks = session.get(f"{SERVER_URL}/tasks").json()
    except Exception as e:
        print(f"Could not connect to {SERVER_URL}. Is the server running? Error: {e}")
        sys.exit(1)

    total_score = 0.0

    for task in tasks:
        task_id = task["task_id"]
        print(f"\n── Task: {task_id} ──")

        # 1. Reset
        obs = session.post(f"{SERVER_URL}/reset", params={"task_id": task_id}).json()
        
        # 2. LLM Call using OpenAI Client
        prompt = f"""You are a Support AI. Classify this ticket.
Ticket: {obs.get('customer_message')}

Return a JSON object with exactly these keys:
"category": (Must be "Refund", "TechSupport", "Billing", or "Legal")
"urgency": (Must be "Low", "Medium", "High", or "Critical")
"suggested_reply": (A short draft response)"""

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            action = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM Error: {e}")
            action = {"category": "Billing", "urgency": "Low", "suggested_reply": "Error"}

        # 3. Step
        payload = {"action": action}
        if obs.get("session_id"): payload["session_id"] = obs.get("session_id")
        
        result = session.post(f"{SERVER_URL}/step", json=payload).json()
        print(f"Agent Predicted: {action.get('category')} / {action.get('urgency')}")
        print(f"★ Reward: {result.get('reward')}")
        total_score += float(result.get("reward", 0.0))

    print(f"\nAGGREGATE SCORE: {total_score:.4f}")

if __name__ == "__main__":
    main()
