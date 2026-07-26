# api/patient_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User
from auth.dependencies import get_current_user, require_patient
from tools.patient_tools import (
    get_patient_profile,
    update_patient_profile,
    get_or_create_patient_profile,
)
from tools.audit_tools import log_audit_event
from schemas.pydantic_schemas import (
    PatientProfileUpdate, PatientProfileResponse
)
import logging

router = APIRouter(prefix="/api/patients", tags=["Patients"])
logger = logging.getLogger(__name__)


@router.get("/profile", response_model=PatientProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the current patient's profile.
    Patients can only see their own profile.
    Staff can view any profile via staff routes.
    """
    profile = get_or_create_patient_profile(
        db=db,
        user_id=current_user.id,
        actor_id=current_user.id,
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    return PatientProfileResponse(**profile)


@router.put("/profile", response_model=PatientProfileResponse)
def update_my_profile(
    updates: PatientProfileUpdate,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Updates the current patient's own profile.
    Patients can ONLY update their own profile.
    """
    try:
        updated = update_patient_profile(
            db=db,
            user_id=current_user.id,
            updates=updates.dict(exclude_none=True),
            actor_id=current_user.id,
        )

        log_audit_event(
            db=db,
            action="profile_updated_by_patient",
            actor_id=current_user.id,
            entity_type="PatientProfile",
            metadata={"fields": list(updates.dict(exclude_none=True).keys())},
        )

        return PatientProfileResponse(**updated)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"[PATIENT ROUTE] Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed.",
        )


@router.get("/profile/{user_id}", response_model=PatientProfileResponse)
def get_patient_profile_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns a patient profile by user_id.
    Patients can only view their own. Staff/Admin can view any.
    """
    from database.models import UserRole

    # Enforce: patients can only view their own
    if (current_user.role == UserRole.patient
            and current_user.id != user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile.",
        )

    profile = get_patient_profile(db=db, user_id=user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No profile found for user_id={user_id}",
        )

    return PatientProfileResponse(**profile)

@router.get("/notifications")
def get_my_notifications(
    limit: int = 50,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Returns all notifications sent to the current patient."""
    from database.models import Notification

    notifications = db.query(Notification).filter(
        Notification.recipient_email == current_user.email
    ).order_by(Notification.created_at.desc()).limit(limit).all()

    return {
        "notifications": [
            {
                "id":                n.id,
                "subject":           n.subject,
                "notification_type": n.notification_type.value,
                "status":            n.status.value,
                "created_at":        n.created_at.isoformat() if n.created_at else None,
                "sent_at":           n.sent_at.isoformat() if n.sent_at else None,
            }
            for n in notifications
        ],
        "total": len(notifications),
    }


@router.get("/notifications/{notification_id}")
def get_my_notification_detail(
    notification_id: int,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Returns full notification body for preview. Only own notifications."""
    from database.models import Notification

    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_email == current_user.email,
    ).first()

    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {
        "id":                n.id,
        "recipient_email":   n.recipient_email,
        "subject":           n.subject,
        "body_html":         n.body_html,
        "body_plain":        n.body_plain,
        "notification_type": n.notification_type.value,
        "status":            n.status.value,
        "created_at":        n.created_at.isoformat() if n.created_at else None,
        "sent_at":           n.sent_at.isoformat() if n.sent_at else None,
    }