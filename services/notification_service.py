# services/notification_service.py

import logging
from datetime import datetime
from typing import Dict, Any, List
from database.connection import get_db_session
from database.models import Reminder, ReminderStatus

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Simulated notification service.
    In production this would integrate with email/SMS providers.
    For now it logs notifications and marks reminders as sent.
    """

    def send_appointment_confirmation(
        self,
        patient_name: str,
        patient_email: str,
        doctor_name: str,
        department: str,
        appointment_date: str,
        appointment_time: str,
        appointment_id: int,
    ) -> Dict[str, Any]:
        """
        Sends appointment confirmation notification.
        Simulated — logs the notification.
        """
        message = (
            f"Dear {patient_name},\n\n"
            f"Your appointment has been confirmed!\n\n"
            f"Details:\n"
            f"  Doctor     : {doctor_name}\n"
            f"  Department : {department}\n"
            f"  Date       : {appointment_date}\n"
            f"  Time       : {appointment_time}\n"
            f"  Appt ID    : #{appointment_id}\n\n"
            f"Please arrive 15 minutes early and bring your documents.\n\n"
            f"AgentCare Team"
        )

        logger.info(
            f"[NOTIFY] Appointment confirmation sent to {patient_email}\n"
            f"{message}"
        )

        return {
            "type":       "appointment_confirmation",
            "recipient":  patient_email,
            "message":    message,
            "sent_at":    datetime.utcnow().isoformat(),
            "status":     "sent",
        }

    def send_appointment_reminder(
        self,
        patient_name: str,
        patient_email: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        hours_before: int,
        reminder_id: int,
    ) -> Dict[str, Any]:
        """
        Sends appointment reminder notification.
        """
        message = (
            f"Dear {patient_name},\n\n"
            f"Reminder: Your appointment is in {hours_before} hour(s).\n\n"
            f"  Doctor : {doctor_name}\n"
            f"  Date   : {appointment_date}\n"
            f"  Time   : {appointment_time}\n\n"
            f"Please do not forget to bring your medical documents.\n\n"
            f"AgentCare Team"
        )

        logger.info(
            f"[NOTIFY] Reminder sent to {patient_email} "
            f"({hours_before}h before appointment)"
        )

        # Mark reminder as sent in DB
        self._mark_reminder_sent(reminder_id)

        return {
            "type":       "appointment_reminder",
            "recipient":  patient_email,
            "message":    message,
            "sent_at":    datetime.utcnow().isoformat(),
            "status":     "sent",
        }

    def send_escalation_alert(
        self,
        staff_email: str,
        escalation_id: int,
        reason: str,
        patient_name: str,
        workflow_run_id: int,
    ) -> Dict[str, Any]:
        """
        Alerts staff about a new escalation requiring review.
        """
        message = (
            f"ESCALATION ALERT\n\n"
            f"A patient request requires your review.\n\n"
            f"  Escalation ID  : #{escalation_id}\n"
            f"  Patient        : {patient_name}\n"
            f"  Workflow Run   : #{workflow_run_id}\n"
            f"  Reason         : {reason}\n\n"
            f"Please log in to AgentCare Staff Portal to review.\n\n"
            f"AgentCare System"
        )

        logger.warning(
            f"[NOTIFY] Escalation alert sent to {staff_email}: "
            f"Escalation #{escalation_id}"
        )

        return {
            "type":          "escalation_alert",
            "recipient":     staff_email,
            "escalation_id": escalation_id,
            "message":       message,
            "sent_at":       datetime.utcnow().isoformat(),
            "status":        "sent",
        }

    def send_document_upload_confirmation(
        self,
        patient_name: str,
        patient_email: str,
        document_type: str,
        filename: str,
        is_duplicate: bool,
    ) -> Dict[str, Any]:
        """
        Confirms document upload to patient.
        """
        if is_duplicate:
            note = (
                "Note: This document appears to be a duplicate "
                "of one already in our system."
            )
        else:
            note = "Your document has been successfully stored."

        message = (
            f"Dear {patient_name},\n\n"
            f"Document Upload Confirmation\n\n"
            f"  File     : {filename}\n"
            f"  Type     : {document_type}\n"
            f"  Status   : {note}\n\n"
            f"AgentCare Team"
        )

        logger.info(
            f"[NOTIFY] Document upload confirmation sent to {patient_email}: "
            f"{filename}"
        )

        return {
            "type":      "document_confirmation",
            "recipient": patient_email,
            "message":   message,
            "sent_at":   datetime.utcnow().isoformat(),
            "status":    "sent",
        }

    def send_followup_reminder(
        self,
        patient_name: str,
        patient_email: str,
        original_appointment_date: str,
        followup_due_date: str,
    ) -> Dict[str, Any]:
        """
        Sends a follow-up reminder to the patient.
        """
        message = (
            f"Dear {patient_name},\n\n"
            f"Follow-up Reminder\n\n"
            f"It has been some time since your appointment on "
            f"{original_appointment_date}.\n\n"
            f"If your doctor recommended a follow-up visit, "
            f"please schedule one by {followup_due_date}.\n\n"
            f"You can book at: http://localhost:8501\n\n"
            f"AgentCare Team"
        )

        logger.info(
            f"[NOTIFY] Follow-up reminder sent to {patient_email}"
        )

        return {
            "type":      "followup_reminder",
            "recipient": patient_email,
            "message":   message,
            "sent_at":   datetime.utcnow().isoformat(),
            "status":    "sent",
        }

    def send_cancellation_confirmation(
        self,
        patient_name: str,
        patient_email: str,
        doctor_name: str,
        appointment_date: str,
        appointment_id: int,
    ) -> Dict[str, Any]:
        """
        Confirms appointment cancellation to patient.
        """
        message = (
            f"Dear {patient_name},\n\n"
            f"Your appointment has been cancelled.\n\n"
            f"  Doctor     : {doctor_name}\n"
            f"  Date       : {appointment_date}\n"
            f"  Appt ID    : #{appointment_id}\n\n"
            f"You can book a new appointment anytime on AgentCare.\n\n"
            f"AgentCare Team"
        )

        logger.info(
            f"[NOTIFY] Cancellation confirmation sent to {patient_email}"
        )

        return {
            "type":      "cancellation_confirmation",
            "recipient": patient_email,
            "message":   message,
            "sent_at":   datetime.utcnow().isoformat(),
            "status":    "sent",
        }

    def _mark_reminder_sent(self, reminder_id: int) -> None:
        """Marks a reminder as sent in the database."""
        try:
            db = get_db_session()
            reminder = db.query(Reminder).filter(
                Reminder.id == reminder_id
            ).first()
            if reminder:
                reminder.status = ReminderStatus.sent
                db.commit()
            db.close()
        except Exception as e:
            logger.error(
                f"[NOTIFY] Failed to mark reminder {reminder_id} sent: {e}"
            )

    def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """
        Returns all pending reminders that should be sent now.
        Used by a scheduler or background task.
        """
        try:
            db = get_db_session()
            now = datetime.utcnow()

            pending = db.query(Reminder).filter(
                Reminder.status == ReminderStatus.pending,
                Reminder.scheduled_at <= now,
            ).all()

            result = []
            for r in pending:
                result.append({
                    "reminder_id":    r.id,
                    "patient_id":     r.patient_id,
                    "appointment_id": r.appointment_id,
                    "reminder_type":  r.reminder_type.value,
                    "message":        r.message,
                    "scheduled_at":   r.scheduled_at.isoformat(),
                })

            db.close()
            return result

        except Exception as e:
            logger.error(f"[NOTIFY] Error fetching pending notifications: {e}")
            return []


# ── Singleton instance ─────────────────────────────────────────
notification_service = NotificationService()