##clinic slot booking Agent
```
doctor-clinic-agent/
│
├── app/
│   ├── agent/
│   │   ├── graph.py       # LangGraph workflow (next phase)
│   │   ├── state.py       # Agent state definition (next phase)
│   │   ├── nodes.py       # Graph nodes (next phase)
│   │   ├── tools.py       # Agent tools (next phase)
│   │   ├── prompts.py     # Prompt templates (next phase)
│   │   └── memory.py      # Redis checkpointer (next phase)
│   │
│   ├── api/
│   │   ├── routes.py      # FastAPI endpoints
│   │   └── schemas.py     # Pydantic request/response models
│   │
│   ├── services/
│   │   ├── calcom.py      # Cal.com API client (next phase)
│   │   ├── groq_client.py # Groq SDK wrapper
│   │   └── conversation.py# Database helpers for conversations
│   │
│   ├── database/
│   │   ├── database.py    # SQLAlchemy engine + session
│   │   └── models.py      # ORM models (conversation table)
│   │
│   ├── config/
│   │   └── settings.py    # All settings via python-decouple
│   │
│   ├── main.py            # FastAPI app + startup
│   └── __init__.py
│
├── docker-compose.yml     # Redis + PostgreSQL containers
├── pyproject.toml         # uv project config + dependencies
├── .env                   # Environment variables (fill in your keys)
└── README.md
```

---

## Database

Only **one table** is used: `conversation`.

| Column | Type | Description |
|---|---|---|
| id | Integer | Auto-incremented primary key |
| session_id | String(255) | Groups messages into a session |
| human_message | Text | The user's message |
| ai_message | Text | The AI's response |
| timestamp | DateTime | When the exchange happened |

---

## Quick Start

### 1. Clone / navigate to the project

```bash
cd doctor-clinic-agent
```

### 2. Fill in your `.env` file

Open `.env` and replace the placeholder values:

```
GROQ_API_KEY=your_real_groq_api_key
POSTGRES_URL=postgresql://postgres:postgres@postgres:5432/clinic_db
REDIS_URL=redis://redis:6379/0
```

### 3. Start Redis and PostgreSQL

```bash
docker compose up -d
```

Verify both containers are healthy:

```bash
docker compose ps
```

### 4. Install dependencies with uv

```bash
uv sync
```

### 5. Run the API server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will:
- Automatically create the `conversation` table on first startup
- Be accessible at `http://localhost:8000`
- Serve interactive docs at `http://localhost:8000/docs`

---

#
### Example: Chat request

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user-001", "message": "I need to book an appointment."}'
```

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `APP_TITLE` | `Doctor Clinic AI Assistant` | API title shown in docs |
| `APP_VERSION` | `1.0.0` | API version |
| `DEBUG` | `False` | Enable debug mode |
| `GROQ_API_KEY` | — | **Required.** Your Groq API key |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Model to use |
| `POSTGRES_URL` | — | **Required.** Full PostgreSQL connection URL |
| `REDIS_URL` | — | **Required.** Full Redis connection URL |
| `CALCOM_API_KEY` | — | Cal.com API key *(next phase)* |
| `CALCOM_BASE_URL` | `https://api.cal.com/v2` | Cal.com base URL |

---



##Use this command for view converstation history
docker exec -it clinic_postgres psql -U postgres -d clinic_db -c "SELECT * FROM conversation;"
