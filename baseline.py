import os
import json
import time
from google import genai
from google.genai import types
from models import TriageAction
from client import TriageEnvClient

def main():
    print("============================================================")
    print("  Customer Support Ticket Triage — LLM Baseline")
    print("  Model: gemini-2.5-flash (Strict JSON Mode)")
    print("  Server: http://localhost:8000")
    print("============================================================\n")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        return

    client = genai.Client(api_key=api_key)
    env_client = TriageEnvClient("http://localhost:8000")

    tasks = env_client.list_tasks()
    total_score = 0.0
    
    for task in tasks:
        task_id = task["task_id"]
        difficulty = task["difficulty"]
        print(f"── Task: {task_id} ({difficulty}) ──")
        
        # 1. Reset environment to load the ticket
        obs = env_client.reset(task_id=task_id)
        print(f"   Ticket: {obs.ticket_id}")
        
        # 2. Build the prompt
        prompt = f"""
        You are a Customer Support AI. Read the following ticket and classify it.
        
        TICKET CONTENT:
        {obs.customer_message}
        
        INSTRUCTIONS:
        Return a JSON object with EXACTLY these keys:
        - "category": Must be one of ["Refund", "TechSupport", "Billing", "Legal"]
        - "urgency": Must be one of ["Low", "Medium", "High", "Critical"]
        - "suggested_reply": A short draft response string.
        """
        
        # 3. Ask Gemini using STRICT JSON mode
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            
            action_dict = json.loads(response.text)
            action = TriageAction(**action_dict)
            
        except Exception as e:
            print(f"   \u26a0 LLM Parsing Error: {e}")
            action = TriageAction(category="Billing", urgency="Low", suggested_reply="Error")

        print(f"   Agent Category: {action.category}")
        print(f"   Agent Urgency:  {action.urgency}")
        
        # 4. Step the environment
        result = env_client.step(action)
        
        print(f"   ★ Reward:   {result.reward}")
        print(f"   Feedback:   {result.feedback}\n")
        
        total_score += float(result.reward or 0.0)
        
        # 5. PAUSE FOR RATE LIMITS (10 Seconds)
        time.sleep(10)

    print("============================================================")
    print(f"  AGGREGATE SCORE: {total_score:.4f}  ({len(tasks)} tasks)")
    print("============================================================")

if __name__ == "__main__":
    main()