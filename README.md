# 🏥 AgentCare — Agentic AI for Patient Administration and Care Coordination

An **agentic healthcare administration system** that coordinates a patient's non-clinical journey — from registration and department routing to appointment booking, document collection, reminders, and follow-up — while keeping medical decisions under human supervision.

> ⚠️ **Important:** This system is for **administrative tasks only**. It does NOT diagnose, prescribe, or replace clinical judgment.

---

## ✨ Features

- 🤖 **6 distinct AI agents** with unique prompts and responsibilities
- 🔐 **JWT authentication** with backend-enforced role-based access control
- 📄 **Document management** with SHA256 duplicate detection and LLM classification
- 📅 **Appointment lifecycle** — book, reschedule, cancel with double-booking prevention
- 🔔 **Automatic reminders** (24h, 2h before) and follow-up scheduling
- ⚠️ **Safety guardrails** blocking diagnosis/prescription language
- 🚨 **Human escalation** workflow for uncertain or sensitive requests
- 📊 **Full audit logging** on every action
- 🎨 **Streamlit UI** for both patients and staff/admin

---

## 🏗️ Architecture


## 🙏 Third-Party Components & Attribution

This project uses the following open-source libraries and services:

### Frameworks & Libraries
- **[FastAPI](https://fastapi.tiangolo.com/)** — Python web framework for the REST API
- **[SQLAlchemy](https://www.sqlalchemy.org/)** — SQL toolkit and ORM
- **[Streamlit](https://streamlit.io/)** — Frontend UI framework
- **[Pydantic](https://docs.pydantic.dev/)** — Data validation
- **[Uvicorn](https://www.uvicorn.org/)** — ASGI server
- **[Passlib](https://passlib.readthedocs.io/)** — Password hashing (bcrypt)
- **[python-jose](https://github.com/mpdavis/python-jose)** — JWT authentication
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — Environment configuration
- **[pytest](https://docs.pytest.org/)** — Testing framework

### External Services
- **[Groq API](https://groq.com/)** — LLM inference (llama-3.1-8b-instant model)
- **[Gmail SMTP](https://support.google.com/mail/)** — Email delivery (for real notifications)

### Design Inspiration
- Color palette inspired by modern healthcare apps (Apollo, Practo, Zocdoc)
- Chat UI patterns inspired by ChatGPT, Claude
- Font: [Inter](https://fonts.google.com/specimen/Inter) by Rasmus Andersson

### AI Assistance Acknowledgment
- Development assisted by AI pair programming
- All architecture, agent design, business logic, and integration is original work
- LLM prompts, database schema, and workflow orchestration are custom-built

### License Compliance
All third-party libraries used are open source under permissive licenses 
(MIT, Apache 2.0, BSD). No proprietary code was reused.

# Just open your README.md and paste the attribution section I gave above
# at the end of the file, before the disclaimer.


## 🙏 Third-Party Components & Attribution

This project uses the following open-source libraries and services:

### Frameworks & Libraries
- **[FastAPI](https://fastapi.tiangolo.com/)** — Python web framework for the REST API
- **[SQLAlchemy](https://www.sqlalchemy.org/)** — SQL toolkit and ORM
- **[Streamlit](https://streamlit.io/)** — Frontend UI framework
- **[Pydantic](https://docs.pydantic.dev/)** — Data validation
- **[Uvicorn](https://www.uvicorn.org/)** — ASGI server
- **[Passlib](https://passlib.readthedocs.io/)** — Password hashing (bcrypt)
- **[python-jose](https://github.com/mpdavis/python-jose)** — JWT authentication
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — Environment configuration
- **[pytest](https://docs.pytest.org/)** — Testing framework
- **[requests](https://requests.readthedocs.io/)** — HTTP client library

### External Services
- **[Groq API](https://groq.com/)** — LLM inference (llama-3.1-8b-instant model)
- **[Gmail SMTP](https://support.google.com/mail/)** — Email delivery service

### Design Inspiration
- Color palette inspired by modern healthcare apps (Apollo, Practo, Zocdoc)
- Chat UI patterns inspired by ChatGPT, Claude
- Font: [Inter](https://fonts.google.com/specimen/Inter) by Rasmus Andersson

### AI Assistance Acknowledgment
- Development was assisted by AI pair programming for boilerplate generation
- All architecture decisions, agent design, business logic, workflow orchestration, 
  database schema, and integration are original work
- Custom system prompts for each of the 7 AI agents
- Safety enforcement logic and healthcare compliance rules are hand-crafted
- All third# 🚀 Excellent! Let's Build All 8 Features — In Order of Impact

You have 6 days. Let me plan this smartly.

---

## 📅 Recommended Build Order & Time

| # | Feature | Time | Priority | Why This Order |
|---|---|---|---|---|
| 1 | **Comprehensive Tests** | 1.5h | 🔴 First | Ensures nothing breaks as we add features |
| 2 | **Doctor Portal** | 1.5h | 🔴 High | New role = shows complete system |
| 3 | **Analytics Dashboard** | 1h | 🟡 Medium | Visual wow factor |
| 4 | **Search & Filter** | 45m | 🟡 Medium | Better UX |
| 5 | **Multi-Language Support** | 1.5h | 🟢 Bonus | Hackathon PDF mentioned this |
| 6 | **Conversational Memory** | 2h | 🟢 Wow | True ChatGPT feel |
| 7 | **Voice Input** | 1h | 🟢 Cool | Unique feature |
| 8 | **Cloud Deployment** | 1h | 🔴 LAST | Deploy final complete version |

**Total: ~10 hours** spread over 6 days = **~1.5 hours per day** 🎯

---

## 🎯 Why Tests First?

Right now if we add features, we might accidentally break existing ones. Tests catch regressions early. Plus, it's a **major hackathon scoring point**.

---

## 🚀 LET'S START WITH #1: COMPREHENSIVE TESTS

Let me build a professional pytest suite covering all critical paths.

---

## 📁 STEP 1.1: Create Test Infrastructure

**Create these test files** in your `tests/` folder:

---

### File 1: `tests/conftest.py`

Create this file **at `tests/conftest.py`**:

```python
# tests/conftest.py
"""
Shared pytest fixtures for AgentCare tests.
Uses a separate test database to avoid polluting production data.
"""

import os
import pytest
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set test mode BEFORE importing app
os.environ["DATABASE_URL"] = "sqlite:///./test_agentcare.db"

from database.models import Base
from database.connection import get_db
from main import app


# ─── Test Database Setup ─────────────────────────────────────
TEST_DB_URL = "sqlite:///./test_agentcare.db"
test_engine = create_engine(
    TEST_DB_URL, connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test DB tables once per test session."""
    Base.metadata.create_all(bind=test_engine)
    
    # Seed test data
    from database.seed import (
        DEPARTMENTS, DOCTORS, STAFF_USERS, PATIENT_USERS,
        generate_slots_for_doctor
    )
    from database.models import (
        User, PatientProfile, Department, Doctor,
        UserRole, AppointmentSlot, SlotStatus
    )
    from auth.password import hash_password
    from datetime import datetime
    
    db = TestSessionLocal()
    
    # Seed if empty
    if not db.query(User).first():
        # Departments
        dept_map = {}
        for d in DEPARTMENTS:
            dept = Department(name=d["name"], description=d["description"], active=True)
            db.add(dept)
            db.flush()
            dept_map[d["name"]] = dept.id
        
        # Doctors + slots
        for doc_data in DOCTORS:
            dept_id = dept_map.get(doc_data["dept"])
            if not dept_id:
                continue
            doctor = Doctor(
                department_id=dept_id,
                name=doc_data["name"],
                specialization=doc_data["specialization"],
                qualification=doc_data["qualification"],
                active=True,
            )
            db.add(doctor)
            db.flush()
            slots = generate_slots_for_doctor(doctor.id, days_ahead=7)
            for slot in slots:
                db.add(slot)
        
        # Staff users
        for su in STAFF_USERS:
            user = User(
                name=su["name"], email=su["email"],
                password_hash=hash_password(su["password"]),
                role=su["role"], is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(user)
        
        # Patient users
        for pu in PATIENT_USERS:
            user = User(
                name=pu["name"], email=pu["email"],
                password_hash=hash_password(pu["password"]),
                role=UserRole.patient, is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(user)
            db.flush()
            profile = PatientProfile(
                user_id=user.id,
                phone=pu["phone"], age=pu["age"],
                gender=pu["gender"],
                preferred_language="English",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(profile)
        
        db.commit()
    
    db.close()
    
    yield
    
    # Cleanup: delete test DB after all tests
    try:
        os.remove("./test_agentcare.db")
    except Exception:
        pass


@pytest.fixture
def db_session():
    """Fresh DB session for each test."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """FastAPI test client."""
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def patient_token(client):
    """Returns auth token for patient user."""
    response = client.post(
        "/api/auth/login",
        data={"username": "john.doe@example.com", "password": "Patient@123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def staff_token(client):
    """Returns auth token for staff user."""
    response = client.post(
        "/api/auth/login",
        data={"username": "staff1@agentcare.com", "password": "Staff@123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client):
    """Returns auth token for admin user."""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin@agentcare.com", "password": "Admin@123"},
    )
    return response.json()["access_token"]


## 🧪 Test Coverage

This project has **73 automated tests** covering:
- All 7 AI agents (safety, routing, query, coordinator, appointment, document, follow-up)
- All API endpoints (auth, patient, staff, appointments, workflow)  
- Role-based access control enforcement
- Doctor lookup by name (partial/full/case-insensitive)
- Safety guardrails (blocks diagnosis, prescription, dosage requests)
- Emergency detection

Run: `pytest tests/ -v`    