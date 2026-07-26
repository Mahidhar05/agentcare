# agents/appointment_agent.py

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from services.llm_service import llm_service
from tools.appointment_tools import (
    get_available_slots,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    get_patient_appointments,
)
from database.connection import get_db_session

logger = logging.getLogger(__name__)

APPOINTMENT_SYSTEM_PROMPT = """You are the AgentCare Appointment Scheduling Agent.

Your job is to select the best matching appointment slot from a given list,
based on the patient's stated date and time preferences.

You will be given:
- The current date (TODAY IS)
- A mapping of upcoming weekdays to actual dates (UPCOMING DAYS REFERENCE)
- The patient's request text
- A list of available slots with slot_id, doctor, date, and time

CRITICAL DATE INTERPRETATION RULES:

1. "next Monday" = Use the date shown for "Monday" in UPCOMING DAYS REFERENCE
2. "next Tuesday" = Use the date shown for "Tuesday" in UPCOMING DAYS REFERENCE
3. "tomorrow" = day after today
4. "next week" = 7+ days from today
5. "as soon as possible" / "asap" / "earliest" = pick the earliest available slot
6. Morning preference = pick 9AM-12PM slots
7. Afternoon preference = pick 2PM-5PM slots
8. No preference = pick the earliest available

If the requested exact date has NO available slots, pick the CLOSEST available date.

STRICT RULES:
- ONLY return a slot_id from the AVAILABLE SLOTS list provided
- Do NOT invent slot_ids
- You NEVER give medical advice
- You NEVER recommend treatments or medications

Respond ONLY in this exact JSON format:
{
  "selected_slot_id": integer,
  "reasoning": "brief explanation of why you picked this specific slot and how it matches the patient's date preference",
  "patient_message": "friendly confirmation message mentioning the date and time"
}"""


