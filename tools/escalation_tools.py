# tools/escalation_tools.py

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from database.models import Escalation, EscalationStatus, WorkflowRun, WorkflowStatus
from tools.audit_tools import log_audit_event

logger = logging.getLogger(__name__)


def create_escalation(
    db: Session,
    reason: str,
    workflow_run_id: Optional[int] = None,
    details: Optional[str] = None,
    actor_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Creates a human-review escalation record.
    Also triggers email notification to all staff.
    """
    try:
        escalation = Escalation(
            workflow_run_id=workflow_run_id,
            reason=reason,
            details=details,
            status=EscalationStatus.open,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(escalation)

        # Mark workflow as escalated
        if workflow_run_id:
            workflow = db.query(WorkflowRun).filter(
                WorkflowRun.id == workflow_run_id
            ).first()
            if workflow:
                workflow.status = WorkflowStatus.escalated
                workflow.current_step = "escalated"
                workflow.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(escalation)

        log_audit_event(
            db=db,
            action="escalation_created",
            actor_id=actor_id,
            entity_type="Escalation",
            entity_id=escalation.id,
            metadata={
                "reason":           reason,
                "workflow_run_id":  workflow_run_id,
            },
        )

        logger.warning(
            f"[ESCALATION] Created escalation #{escalation.id}: {reason}"
        )

        # ── Trigger email notifications to staff ───────────────
        try:
            from services.email_service import email_service
            from database.models import PatientProfile, User

            # Try to get patient name for the email
            patient_name = "Unknown Patient"
            if workflow_run_id:
                workflow = db.query(WorkflowRun).filter(
                    WorkflowRun.id == workflow_run_id
                ).first()
                if workflow:
                    patient = db.query(PatientProfile).filter(
                        PatientProfile.id == workflow.patient_id
                    ).first()
                    if patient:
                        user = db.query(User).filter(
                            User.id == patient.user_id
                        ).first()
                        if user:
                            patient_name = user.name

            notifications = email_service.send_escalation_alert_to_staff(
                escalation_id=escalation.id,
                reason=reason,
                details=details or "No additional details",
                workflow_run_id=workflow_run_id,
                patient_name=patient_name,
            )

            log_audit_event(
                db=db,
                action="notifications_dispatched",
                actor_id=actor_id,
                entity_type="Escalation",
                entity_id=escalation.id,
                metadata={
                    "notification_count": len(notifications),
                    "recipients": [n.get("recipient") for n in notifications],
                },
            )

        except Exception as email_err:
            # Email failure should NOT break the escalation
            logger.error(f"[ESCALATION] Email notification failed: {email_err}")

        return _escalation_to_dict(escalation)

    except Exception as e:
        logger.error(f"[ESCALATION] Failed to create escalation: {e}")
        db.rollback()
        raise


def get_open_escalations(db: Session) -> List[Dict[str, Any]]:
    """
    Returns all open escalations for staff review.
    """
    try:
        escalations = db.query(Escalation).filter(
            Escalation.status == EscalationStatus.open
        ).order_by(Escalation.created_at.desc()).all()

        return [_escalation_to_dict(e) for e in escalations]

    except Exception as e:
        logger.error(f"[ESCALATION] Error fetching open escalations: {e}")
        return []


def get_all_escalations(
    db: Session,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Returns all escalations (for admin view).
    """
    try:
        escalations = db.query(Escalation).order_by(
            Escalation.created_at.desc()
        ).limit(limit).all()

        return [_escalation_to_dict(e) for e in escalations]

    except Exception as e:
        logger.error(f"[ESCALATION] Error fetching all escalations: {e}")
        return []


def resolve_escalation(
    db: Session,
    escalation_id: int,
    reviewer_user_id: int,
    resolution_note: str,
    new_status: str = "resolved",
) -> Dict[str, Any]:
    """
    Staff/Admin resolves or reviews an escalation.

    Args:
        escalation_id    : Escalation.id
        reviewer_user_id : User.id of staff who reviewed it
        resolution_note  : Notes about the resolution
        new_status       : 'reviewed' or 'resolved'

    Returns:
        Updated escalation dict
    """
    try:
        escalation = db.query(Escalation).filter(
            Escalation.id == escalation_id
        ).first()

        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found.")

        try:
            status_enum = EscalationStatus(new_status)
        except ValueError:
            status_enum = EscalationStatus.resolved

        escalation.status          = status_enum
        escalation.reviewed_by     = reviewer_user_id
        escalation.resolution_note = resolution_note
        escalation.updated_at      = datetime.utcnow()

        db.commit()
        db.refresh(escalation)

        log_audit_event(
            db=db,
            action="escalation_resolved",
            actor_id=reviewer_user_id,
            entity_type="Escalation",
            entity_id=escalation_id,
            metadata={
                "status":          new_status,
                "resolution_note": resolution_note,
            },
        )

        logger.info(
            f"[ESCALATION] Escalation #{escalation_id} "
            f"marked as {new_status} by user {reviewer_user_id}"
        )

        return _escalation_to_dict(escalation)

    except Exception as e:
        logger.error(
            f"[ESCALATION] Failed to resolve escalation {escalation_id}: {e}"
        )
        db.rollback()
        raise


def get_escalation_by_id(
    db: Session,
    escalation_id: int
) -> Optional[Dict[str, Any]]:
    """Fetches a single escalation by ID."""
    try:
        e = db.query(Escalation).filter(
            Escalation.id == escalation_id
        ).first()

        if not e:
            return None

        return _escalation_to_dict(e)

    except Exception as ex:
        logger.error(
            f"[ESCALATION] Error fetching escalation {escalation_id}: {ex}"
        )
        return None


def _escalation_to_dict(escalation: Escalation) -> Dict[str, Any]:
    """Converts Escalation ORM object to dict."""
    return {
        "escalation_id":    escalation.id,
        "workflow_run_id":  escalation.workflow_run_id,
        "reason":           escalation.reason,
        "details":          escalation.details,
        "status":           escalation.status.value,
        "reviewed_by":      escalation.reviewed_by,
        "resolution_note":  escalation.resolution_note,
        "created_at": (
            escalation.created_at.isoformat()
            if escalation.created_at else None
        ),
        "updated_at": (
            escalation.updated_at.isoformat()
            if escalation.updated_at else None
        ),
    }