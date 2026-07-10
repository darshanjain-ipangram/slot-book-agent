

from fastapi import FastAPI

from app.database.database import create_tables
from app.api.routes import router


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI()

# ── Register routes ───────────────────────────────────────────────────────────
app.include_router(router)


# ── Startup event ─────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    """
    Runs once when the server starts.
    Creates all database tables if they don't already exist.
    """
    create_tables()


