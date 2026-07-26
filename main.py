# main.py

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.connection import init_db
from database.seed import seed

# ── Import all routers ────────────────────────────────────────
from api.auth_routes        import router as auth_router
from api.patient_routes     import router as patient_router
from api.workflow_routes    import router as workflow_router
from api.appointment_routes import router as appointment_router
from api.document_routes    import router as document_router
from api.staff_routes       import router as staff_router
from api.escalation_routes  import router as escalation_router
from api.doctor_routes      import router as doctor_router

# ── Logging setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan: startup + shutdown ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Create uploads folder
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"📁 Upload directory: {settings.UPLOAD_DIR}")

    # Initialize database
    init_db()
    logger.info("✅ Database initialized")

    # Seed if empty
    seed()

    logger.info(f"✅ {settings.APP_NAME} is ready!")
    logger.info(f"📖 API docs: http://localhost:{settings.API_PORT}/docs")

    yield

    # Shutdown
    logger.info(f"👋 {settings.APP_NAME} shutting down...")


# ── FastAPI App ───────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AgentCare — Agentic AI for Patient Administration and Care Coordination. "
        "Handles patient registration, department routing, appointment booking, "
        "document management, reminders, and follow-up coordination. "
        "IMPORTANT: This system handles administrative tasks only. "
        "It does NOT provide medical diagnoses or treatment recommendations."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register Routers ──────────────────────────────────────────
app.include_router(auth_router)
app.include_router(patient_router)
app.include_router(workflow_router)
app.include_router(appointment_router)
app.include_router(document_router)
app.include_router(staff_router)
app.include_router(escalation_router)
app.include_router(doctor_router)


# ── Root endpoint ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status":  "running",
        "docs":    "/docs",
        "message": (
            "AgentCare Administrative AI System. "
            "For medical emergencies, call 112 or visit the nearest ER."
        ),
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    from database.connection import get_db_session
    from services.llm_service import llm_service

    db_status = "unknown"
    try:
        db = get_db_session()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status":   "healthy",
        "app":      settings.APP_NAME,
        "version":  settings.APP_VERSION,
        "database": db_status,
        "llm_model": llm_service.model,
        "upload_dir": settings.UPLOAD_DIR,
    }


# ── Run directly ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )