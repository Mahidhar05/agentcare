# tools/patient_tools.py

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models import User, PatientProfile, UserRole
from auth.password import hash_password
from tools.audit_tools import log_audit_event

logger = logging.getLogger(__name__)


def get_patient_profile(
    db: Session,
    user_id: int
) -> Optional[Dict[str, Any]]:
    """
    Fetches a patient profile by user_id.
    Returns dict with patient info or None if not found.
    """
    try:
        profile = db.query(PatientProfile).filter(
            PatientProfile.user_id == user_id
        ).first()

        if not profile:
            return None

        user = db.query(User).filter(User.id == user_id).first()

        return {
            "profile_id":          profile.id,
            "user_id":             user_id,
            "name":                user.name  if user else "Unknown",
            "email":               user.email if user else "Unknown",
            "date_of_birth":       profile.date_of_birth,
            "age":                 profile.age,
            "phone":               profile.phone,
            "gender":              profile.gender,
            "address":             profile.address,
            "preferred_language":  profile.preferred_language,
            "emergency_contact":   profile.emergency_contact,
            "blood_group":         profile.blood_group,
            "created_at": (
                profile.created_at.isoformat() if profile.created_at else None
            ),
            "updated_at": (
                profile.updated_at.isoformat() if profile.updated_at else None
            ),
        }

    except Exception as e:
        logger.error(f"[PATIENT] Error fetching profile for user {user_id}: {e}")
        return None


def get_or_create_patient_profile(
    db: Session,
    user_id: int,
    actor_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Returns existing patient profile or creates a blank one.
    Used by the Coordinator Agent at workflow start.
    """
    try:
        existing = get_patient_profile(db, user_id)

        if existing:
            logger.info(f"[PATIENT] Found existing profile for user {user_id}")
            existing["created"] = False
            return existing

        # Create blank profile
        profile = PatientProfile(
            user_id=user_id,
            preferred_language="English",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

        user = db.query(User).filter(User.id == user_id).first()

        log_audit_event(
            db=db,
            action="patient_profile_created",
            actor_id=actor_id or user_id,
            entity_type="PatientProfile",
            entity_id=profile.id,
            metadata={"user_id": user_id},
        )

        logger.info(f"[PATIENT] Created new profile for user {user_id}")

        return {
            "profile_id":         profile.id,
            "user_id":            user_id,
            "name":               user.name  if user else "Unknown",
            "email":              user.email if user else "",
            "date_of_birth":      None,
            "age":                None,
            "phone":              None,
            "gender":             None,
            "address":            None,
            "preferred_language": "English",
            "emergency_contact":  None,
            "blood_group":        None,
            "created_at":         profile.created_at.isoformat(),
            "updated_at":         profile.updated_at.isoformat(),
            "created":            True,
        }

    except Exception as e:
        logger.error(f"[PATIENT] Error in get_or_create for user {user_id}: {e}")
        db.rollback()
        raise


def update_patient_profile(
    db: Session,
    user_id: int,
    updates: Dict[str, Any],
    actor_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Updates an existing patient profile with provided fields.
    """
    try:
        profile = db.query(PatientProfile).filter(
            PatientProfile.user_id == user_id
        ).first()

        if not profile:
            raise ValueError(f"No patient profile found for user_id={user_id}")

        allowed_fields = [
            "date_of_birth", "age", "phone", "gender",
            "address", "preferred_language",
            "emergency_contact", "blood_group",
        ]

        updated_fields = []
        for field, value in updates.items():
            if field in allowed_fields and value is not None:
                setattr(profile, field, value)
                updated_fields.append(field)

        profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(profile)

        log_audit_event(
            db=db,
            action="patient_profile_updated",
            actor_id=actor_id or user_id,
            entity_type="PatientProfile",
            entity_id=profile.id,
            metadata={"updated_fields": updated_fields},
        )

        logger.info(f"[PATIENT] Updated profile {profile.id}: {updated_fields}")

        return get_patient_profile(db, user_id)

    except Exception as e:
        logger.error(f"[PATIENT] Error updating profile for user {user_id}: {e}")
        db.rollback()
        raise


def register_new_patient(
    db: Session,
    name: str,
    email: str,
    password: str,
    phone: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    age: Optional[int] = None,
    gender: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Registers a brand new patient user + profile in one step.
    """
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError(f"Email {email} is already registered.")

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.patient,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db.add(user)
        db.flush()

        profile = PatientProfile(
            user_id=user.id,
            phone=phone,
            date_of_birth=date_of_birth,
            age=age,
            gender=gender,
            preferred_language="English",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(profile)
        db.commit()
        db.refresh(user)
        db.refresh(profile)

        log_audit_event(
            db=db,
            action="patient_registered",
            actor_id=user.id,
            entity_type="User",
            entity_id=user.id,
            metadata={"email": email, "name": name},
        )

        logger.info(f"[PATIENT] New patient registered: {email}")

        return {
            "user_id":    user.id,
            "profile_id": profile.id,
            "name":       name,
            "email":      email,
            "role":       "patient",
        }

    except Exception as e:
        logger.error(f"[PATIENT] Registration failed: {e}")
        db.rollback()
        raise


def get_patient_by_profile_id(
    db: Session,
    profile_id: int
) -> Optional[Dict[str, Any]]:
    """
    Fetches patient info using profile_id (not user_id).
    """
    try:
        profile = db.query(PatientProfile).filter(
            PatientProfile.id == profile_id
        ).first()

        if not profile:
            return None

        return get_patient_profile(db, profile.user_id)

    except Exception as e:
        logger.error(f"[PATIENT] Error fetching by profile_id {profile_id}: {e}")
        return None