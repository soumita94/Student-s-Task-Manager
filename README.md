# AI-Assisted Student Task & Schedule Manager

An intelligent academic productivity system built for the **B.Tech (Second Year)** course at **UEM Kolkata**, specializing in **Artificial Intelligence**.

Moving beyond passive task logging (CRUD), this system optimizes student focus by **mathematically prioritizing tasks** using a custom Urgency/Importance algorithm and **predicting task durations** based on historical behavioral data.

## 🚀 Key AI Specializations

### 1. Dynamic Priority Scoring (Phase 2)
The core of the system is the priority engine. It replaces static chronological sorting with a mathematical matrix (Urgency vs. Importance).
- **Urgency Factor:** Calculated from the remaining time until the deadline.
- **Importance Factor:** Derived from the **User-Assigned Importance** (1-5) and specific academic **Category Weights**.

Example Weighting:
* **DSA Practice:** 1.5x
* **Exam Prep:** 1.3x
* **Project Work:** 1.2x
* **General Assignment:** 1.0x

### 2. Behavioral Duration Prediction (Phase 3)
Integrated with **Scikit-learn (Linear Regression)**, the system:
1.  Stores both the **User's Estimated Duration** and the **Actual Completion Time**.
2.  Trains a simple regression model on historical task data.
3.  Automatically calculates a **Predicted Duration** (adding a personalized "procrastination buffer") when scheduling future work in that category.

### 3. NLP Structuring Interface (Phase 4)
Integrated with **OpenAI GPT-4o** to reduce the friction of manual task logging.
- **Input:** "Add a DBMS assignment due next Friday 5pm, high priority, 2 hours."
- **Output:** The backend calls GPT-4o to parse and map this natural language into the strict JSON schema required by the `TaskCreate` model.

---

## 🛠️ Technical Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | **FastAPI** (Python 3.11+, Asynchronous) |
| **Frontend** | **Streamlit** (User Interface) |
| **Database** | **SQLite** + **SQLAlchemy ORM** (Persistence) |
| **AI/NLP** | **Gemini 2.5 flash API** (Structured Parsing) |
| **ML Engine** | **Scikit-learn** (Behavioral Regression) |
| **Deployment** | **Render / Streamlit Cloud** (Microservices) |

---

## 📁 System Architecture

```text
ai-scheduler-mvp/
├── backend/               # FastAPI Microservice (Deployed on Render)
│   ├── app/
│   │   ├── routers/        # APIRouters (Tasks, NLP, Analytics)
│   │   ├── services/       # Priority Engine, NLP Parser
│   │   ├── models.py       # SQLAlchemy DB Schema (defines 'Task')
│   │   ├── schemas.py      # Pydantic Schemas (input validation)
│   │   └── database.py     # Connection & Session Management
│   ├── .env.example        # Environment Variable Templates
│   ├── main.py             # FastAPI App Initialization
│   └── requirements.txt
├── frontend/              # Streamlit Microservice (Deployed on Streamlit Cloud)
│   ├── app.py              # Main UI, HTTP calls to Backend
│   └── requirements.txt
└── README.md              # Project Master Specification