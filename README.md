# 🎫 Customer Support Ticket Triage — OpenEnv Environment

> **Meta OpenEnv Hackathon Submission**
> An AI agent environment that simulates real-world customer support ticket triage.

---

## 🌐 Domain Overview

Customer support teams receive hundreds of tickets daily. Each ticket must be:

1. **Categorized** — routed to the right team (Refund, TechSupport, Billing, Legal)
2. **Prioritized** — assigned an urgency level (Low, Medium, High, Critical)
3. **Responded to** — given a professional draft reply

This environment presents the agent with a customer email and expects all three outputs in a single step.

---

## 🏗️ Architecture

```
ticket_triage/
├── models.py                # TriageAction, TriageObservation, TriageState
├── client.py                # HTTP client wrapper (TriageEnvClient)
├── baseline.py              # LLM baseline agent (Gemini)
├── inference.py             # HTTP inference script (no direct imports)
├── __init__.py              # Package exports
├── requirements.txt         # Python dependencies
├── openenv.yaml             # OpenEnv manifest
├── README.md                # This file
└── server/
    ├── __init__.py
    ├── environment.py       # TriageEnvironment (reset / step / state)
    ├── app.py               # FastAPI application + custom endpoints
    └── Dockerfile           # Docker container definition
```

---

## 📐 Action / Observation Spaces

### TriageAction (Agent → Environment)

| Field              | Type                                       | Description                                |
| ------------------ | ------------------------------------------ | ------------------------------------------ |
| `category`         | `Refund \| TechSupport \| Billing \| Legal` | Team that should handle the ticket         |
| `urgency`          | `Low \| Medium \| High \| Critical`         | Priority level                             |
| `suggested_reply`  | `string`                                    | Draft response to the customer             |

### TriageObservation (Environment → Agent)

| Field          | Type      | Description                              |
| -------------- | --------- | ---------------------------------------- |
| `ticket_id`    | `string`  | Unique ticket identifier                 |
| `subject`      | `string`  | Email subject line                       |
| `body`         | `string`  | Full email body (on reset)               |
| `sender_email` | `string`  | Customer's email address                 |
| `done`         | `bool`    | `True` after grading                     |
| `reward`       | `float`   | Score in \[0.0, 1.0\]                    |
| `metadata`     | `dict`    | Detailed grading breakdown               |

---

## 📊 Grading Rubric

Each task is scored 0.0 → 1.0 with partial credit:

| Component          | Weight | Criteria                                                    |
| ------------------ | ------ | ----------------------------------------------------------- |
| **Category**       | 0.40   | Exact match against ground truth                            |
| **Urgency**        | 0.40   | Exact match against ground truth                            |
| **Suggested Reply**| 0.20   | Non-empty (+0.05), ≥20 chars (+0.05), keyword hits (+0.10)  |

---

## 🧪 Tasks

| Task ID  | Difficulty | Scenario                                          | Expected Category | Expected Urgency |
| -------- | ---------- | ------------------------------------------------- | ----------------- | ---------------- |
| `easy`   | Easy       | Clear refund request for a damaged product        | Refund            | Medium           |
| `medium` | Medium     | App crash + unauthorized billing charge           | TechSupport       | High             |
| `hard`   | Hard       | GDPR data deletion with legal threat              | Legal             | Critical         |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### 3. Test the Endpoints

```bash
# Health check
curl http://localhost:8000/health

# List tasks
curl http://localhost:8000/tasks

# View grading rubric
curl http://localhost:8000/grader

# Reset with a task
curl -X POST "http://localhost:8000/reset?task_id=easy"

# Submit a triage action
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"category": "Refund", "urgency": "Medium", "suggested_reply": "We will process your refund."}'

# Run built-in baseline
curl -X POST http://localhost:8000/baseline
```

### 4. Run HTTP Inference (No API Key Required)

```bash
python inference.py
```

This script communicates with the server purely over HTTP (`/reset`, `/step`) using a keyword heuristic — proving the API works end-to-end.

### 5. Run the LLM Baseline (Requires Gemini API Key)

```bash
export GEMINI_API_KEY=your-key-here
python baseline.py
```

---

## 🐳 Docker

```bash
# Build
docker build -t ticket-triage -f server/Dockerfile .

# Run
docker run -p 8000:8000 ticket-triage
```

---

## 📡 API Endpoints

| Method | Path        | Description                                     |
| ------ | ----------- | ----------------------------------------------- |
| GET    | `/health`   | Health check                                    |
| POST   | `/reset`    | Reset with `?task_id=easy\|medium\|hard`        |
| POST   | `/step`     | Submit `TriageAction` JSON, receive graded obs  |
| GET    | `/state`    | Current environment state                       |
| GET    | `/tasks`    | List all available tasks with metadata           |
| GET    | `/grader`   | Grading rubric documentation                    |
| POST   | `/baseline` | Run heuristic baseline, returns scores          |

---

## 📜 License

MIT — Built for the Meta OpenEnv Hackathon 2026.
