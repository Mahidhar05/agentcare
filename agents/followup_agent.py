# agents/followup_agent.py

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from services.llm_service import llm_service
from services.notification_service import notification_service
from tools.reminder_tools import (
    create_appointment_reminder,
    create_followup_reminder,
    get_patient_reminders,
)
from database.connection import get_db_session

logger = logging.getLogger(__name__)

FOLLOWUP_SYSTEM_PROMPT = """You are the AgentCare Follow-up Coordination Agent.

Your job is to create reminders and follow-up tasks for patients
after their appointments are booked or completed.

You determine:
1. What reminders to create (24h before, 2h before appointment)
2. Whether a follow-up visit should be scheduled
3. What follow-up timeframe is appropriate (based on department only)
4. A friendly message to include in reminders

STRICT RULES:
- You schedule follow-ups based on DEPARTMENT TYPE only, not medical findings
- You NEVER say "come back because your condition requires it"
- Standard follow-up: 7 days for most departments, 14 days for surgical
- You NEVER prescribe or recommend treatments

Respond ONLY in this exact JSON format:
{
  "create_24h_reminder": true or false,
  "create_2h_reminder": true or false,
  "create_followup": true or false,
  "followup_days": 7 or 14 or 30,
  "followup_reason": "administrative reason for follow-up",
  "reminder_message": "friendly reminder message for patient",
  "followup_message": "friendly follow-up message",
  "summary": "brief summary of what was scheduled"
}"""


class FollowUpAgent:
    """
    Follow-up and Reminder Agent.

    Responsibilities:
    - Create pre-appointment reminders (24h and 2h before)
    - Schedule post-appointment follow-up tasks
    - Detect missed or incomplete workflows
    - Send notifications for reminders
    - Return summary of all scheduled tasks
    """

    def __init__(self):
        self.llm = llm_service

    def process(
        self,
        patient_id: int,
        patient_name: str,
        patient_email: str,
        appointment_id: int,
        appointment_datetime: datetime,
        department_name: str,
        doctor_name: str,
        actor_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Creates reminders and follow-up tasks for a booked appointment.

        Args:
            patient_id           : PatientProfile.id
            patient_name         : For notifications
            patient_email        : For notifications
            appointment_id       : Appointment.id
            appointment_datetime : When the appointment is scheduled
            department_name      : For follow-up timing logic
            doctor_name          : For messages
            actor_id             : For audit

        Returns:
            Dict with all created reminders and follow-up tasks
        """
        db = get_db_session()
        try:
            logger.info(
                f"[FOLLOWUP AGENT] Processing follow-up for "
                f"appointment #{appointment_id}, patient {patient_id}"
            )

            # ── Step 1: LLM decides what to schedule ──────────
            llm_result = self.llm.chat_json(
                system_prompt=FOLLOWUP_SYSTEM_PROMPT,
                user_message=(
                    f"Patient: {patient_name}\n"
                    f"Department: {department_name}\n"
                    f"Doctor: {doctor_name}\n"
                    f"Appointment date: "
                    f"{appointment_datetime.strftime('%Y-%m-%d %I:%M %p')}\n\n"
                    f"Determine what reminders and follow-ups to schedule."
                ),
            )

            created_reminders = []
            followup_reminder = None

            # ── Step 2: Create appointment reminders ──────────
            reminders = create_appointment_reminder(
                db=db,
                patient_id=patient_id,
                appointment_id=appointment_id,
                appointment_datetime=appointment_datetime,
                actor_id=actor_id,
            )
            created_reminders.extend(reminders)

            # ── Step 3: Create follow-up reminder ─────────────
            if llm_result.get("create_followup", True):
                followup_days = llm_result.get("followup_days", 7)

                # Adjust based on department
                if department_name in ["Orthopedics", "Neurology"]:
                    followup_days = max(followup_days, 14)

                followup_reminder = create_followup_reminder(
                    db=db,
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    appointment_datetime=appointment_datetime,
                    followup_days=followup_days,
                    actor_id=actor_id,
                )

            # ── Step 4: Send confirmation notification ─────────
            notification_service.send_appointment_confirmation(
                patient_name=patient_name,
                patient_email=patient_email,
                doctor_name=doctor_name,
                department=department_name,
                appointment_date=appointment_datetime.strftime("%Y-%m-%d"),
                appointment_time=appointment_datetime.strftime("%I:%M %p"),
                appointment_id=appointment_id,
            )

            result = {
                "success":           True,
                "reminders_created": created_reminders,
                "followup_reminder": followup_reminder,
                "total_reminders":   len(created_reminders) + (
                    1 if followup_reminder else 0
                ),
                "llm_plan":          llm_result,
                "message":           llm_result.get(
                    "summary",
                    f"Reminders set for your appointment on "
                    f"{appointment_datetime.strftime('%Y-%m-%d')}."
                ),
            }

            logger.info(
                f"[FOLLOWUP AGENT] Created {result['total_reminders']} "
                f"reminders for appointment #{appointment_id}"
            )

            return result

        except Exception as e:
            logger.error(f"[FOLLOWUP AGENT] Processing failed: {e}")
            return {
                "success":           False,
                "reminders_created": [],
                "followup_reminder": None,
                "total_reminders":   0,
                "message":           f"Follow-up scheduling failed: {str(e)}",
            }
        finally:
            db.close()

    def get_patient_reminders(
        self,
        patient_id: int,
    ) -> Dict[str, Any]:
        """Returns all reminders for a patient."""
        db = get_db_session()
        try:
            reminders = get_patient_reminders(db, patient_id)
            pending   = [r for r in reminders if r["status"] == "pending"]
            sent      = [r for r in reminders if r["status"] == "sent"]

            return {
                "total":    len(reminders),
                "pending":  len(pending),
                "sent":     len(sent),
                "reminders": reminders,
            }
        except Exception as e:
            logger.error(
                f"[FOLLOWUP AGENT] Error fetching reminders "
                f"for patient {patient_id}: {e}"
            )
            return {"total": 0, "pending": 0, "sent": 0, "reminders": []}
        finally:
            db.close()


# ── Singleton instance ─────────────────────────────────────────
followup_agent = FollowUpAgent()