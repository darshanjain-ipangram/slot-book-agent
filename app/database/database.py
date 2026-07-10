from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


from app.config.settings import POSTGRES_URL


# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    POSTGRES_URL,
    echo=False,         
    pool_pre_ping=True,  
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ── Base class for all ORM models ─────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


def get_db():

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Creates all tables defined in ORM models.
    Called once on application startup.
    """
    # Import models so SQLAlchemy registers them before creating tables
    from app.database import models
    Base.metadata.create_all(bind=engine)
