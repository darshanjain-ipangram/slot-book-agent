from decouple import config


# ── Application ───────────────────────────────────────────────────────────────
APP_TITLE = config("APP_TITLE", default="Doctor Clinic AI Assistant")
APP_VERSION = config("APP_VERSION", default="1.0.0")
DEBUG = config("DEBUG", default=False, cast=bool)

# ── Groq ──────────────────────────────────────────────────────────────────────
GROQ_API_KEY = config("GROQ_API_KEY")
GROQ_MODEL = config("GROQ_MODEL", default="openai/gpt-oss-120b")

# ── PostgreSQL ─────────────────────────────────────────────────────────────────
POSTGRES_URL = config("POSTGRES_URL")

# ── Redis ──────────────────────────────────────────────────────────────────────
REDIS_URL = config("REDIS_URL")

# ── Cal.com ───────────────────────────────────────────────────────────────────
CALCOM_API_KEY = config("CALCOM_API_KEY", default="")
CALCOM_BASE_URL = config("CALCOM_BASE_URL", default="https://api.cal.com/v2")
CALCOM_EVENT_TYPE_ID = config("CALCOM_EVENT_TYPE_ID", cast=int)
