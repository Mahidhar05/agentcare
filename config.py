# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "AgentCare"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./agentcare.db")

    # ── JWT Auth ─────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme-use-a-long-random-string-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # ── LLM (Groq) ───────────────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3-70b-8192")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))

    # ── File Upload ───────────────────────────────────────
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    ALLOWED_EXTENSIONS: list = ["pdf", "jpg", "jpeg", "png", "dcm", "txt"]

    # ── Safety ───────────────────────────────────────────
    UNSAFE_KEYWORDS: list = [
        "diagnose", "diagnosis", "prescribe", "prescription",
        "dosage", "dose", "medication", "medicine", "drug",
        "treatment plan", "you have", "condition is",
        "take this", "symptom means", "cure", "therapy",
        "clinical recommendation", "medical advice"
    ]

    # ── FastAPI ───────────────────────────────────────────
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    FASTAPI_URL: str = os.getenv("FASTAPI_URL", "http://localhost:8000")

    # ── Streamlit ─────────────────────────────────────────
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))



    # ── Email / Notifications ─────────────────────────────
    EMAIL_MODE: str = os.getenv("EMAIL_MODE", "database")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "AgentCare System")


settings = Settings()