# tests/conftest.py
"""
Shared pytest fixtures for AgentCare tests.
Uses a separate test database to avoid polluting production data.
"""

import os
import pytest
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
    """Create test DB tables + seed with all users (patients, staff, doctors)."""
    # ALWAYS remove old test DB to ensure fresh state
    if os.path.exists("./test_agentcare.db"):
        try:
            os.remove("./test_agentcare.db")
        except Exception as e:
            print(f"Could not remove old test DB: {e}")
    
    Base.metadata.create_all(bind=test_engine)
    
    # Import all seed data + helpers
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
    
    try:
        # 1. Seed departments
        dept_map = {}
        for d in DEPARTMENTS:
            dept = Department(
                name=d["name"],
                description=d["description"],
                active=True
            )
            db.add(dept)
            db.flush()
            dept_map[d["name"]] = dept.id
        
        # 2. Seed doctors with User accounts (like real seed does)
        for doc_data in DOCTORS:
            dept_id = dept_map.get(doc_data["dept"])
            if not dept_id:
                continue
            
            # Create User account for doctor
            name_parts = doc_data["name"].replace("Dr. ", "").split()
            first_name = name_parts[0].lower()
            last_name = name_parts[-1].lower() if len(name_parts) > 1 else "doc"
            doctor_email = f"{first_name}.{last_name}@agentcare.com"
            
            doctor_user = User(
                name=doc_data["name"],
                email=doctor_email,
                password_hash=hash_password("Doctor@123"),
                role=UserRole.doctor,
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(doctor_user)
            db.flush()
            
            # Create Doctor profile
            doctor = Doctor(
                department_id=dept_id,
                user_id=doctor_user.id,
                name=doc_data["name"],
                specialization=doc_data["specialization"],
                qualification=doc_data["qualification"],
                active=True,
            )
            db.add(doctor)
            db.flush()
            
            # Generate 7 days of slots
            slots = generate_slots_for_doctor(doctor.id, days_ahead=7)
            for slot in slots:
                db.add(slot)
        
        # 3. Seed staff users
        for su in STAFF_USERS:
            user = User(
                name=su["name"],
                email=su["email"],
                password_hash=hash_password(su["password"]),
                role=su["role"],
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(user)
        
        # 4. Seed patient users
        for pu in PATIENT_USERS:
            user = User(
                name=pu["name"],
                email=pu["email"],
                password_hash=hash_password(pu["password"]),
                role=UserRole.patient,
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(user)
            db.flush()
            
            profile = PatientProfile(
                user_id=user.id,
                phone=pu.get("phone"),
                age=pu.get("age"),
                gender=pu.get("gender"),
                date_of_birth=pu.get("dob"),
                address=pu.get("address"),
                emergency_contact=pu.get("emergency_contact"),
                blood_group=pu.get("blood_group"),
                preferred_language="English",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(profile)
        
        db.commit()
        print(f"✅ Test DB seeded: 14 doctors, 3 staff, 3 patients")
    except Exception as e:
        print(f"❌ Test DB seed error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    yield
    
    # Cleanup after all tests
    try:
        if os.path.exists("./test_agentcare.db"):
            os.remove("./test_agentcare.db")
    except Exception:
        pass


@pytest.fixture
def db_session():
    """Fresh DB session for each test — uses the pre-seeded test DB."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """FastAPI test client that uses the test DB."""
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
    assert response.status_code == 200, f"Login failed: {response.json()}"
    return response.json()["access_token"]


@pytest.fixture
def staff_token(client):
    """Returns auth token for staff user."""
    response = client.post(
        "/api/auth/login",
        data={"username": "staff1@agentcare.com", "password": "Staff@123"},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client):
    """Returns auth token for admin user."""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin@agentcare.com", "password": "Admin@123"},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    return response.json()["access_token"]