class AppointmentAgent:
    """
    Appointment Scheduling Agent.
    Detects intent, fetches slots, uses LLM to pick best slot, executes.
    """

    def __init__(self):
        self.llm = llm_service

    def process(
        self,
        request_text: str,
        patient_id: int,
        department_id: int,
        department_name: str,
        actor_id: Optional[int] = None,
        workflow_run_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Main entry point for appointment processing."""
        db = get_db_session()
        try:
            # ── Step 1: Detect intent ──────────────────────────
            intent = self._detect_intent(request_text)
            logger.info(
                f"[APPT AGENT] Intent: {intent} for patient {patient_id}"
            )

            # ── Step 2: Route to correct handler ───────────────
            if intent == "cancel":
                return self._handle_cancel(
                    db, request_text, patient_id, actor_id
                )

            if intent == "view":
                return self._handle_view(db, patient_id)

            if intent == "reschedule":
                return self._handle_reschedule_flow(
                    db, request_text, patient_id,
                    department_id, department_name, actor_id
                )

            # Default: book new appointment
            return self._handle_book(
                db, request_text, patient_id,
                department_id, department_name, actor_id
            )

        except Exception as e:
            logger.error(f"[APPT AGENT] Processing failed: {e}")
            return {
                "success":     False,
                "action":      "error",
                "appointment": None,
                "message":     f"Appointment processing failed: {str(e)}",
            }
        finally:
            db.close()

    def _detect_intent(self, request_text: str) -> str:
        """
        Detects appointment intent from request text.
        Returns: 'book', 'reschedule', 'cancel', or 'view'
        """
        text_lower = request_text.lower()

        cancel_words = [
            "cancel", "cancellation", "remove appointment",
            "drop my appointment"
        ]
        reschedule_words = [
            "reschedule", "re-schedule", "change appointment",
            "change my appointment", "move appointment",
            "move my appointment", "different time",
            "another slot", "shift my appointment"
        ]
        view_words = [
            "view my appointments", "show my appointments",
            "list my appointments", "check my appointment",
            "when is my appointment"
        ]

        # Check most specific first
        if any(w in text_lower for w in cancel_words):
            return "cancel"
        if any(w in text_lower for w in reschedule_words):
            return "reschedule"
        if any(w in text_lower for w in view_words):
            return "view"

        return "book"

    def _handle_view(
        self,
        db: Any,
        patient_id: int,
    ) -> Dict[str, Any]:
        """Returns patient's existing appointments."""
        appointments = get_patient_appointments(db, patient_id)
        return {
            "success":      True,
            "action":       "view",
            "appointments": appointments,
            "appointment":  None,
            "message": (
                f"You have {len(appointments)} appointment(s) on record."
            ),
        }

    def _handle_cancel(
        self,
        db: Any,
        request_text: str,
        patient_id: int,
        actor_id: Optional[int],
    ) -> Dict[str, Any]:
        """Cancels the most recent active appointment."""
        appointments = get_patient_appointments(
            db, patient_id, status_filter="confirmed"
        )
        if not appointments:
            appointments = get_patient_appointments(
                db, patient_id, status_filter="pending"
            )

        if not appointments:
            return {
                "success":     False,
                "action":      "cancel",
                "appointment": None,
                "message":     "No active appointments found to cancel.",
            }

        latest = appointments[0]
        try:
            cancelled = cancel_appointment(
                db=db,
                appointment_id=latest["appointment_id"],
                actor_id=actor_id,
                reason=request_text,
            )
            return {
                "success":     True,
                "action":      "cancel",
                "appointment": cancelled,
                "message": (
                    f"Appointment with {cancelled['doctor_name']} "
                    f"on {cancelled['date']} has been cancelled."
                ),
            }
        except Exception as e:
            logger.error(f"[APPT AGENT] Cancel failed: {e}")
            return {
                "success":     False,
                "action":      "cancel",
                "appointment": None,
                "message":     f"Cancellation failed: {str(e)}",
            }

    def _handle_book(
        self,
        db: Any,
        request_text: str,
        patient_id: int,
        department_id: int,
        department_name: str,
        actor_id: Optional[int],
    ) -> Dict[str, Any]:
        """Books a new appointment with strict date+time validation."""

        # ── STEP 1: Validate date + time provided ─────────────
        validation = self._validate_datetime_specified(request_text)
        if not validation["valid"]:
            missing_msg = {
                "date": "You didn't mention a specific day. ",
                "time": "You didn't mention a specific time. ",
                "both": "Please provide both day and time. ",
            }.get(validation["missing"], "")

            sample_slots = get_available_slots(
                db=db,
                department_id=department_id,
                days_ahead=7,
                exclude_patient_id=patient_id,
            )[:5]

            logger.info(
                f"[APPT AGENT] Rejected — missing {validation['missing']} "
                f"in request: '{request_text[:60]}'"
            )

            return {
                "success":         False,
                "action":          "book",
                "missing_info":    validation["missing"],
                "appointment":     None,
                "available_slots": sample_slots,
                "message": f"{missing_msg}{validation['suggestion']}",
            }

        # ── STEP 2: Fetch available slots ─────────────────────
        slots = get_available_slots(
            db=db,
            department_id=department_id,
            days_ahead=30,
            exclude_patient_id=patient_id,
        )

        if not slots:
            return {
                "success":     False,
                "action":      "book",
                "appointment": None,
                "message":     f"No available slots in {department_name}.",
            }

        # ── STEP 3: Extract preferences ───────────────────────
        preferred_date = self._extract_preferred_date(request_text)
        preferred_hour = self._extract_preferred_hour(request_text)

        logger.info(
            f"[APPT AGENT] Preferences — date={preferred_date}, "
            f"hour={preferred_hour}"
        )

        # ── STEP 4: Find exact match ──────────────────────────
        exact_match = None
        if preferred_date and preferred_hour is not None:
            for s in slots:
                slot_dt = datetime.fromisoformat(s["start_time"])
                if (s["date"] == preferred_date and
                        slot_dt.hour == preferred_hour):
                    exact_match = s
                    break

        # ── STEP 5: If exact match found, book it ─────────────
        if exact_match:
            try:
                appointment = book_appointment(
                    db=db,
                    patient_id=patient_id,
                    slot_id=exact_match["slot_id"],
                    reason=request_text,
                    actor_id=actor_id,
                )
                logger.info(
                    f"[APPT AGENT] Booked EXACT match "
                    f"#{appointment['appointment_id']}"
                )
                return {
                    "success":     True,
                    "action":      "book",
                    "appointment": appointment,
                    "exact_match": True,
                    "message": (
                        f"✅ Booked your preferred slot: "
                        f"{appointment['date']} at {appointment['time']} "
                        f"with {appointment['doctor_name']}."
                    ),
                }
            except ValueError as e:
                logger.error(f"[APPT AGENT] Exact-match book failed: {e}")

        # ── STEP 6: Preferred slot NOT available — return alternatives ──
        alternatives = []
        if preferred_date:
            same_day = [s for s in slots if s["date"] == preferred_date]
            alternatives.extend(same_day[:6])

        if len(alternatives) < 6:
            nearby = [
                s for s in slots
                if s["date"] != preferred_date
            ][:6 - len(alternatives)]
            alternatives.extend(nearby)

        preferred_time_str = ""
        if preferred_hour is not None:
            hour_12 = preferred_hour % 12 or 12
            ampm = "AM" if preferred_hour < 12 else "PM"
            preferred_time_str = f" at {hour_12}:00 {ampm}"

        logger.info(
            f"[APPT AGENT] No exact match for "
            f"{preferred_date}{preferred_time_str}. "
            f"Returning {len(alternatives)} alternatives."
        )

        return {
            "success":         False,
            "action":          "slot_unavailable",
            "appointment":     None,
            "requested_date":  preferred_date,
            "requested_time":  preferred_time_str,
            "available_slots": alternatives[:6],
            "department_name": department_name,
            "message": (
                f"❌ Your preferred slot "
                f"({preferred_date}{preferred_time_str}) is not available.\n\n"
                f"Please choose from the alternatives below."
            ),
        }

    def _handle_reschedule_flow(
        self,
        db: Any,
        request_text: str,
        patient_id: int,
        department_id: int,
        department_name: str,
        actor_id: Optional[int],
    ) -> Dict[str, Any]:
        """Reschedules the most recent active appointment to a new slot."""
        # ── Find existing active appointment ──────────────────
        # Active means: confirmed, pending, OR rescheduled (still upcoming)
        all_active = []
        for status in ["confirmed", "pending", "rescheduled"]:
            appts = get_patient_appointments(
                db, patient_id, status_filter=status
            )
            all_active.extend(appts)

        # Filter to only FUTURE appointments (skip past ones)
        now = datetime.utcnow()
        future_appts = []
        for a in all_active:
            try:
                start = datetime.fromisoformat(a["start_time"])
                if start > now:
                    future_appts.append(a)
            except Exception:
                # If we can't parse, include it anyway
                future_appts.append(a)

        # Sort by start_time ascending (soonest first)
        future_appts.sort(
            key=lambda x: x.get("start_time", ""),
            reverse=False
        )

        if not future_appts:
            return {
                "success":     False,
                "action":      "reschedule",
                "appointment": None,
                "message": (
                    "No upcoming appointments found to reschedule. "
                    "Would you like to book a new appointment instead?"
                ),
            }

        # Take the SOONEST upcoming appointment
        latest_appt = future_appts[0]

        logger.info(
            f"[APPT AGENT] Found appointment #{latest_appt['appointment_id']} "
            f"to reschedule (currently on {latest_appt.get('date')} "
            f"at {latest_appt.get('time')}, status: {latest_appt.get('status')})"
        )

        # Use the SAME department as the existing appointment if possible
        # (rescheduling usually means same doctor/department)
        original_dept_id = latest_appt.get("department_id") or department_id

        # Fetch available slots for that department
        slots = get_available_slots(
            db=db,
            department_id=original_dept_id,
            days_ahead=30,
            exclude_patient_id=patient_id,
        )

        logger.info(
            f"[APPT AGENT] Fetched {len(slots)} available slots "
            f"for department {original_dept_id}"
        )

        # Also exclude the current appointment's slot from options
        # (patient wants to MOVE, not stay)
        current_slot_id = latest_appt.get("slot_id")
        slots = [s for s in slots if s["slot_id"] != current_slot_id]

        slots = self._filter_slots_by_preference(request_text, slots)

        if not slots:
            return {
                "success":     False,
                "action":      "reschedule",
                "appointment": None,
                "message": (
                    "No alternative slots available for rescheduling. "
                    "Please try again later or contact staff."
                ),
            }

        # LLM picks a new slot
        selected_slot_id = self._llm_select_slot(
            request_text, department_name, slots, action="reschedule"
        )

        if not selected_slot_id:
            selected_slot_id = slots[0]["slot_id"]
            logger.warning(
                "[APPT AGENT] LLM didn't select reschedule slot"
            )

        try:
            rescheduled = reschedule_appointment(
                db=db,
                appointment_id=latest_appt["appointment_id"],
                new_slot_id=selected_slot_id,
                actor_id=actor_id,
            )
            logger.info(
                f"[APPT AGENT] Rescheduled appointment #{rescheduled['appointment_id']} "
                f"to slot {selected_slot_id}"
            )
            return {
                "success":     True,
                "action":      "reschedule",
                "appointment": rescheduled,
                "message": (
                    f"Appointment rescheduled to {rescheduled['date']} "
                    f"at {rescheduled['time']} with {rescheduled['doctor_name']}."
                ),
            }
        except ValueError as e:
            logger.error(f"[APPT AGENT] Reschedule failed: {e}")
            return {
                "success":     False,
                "action":      "reschedule",
                "appointment": None,
                "message":     f"Rescheduling failed: {str(e)}",
            }

    def _extract_preferred_date(self, request_text: str) -> Optional[str]:
        """
        Deterministically extracts a requested date from natural language.

        Handles:
        - next Monday/Tuesday/etc.
        - Monday/Tuesday/etc.
        - tomorrow
        - YYYY-MM-DD

        Returns:
            Date string in YYYY-MM-DD format, or None.
        """
        text = request_text.lower()
        today = datetime.now().date()

        # Direct YYYY-MM-DD date
        match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        if match:
            return match.group(1)

        # Tomorrow
        if "tomorrow" in text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")

        weekday_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        for weekday_name, weekday_index in weekday_map.items():
            if weekday_name in text:
                today_index = today.weekday()

                # Next occurrence strictly after today.
                days_ahead = (weekday_index - today_index) % 7
                if days_ahead == 0:
                    days_ahead = 7

                target_date = today + timedelta(days=days_ahead)

                logger.info(
                    f"[APPT AGENT] Parsed date preference: "
                    f"'{weekday_name}' -> {target_date.strftime('%Y-%m-%d')}"
                )

                return target_date.strftime("%Y-%m-%d")

        return None

    def _extract_time_preference(self, request_text: str) -> Optional[str]:
        """
        Extracts broad time preference from request text.
        Returns: morning, afternoon, evening, earliest, or None.
        """
        text = request_text.lower()

        if any(w in text for w in ["morning", "am", "before noon"]):
            return "morning"

        if any(w in text for w in ["afternoon", "pm", "after lunch"]):
            return "afternoon"

        if any(w in text for w in ["evening"]):
            return "evening"

        if any(w in text for w in ["earliest", "as soon as possible", "asap", "soonest"]):
            return "earliest"

        return None
    
    def _extract_preferred_hour(self, request_text: str) -> Optional[int]:
        """
        Extracts the preferred hour (0-23) from natural language.
        Returns None if no time specified.
        """
        import re
        text = request_text.lower()

        # Match "10 AM", "3 PM", "10:30 AM", etc.
        am_match = re.search(r'\b(\d{1,2})\s*(?::\d{2})?\s*(am|a\.m)\b', text)
        if am_match:
            hour = int(am_match.group(1))
            if hour == 12:
                hour = 0
            return hour

        pm_match = re.search(r'\b(\d{1,2})\s*(?::\d{2})?\s*(pm|p\.m)\b', text)
        if pm_match:
            hour = int(pm_match.group(1))
            if hour != 12:
                hour += 12
            return hour

        # Handle "noon"
        if "noon" in text:
            return 12

        # Handle general time preferences (midpoint hour)
        if "morning" in text:
            return 10
        if "afternoon" in text:
            return 15
        if "evening" in text:
            return 18

        return None

    def _validate_datetime_specified(self, request_text: str) -> Dict[str, Any]:
        """
        Validates that the request contains BOTH a date and a time reference.

        Returns:
            {
                'valid': bool,
                'missing': 'date' | 'time' | 'both' | None,
                'has_date': bool,
                'has_time': bool,
                'suggestion': str
            }
        """
        import re
        text = request_text.lower()

        # Check for date indicators
        has_date = bool(self._extract_preferred_date(request_text))

        # Also check for date words
        date_words = [
            "today", "tomorrow", "monday", "tuesday", "wednesday",
            "thursday", "friday", "saturday", "sunday", "next week"
        ]
        if not has_date:
            has_date = any(w in text for w in date_words)

        # Check for specific time
        time_patterns = [
            r'\b\d{1,2}\s*(?:am|pm|a\.m|p\.m)\b',
            r'\b\d{1,2}[:.]\d{2}\s*(?:am|pm)?\b',
            r'\b\d{1,2}\s*o\'?clock\b',
        ]
        has_time = any(re.search(p, text) for p in time_patterns)

        # Also check for time preference words
        time_words = ["morning", "afternoon", "evening", "noon"]
        if not has_time:
            has_time = any(w in text for w in time_words)

        if has_date and has_time:
            return {
                "valid": True, "missing": None,
                "has_date": True, "has_time": True,
                "suggestion": None
            }

        if not has_date and not has_time:
            missing = "both"
        elif not has_date:
            missing = "date"
        else:
            missing = "time"

        return {
            "valid": False,
            "missing": missing,
            "has_date": has_date,
            "has_time": has_time,
            "suggestion": (
                "Please provide both a specific day AND time. "
                "Example: 'Book cardiology for tomorrow at 10 AM' "
                "or 'Book cardiology for Wednesday at 3 PM'"
            ),
        }

    def _filter_slots_by_preference(
        self,
        request_text: str,
        slots: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Applies deterministic date/time filtering before LLM selection.

        This prevents the LLM from choosing Tuesday when the patient asked
        for Wednesday.
        """
        if not slots:
            return slots

        preferred_date = self._extract_preferred_date(request_text)
        time_pref = self._extract_time_preference(request_text)

        filtered = slots

        # Date filtering
        if preferred_date:
            exact_date_slots = [
                s for s in filtered
                if s.get("date") == preferred_date
            ]

            if exact_date_slots:
                logger.info(
                    f"[APPT AGENT] Found {len(exact_date_slots)} slot(s) "
                    f"matching requested date {preferred_date}"
                )
                filtered = exact_date_slots
            else:
                # If exact date not available, choose closest date.
                target = datetime.fromisoformat(preferred_date).date()

                available_dates = sorted({
                    datetime.fromisoformat(s["date"]).date()
                    for s in filtered
                    if s.get("date")
                })

                if available_dates:
                    closest_date = min(
                        available_dates,
                        key=lambda d: abs((d - target).days)
                    )

                    logger.warning(
                        f"[APPT AGENT] No slots on requested date {preferred_date}. "
                        f"Using closest available date {closest_date}."
                    )

                    filtered = [
                        s for s in filtered
                        if s.get("date") == closest_date.strftime("%Y-%m-%d")
                    ]

        # Time filtering
        if time_pref and time_pref != "earliest":
            time_filtered = []

            for s in filtered:
                try:
                    start_dt = datetime.fromisoformat(s["start_time"])
                    hour = start_dt.hour

                    if time_pref == "morning" and 9 <= hour < 12:
                        time_filtered.append(s)
                    elif time_pref == "afternoon" and 12 <= hour < 17:
                        time_filtered.append(s)
                    elif time_pref == "evening" and hour >= 17:
                        time_filtered.append(s)

                except Exception:
                    continue

            if time_filtered:
                logger.info(
                    f"[APPT AGENT] Applied time preference '{time_pref}', "
                    f"{len(time_filtered)} slot(s) remain."
                )
                filtered = time_filtered

        # Always sort chronologically
        filtered = sorted(filtered, key=lambda x: x.get("start_time", ""))

        logger.info(
            f"[APPT AGENT] Slots after preference filtering: {len(filtered)}"
        )

        return filtered    







    def _llm_select_slot(
        self,
        request_text: str,
        department_name: str,
        slots: List[Dict],
        action: str = "book",
    ) -> Optional[int]:
        """Uses LLM to pick the best slot for the patient, considering date preferences."""
        if not slots:
            return None

        slots_summary = self._format_slots_for_llm(slots[:20])

        # ── Give LLM current date context ─────────────────────
        today = datetime.now()
        today_str = today.strftime("%A, %Y-%m-%d")   # e.g. "Saturday, 2026-07-18"

        # Calculate next 7 days for reference
        upcoming_days = []
        for i in range(1, 15):
            future = today + timedelta(days=i)
            upcoming_days.append(
                f"  {future.strftime('%A')} = {future.strftime('%Y-%m-%d')}"
            )
        upcoming_str = "\n".join(upcoming_days)

        try:
            llm_result = self.llm.chat_json(
                system_prompt=APPOINTMENT_SYSTEM_PROMPT,
                user_message=(
                    f"TODAY IS: {today_str}\n\n"
                    f"UPCOMING DAYS REFERENCE:\n{upcoming_str}\n\n"
                    f"Patient request: \"{request_text}\"\n"
                    f"Action needed: {action}\n"
                    f"Department: {department_name}\n\n"
                    f"IMPORTANT RULES:\n"
                    f"- If patient says 'next Monday/Tuesday/etc', use the "
                    f"date from the UPCOMING DAYS REFERENCE above\n"
                    f"- If patient says 'tomorrow', pick date = "
                    f"{(today + timedelta(days=1)).strftime('%Y-%m-%d')}\n"
                    f"- If patient says 'next week', pick a slot 7+ days out\n"
                    f"- Only pick a slot_id from the AVAILABLE SLOTS list below\n"
                    f"- If no exact match for requested date, pick the closest available date\n\n"
                    f"AVAILABLE SLOTS:\n{slots_summary}\n\n"
                    f"Return the slot_id that best matches the patient's date preference."
                ),
            )

            selected = llm_result.get("selected_slot_id")
            if selected:
                # Validate the LLM picked one from our list
                valid_ids = {s["slot_id"] for s in slots}
                if selected in valid_ids:
                    logger.info(
                        f"[APPT AGENT] LLM selected slot {selected}: "
                        f"{llm_result.get('reasoning', 'no reason')[:100]}"
                    )
                    return selected
                else:
                    logger.warning(
                        f"[APPT AGENT] LLM picked slot {selected} "
                        f"not in available list. Available: {list(valid_ids)[:5]}..."
                    )

            return None

        except Exception as e:
            logger.error(f"[APPT AGENT] LLM slot selection failed: {e}")
            return None

    def _format_slots_for_llm(self, slots: List[Dict]) -> str:
        """Formats slot list into readable text for LLM."""
        lines = []
        for s in slots:
            lines.append(
                f"  slot_id={s['slot_id']} | "
                f"doctor={s['doctor_name']} | "
                f"date={s['date']} | "
                f"time={s['time']}"
            )
        return "\n".join(lines)


# ── Singleton instance ─────────────────────────────────────────
appointment_agent = AppointmentAgent()