# database/connection.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base
from config import settings
import logging

logger = logging.getLogger(__name__)

# ── Create Engine ─────────────────────────────────────────────────────────────
# connect_args only needed for SQLite (for thread safety with FastAPI)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG          # logs all SQL when DEBUG=true
)

# ── Session Factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ── Init DB (create all tables) ───────────────────────────────────────────────
def init_db():
    """
    Creates all tables if they do not exist.
    Call once at application startup.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created / verified successfully.")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


# ── Dependency for FastAPI routes ─────────────────────────────────────────────
def get_db():
    """
    Yields a database session for use in FastAPI dependency injection.
    Automatically closes the session after the request.

    Usage in routes:
        def my_route(db: Session = Depends(get_db)):
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"DB session error: {e}")
        raise
    finally:
        db.close()


# ── Utility: get a plain session (for use outside FastAPI, e.g. agents/tools) ─
def get_db_session() -> Session:
    """
    Returns a raw session for direct use in agent/tool code.
    Caller is responsible for closing it.

    Usage:
        db = get_db_session()
        try:
            # do work
            db.commit()
        finally:
            db.close()
    """
    return SessionLocal()