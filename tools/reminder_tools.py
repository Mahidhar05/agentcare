# tools/reminder_tools.py

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models import Reminder, ReminderType, ReminderStatus
from tools.audit_tools import log_audit_event

logger = logging.getLogger(__name__)


def create_reminder(
    db: Session,
    patient_id: int,
    reminder_type: str,
    scheduled_at: datetime,
    message: str = None,
    appointment_id: int = None,
    actor_id: int = None,
) -> dict:
    """
    Creates a reminder record for a patient.

    Args:
        patient_id    : PatientProfile.id
        reminder_type : 'appointment', 'document', or 'follow_up'
        scheduled_at  : when the reminder should fire
        message       : reminder message text
        appointment_id: linked appointment (optional)
        actor_id      : for audit log

    Returns:
        Reminder dict
    """
    try:
        try:
            r_type = ReminderType(reminder_type)
        except ValueError:
            r_type = ReminderType.appointment

        reminder = Reminder(
            patient_id=patient_id,
            appointment_id=appointment_id,
            reminder_type=r_type,
            message=message or _default_message(r_type, scheduled_at),
            scheduled_at=scheduled_at,
            status=ReminderStatus.pending,
            created_at=datetime.utcnow(),
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        log_audit_event(
            db=db,
            action="reminder_created",
            actor_id=actor_id,
            entity_type="Reminder",
            entity_id=reminder.id,
            metadata={
                "patient_id": patient_id,
                "type": reminder_type,
                "scheduled_at": scheduled_at.isoformat(),
                "appointment_id": appointment_id,
            },
        )

        logger.info(
            f"[REMINDER] Created {reminder_type} reminder #{reminder.id} "
            f"for patient {patient_id} at {scheduled_at}"
        )

        return _reminder_to_dict(reminder)

    except Exception as e:
        logger.error(f"[REMINDER] Failed to create reminder: {e}")
        db.rollback()
        raise


def create_appointment_reminder(
    db: Session,
    patient_id: int,
    appointment_id: int,
    appointment_datetime: datetime,
    actor_id: int = None,
) -> list:
    """
    Creates standard reminders for an appointment:
    - 24 hours before
    - 2 hours before

    Returns:
        List of created reminder dicts
    """
    reminders = []

    try:
        # 24-hour reminder
        remind_24h = appointment_datetime - timedelta(hours=24)
        if remind_24h > datetime.utcnow():
            r1 = create_reminder(
                db=db,
                patient_id=patient_id,
                reminder_type="appointment",
                scheduled_at=remind_24h,
                message=(
                    f"Reminder: You have an appointment tomorrow at "
                    f"{appointment_datetime.strftime('%I:%M %p')}. "
                    f"Please be on time and bring your documents."
                ),
                appointment_id=appointment_id,
                actor_id=actor_id,
            )
            reminders.append(r1)

        # 2-hour reminder
        remind_2h = appointment_datetime - timedelta(hours=2)
        if remind_2h > datetime.utcnow():
            r2 = create_reminder(
                db=db,
                patient_id=patient_id,
                reminder_type="appointment",
                scheduled_at=remind_2h,
                message=(
                    f"Your appointment is in 2 hours at "
                    f"{appointment_datetime.strftime('%I:%M %p')}. "
                    f"Please proceed to the hospital."
                ),
                appointment_id=appointment_id,
                actor_id=actor_id,
            )
            reminders.append(r2)

        return reminders

    except Exception as e:
        logger.error(f"[REMINDER] Failed to create appointment reminders: {e}")
        return []


def create_followup_reminder(
    db: Session,
    patient_id: int,
    appointment_id: int,
    appointment_datetime: datetime,
    followup_days: int = 7,
    actor_id: int = None,
) -> dict:
    """
    Creates a follow-up reminder after the appointment
    (default: 7 days after).

    Returns:
        Follow-up reminder dict
    """
    try:
        followup_date = appointment_datetime + timedelta(days=followup_days)

        reminder = create_reminder(
            db=db,
            patient_id=patient_id,
            reminder_type="follow_up",
            scheduled_at=followup_date,
            message=(
                f"Follow-up reminder: It has been {followup_days} days since "
                f"your appointment on {appointment_datetime.strftime('%Y-%m-%d')}. "
                f"Please schedule a follow-up visit if advised by your doctor."
            ),
            appointment_id=appointment_id,
            actor_id=actor_id,
        )

        logger.info(
            f"[REMINDER] Created follow-up reminder #{reminder['reminder_id']} "
            f"for patient {patient_id} on {followup_date.date()}"
        )

        return reminder

    except Exception as e:
        logger.error(f"[REMINDER] Failed to create follow-up reminder: {e}")
        raise


def get_patient_reminders(
    db: Session,
    patient_id: int,
    status_filter: str = None,
) -> list:
    """
    Returns all reminders for a patient.
    """
    try:
        query = db.query(Reminder).filter(
            Reminder.patient_id == patient_id
        )

        if status_filter:
            try:
                status_enum = ReminderStatus(status_filter)
                query = query.filter(Reminder.status == status_enum)
            except ValueError:
                pass

        reminders = query.order_by(Reminder.scheduled_at.asc()).all()

        return [_reminder_to_dict(r) for r in reminders]

    except Exception as e:
        logger.error(f"[REMINDER] Error fetching reminders for patient {patient_id}: {e}")
        return []


def mark_reminder_sent(
    db: Session,
    reminder_id: int,
) -> bool:
    """Marks a reminder as sent."""
    try:
        reminder = db.query(Reminder).filter(
            Reminder.id == reminder_id
        ).first()

        if reminder:
            reminder.status = ReminderStatus.sent
            db.commit()
            return True

        return False

    except Exception as e:
        logger.error(f"[REMINDER] Failed to mark reminder {reminder_id} as sent: {e}")
        db.rollback()
        return False


def _default_message(reminder_type: ReminderType, scheduled_at: datetime) -> str:
    """Generates a default reminder message."""
    messages = {
        ReminderType.appointment: (
            f"You have an upcoming appointment on "
            f"{scheduled_at.strftime('%Y-%m-%d at %I:%M %p')}."
        ),
        ReminderType.document: (
            "Please upload your medical documents before your appointment."
        ),
        ReminderType.follow_up: (
            "It's time for your follow-up visit. Please schedule an appointment."
        ),
    }
    return messages.get(reminder_type, "You have a pending action in AgentCare.")


def _reminder_to_dict(reminder: Reminder) -> dict:
    """Converts Reminder ORM to dict."""
    return {
        "reminder_id": reminder.id,
        "patient_id": reminder.patient_id,
        "appointment_id": reminder.appointment_id,
        "reminder_type": reminder.reminder_type.value,
        "message": reminder.message,
        "scheduled_at": reminder.scheduled_at.isoformat() if reminder.scheduled_at else None,
        "status": reminder.status.value,
        "created_at": reminder.created_at.isoformat() if reminder.created_at else None,
    }