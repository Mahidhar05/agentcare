# database/seed.py

"""
Seed script — populates the database with synthetic sample data.
Run once after init_db():  python database/seed.py
All data is fictional and anonymized.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from database.connection import init_db, get_db_session
from database.models import (
    User, UserRole, PatientProfile, Department,
    Doctor, AppointmentSlot, SlotStatus
)
from auth.password import hash_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# SEED DATA DEFINITIONS
# ─────────────────────────────────────────────

DEPARTMENTS = [
    {"name": "Cardiology",       "description": "Heart and cardiovascular system care"},
    {"name": "Neurology",        "description": "Brain, spine, and nervous system care"},
    {"name": "Orthopedics",      "description": "Bones, joints, and musculoskeletal care"},
    {"name": "General Medicine", "description": "General health and primary care"},
    {"name": "Radiology",        "description": "Imaging and diagnostic services"},
    {"name": "Dermatology",      "description": "Skin, hair, and nail care"},
    {"name": "Ophthalmology",    "description": "Eye care and vision services"},
    {"name": "Pediatrics",       "description": "Child and adolescent health care"},
    {"name": "Gynecology",       "description": "Women's reproductive health"},
    {"name": "Gastroenterology", "description": "Digestive system care"},
]

DOCTORS = [
    # Cardiology
    {"name": "Dr. Aisha Sharma",    "dept": "Cardiology",       "specialization": "Interventional Cardiology", "qualification": "MD, DM Cardiology"},
    {"name": "Dr. Rajan Mehta",     "dept": "Cardiology",       "specialization": "Electrophysiology",         "qualification": "MD, DM Cardiology"},
    # Neurology
    {"name": "Dr. Priya Nair",      "dept": "Neurology",        "specialization": "Stroke & Epilepsy",         "qualification": "MD, DM Neurology"},
    {"name": "Dr. Samuel D'souza",  "dept": "Neurology",        "specialization": "Movement Disorders",        "qualification": "MD, DM Neurology"},
    # Orthopedics
    {"name": "Dr. Kavita Joshi",    "dept": "Orthopedics",      "specialization": "Joint Replacement",         "qualification": "MS Orthopedics"},
    {"name": "Dr. Arjun Patel",     "dept": "Orthopedics",      "specialization": "Spine Surgery",             "qualification": "MS Orthopedics"},
    # General Medicine
    {"name": "Dr. Meena Krishnan",  "dept": "General Medicine", "specialization": "Internal Medicine",         "qualification": "MD General Medicine"},
    {"name": "Dr. Vikram Reddy",    "dept": "General Medicine", "specialization": "Diabetology",               "qualification": "MD General Medicine"},
    # Radiology
    {"name": "Dr. Sunita Agarwal",  "dept": "Radiology",        "specialization": "MRI & CT Imaging",          "qualification": "MD Radiology"},
    # Dermatology
    {"name": "Dr. Farah Sheikh",    "dept": "Dermatology",      "specialization": "Cosmetic Dermatology",      "qualification": "MD Dermatology"},
    # Ophthalmology
    {"name": "Dr. Rohit Gupta",     "dept": "Ophthalmology",    "specialization": "Retina & Vitreous",         "qualification": "MS Ophthalmology"},
    # Pediatrics
    {"name": "Dr. Ananya Pillai",   "dept": "Pediatrics",       "specialization": "Neonatology",               "qualification": "MD Pediatrics"},
    # Gynecology
    {"name": "Dr. Deepa Iyer",      "dept": "Gynecology",       "specialization": "Maternal Fetal Medicine",   "qualification": "MS OBG"},
    # Gastroenterology
    {"name": "Dr. Nikhil Bose",     "dept": "Gastroenterology", "specialization": "Hepatology",                "qualification": "MD, DM Gastroenterology"},
]

STAFF_USERS = [
    {"name": "Admin User",    "email": "admin@agentcare.com",   "password": "Admin@123",   "role": UserRole.admin},
    {"name": "Staff Alice",   "email": "staff1@agentcare.com",  "password": "Staff@123",   "role": UserRole.staff},
    {"name": "Staff Bob",     "email": "staff2@agentcare.com",  "password": "Staff@123",   "role": UserRole.staff},
]

PATIENT_USERS = [
    {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "password": "Patient@123",
        "dob": "1985-06-15",
        "age": 39,
        "phone": "+91-9876543210",
        "gender": "Male",
        "address": "123 Main Street, Mumbai",
        "emergency_contact": "Jane Doe: +91-9876543211",
        "blood_group": "O+",
    },
    {
        "name": "Priya Singh",
        "email": "priya.singh@example.com",
        "password": "Patient@123",
        "dob": "1992-03-22",
        "age": 32,
        "phone": "+91-9123456789",
        "gender": "Female",
        "address": "456 Park Avenue, Delhi",
        "emergency_contact": "Amit Singh: +91-9123456790",
        "blood_group": "A+",
    },
    {
        "name": "Rahul Verma",
        "email": "rahul.verma@example.com",
        "password": "Patient@123",
        "dob": "1978-11-08",
        "age": 46,
        "phone": "+91-9988776655",
        "gender": "Male",
        "address": "789 Lake Road, Bangalore",
        "emergency_contact": "Sunita Verma: +91-9988776656",
        "blood_group": "B+",
    },
]


# ─────────────────────────────────────────────
# SLOT GENERATOR
# ─────────────────────────────────────────────

def generate_slots_for_doctor(doctor_id: int, days_ahead: int = 14):
    """
    Generates REALISTIC hospital slots:
    - 1-hour duration
    - Morning:   9AM, 10AM, 11AM, 12PM
    - Lunch:     1PM-2PM (NO SLOT)
    - Afternoon: 2PM, 3PM, 4PM, 5PM, 6PM, 7PM
    = 10 slots per doctor per day
    - Skips Sundays
    """
    slots = []
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Working hours (start hour for each slot)
    morning_hours   = [9, 10, 11, 12]        # 9AM, 10AM, 11AM, 12PM
    afternoon_hours = [14, 15, 16, 17, 18, 19]  # 2PM, 3PM, 4PM, 5PM, 6PM, 7PM
    all_hours       = morning_hours + afternoon_hours

    for day_offset in range(1, days_ahead + 1):
        slot_date = base_date + timedelta(days=day_offset)

        # Skip Sundays (weekday 6)
        if slot_date.weekday() == 6:
            continue

        for hour in all_hours:
            start = slot_date.replace(hour=hour, minute=0)
            end   = start + timedelta(hours=1)
            slots.append(AppointmentSlot(
                doctor_id=doctor_id,
                start_time=start,
                end_time=end,
                status=SlotStatus.available
            ))

    return slots


# ─────────────────────────────────────────────
# MAIN SEED FUNCTION
# ─────────────────────────────────────────────

def seed():
    db = get_db_session()
    try:
        # ── Check if already seeded ──────────────────────
        if db.query(User).first():
            logger.info("⚠️  Database already has data. Skipping seed.")
            return

        logger.info("🌱 Starting database seed...")

        # ── 1. Seed Departments ──────────────────────────
        dept_map = {}
        for d in DEPARTMENTS:
            dept = Department(name=d["name"], description=d["description"], active=True)
            db.add(dept)
            db.flush()
            dept_map[d["name"]] = dept.id
            logger.info(f"   ✅ Department: {d['name']}")

        # ── 2. Seed Doctors + User Accounts + Slots ──────
        for doc_data in DOCTORS:
            dept_id = dept_map.get(doc_data["dept"])
            if not dept_id:
                continue
            
            # Create User account for doctor
            # Email format: firstname.lastname@agentcare.com
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
            )
            db.add(doctor_user)
            db.flush()
            
            # Create Doctor profile linked to User
            doctor = Doctor(
                department_id=dept_id,
                user_id=doctor_user.id,   # ← Link to User
                name=doc_data["name"],
                specialization=doc_data["specialization"],
                qualification=doc_data["qualification"],
                active=True,
            )
            db.add(doctor)
            db.flush()

            # Generate slots for this doctor
            slots = generate_slots_for_doctor(doctor.id, days_ahead=14)
            for slot in slots:
                db.add(slot)

            logger.info(
                f"   ✅ Doctor: {doc_data['name']} "
                f"| Login: {doctor_email} | {len(slots)} slots"
            )
        

        # ── 3. Seed Staff / Admin Users ──────────────────
        for su in STAFF_USERS:
            user = User(
                name=su["name"],
                email=su["email"],
                password_hash=hash_password(su["password"]),
                role=su["role"],
                is_active=True,
            )
            db.add(user)
            logger.info(f"   ✅ Staff user: {su['email']} [{su['role'].value}]")

        # ── 4. Seed Patient Users + Profiles ─────────────
        for pu in PATIENT_USERS:
            user = User(
                name=pu["name"],
                email=pu["email"],
                password_hash=hash_password(pu["password"]),
                role=UserRole.patient,
                is_active=True,
            )
            db.add(user)
            db.flush()

            profile = PatientProfile(
                user_id=user.id,
                date_of_birth=pu["dob"],
                age=pu["age"],
                phone=pu["phone"],
                gender=pu["gender"],
                address=pu["address"],
                preferred_language="English",
                emergency_contact=pu["emergency_contact"],
                blood_group=pu["blood_group"],
            )
            db.add(profile)
            logger.info(f"   ✅ Patient: {pu['email']}")

        # ── 5. Commit Everything ─────────────────────────
        db.commit()
        logger.info("🎉 Database seeded successfully!")
        logger.info("")
        logger.info("─── LOGIN CREDENTIALS ───────────────────────────")
        logger.info("  Admin  : admin@agentcare.com   / Admin@123")
        logger.info("  Staff  : staff1@agentcare.com  / Staff@123")
        logger.info("  Patient: john.doe@example.com  / Patient@123")
        logger.info("  Patient: priya.singh@example.com / Patient@123")
        logger.info("  Patient: rahul.verma@example.com / Patient@123")
        logger.info("  Doctor : aisha.sharma@agentcare.com / Doctor@123")
        logger.info("  Doctor : rajan.mehta@agentcare.com  / Doctor@123")
        logger.info("  Doctor : priya.nair@agentcare.com   / Doctor@123")
        logger.info("  (All doctors use password: Doctor@123)")
        logger.info("─────────────────────────────────────────────────")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Initializing database...")
    init_db()
    seed()