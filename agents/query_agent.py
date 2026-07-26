# agents/query_agent.py

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from services.llm_service import llm_service
from tools.appointment_tools import (
    get_available_slots,
    get_patient_appointments,
)
from tools.department_tools import (
    list_all_departments,
    get_department_by_name,
    get_doctors_by_department,
    find_doctor_by_name,
)
from tools.document_tools import (
    get_patient_documents,
    check_missing_documents,
)
from database.connection import get_db_session

logger = logging.getLogger(__name__)


QUERY_SYSTEM_PROMPT = """You are the AgentCare Query Agent — a read-only conversational
assistant for patients asking questions about the healthcare system.

IMPORTANT: You understand queries in MULTIPLE LANGUAGES including:
- English
- Hindi (हिंदी) — e.g., "मेरे appointments दिखाओ" = show my appointments
- Tamil (தமிழ்) — e.g., "என் சந்திப்புகள் காட்டு" = show my appointments  
- Telugu (తెలుగు) — e.g., "నా అపాయింట్‌మెంట్స్ చూపించు" = show my appointments

You handle READ-ONLY queries (never book, cancel, or modify anything).

Mental translation examples for classification:
- "मेरे appointments दिखाओ" / "నా అపాయింట్‌మెంట్స్ చూపించు" / "என் சந்திப்புகள்" → list_appointments
- "cardiology स्लॉट्स" / "కార్డియాలజీ స్లాట్‌లు" → list_slots
- "डॉक्टर दिखाओ" / "డాక్టర్లను చూపించు" / "மருத்துவர்கள் காட்டு" → list_doctors
- "मेरे documents" / "నా పత్రాలు" / "என் ஆவணங்கள்" → list_documents

You classify the patient's query into one of these types:

1. "list_slots"        — patient wants to see available appointment slots
2. "list_appointments" — patient wants to see their existing appointments (KEYWORDS: my appointments, मेरे appointments, ना అపాయింట్‌మెంట్స్, என் சந்திப்புகள்)
3. "list_doctors"      — patient wants to see doctor information
4. "list_documents"    — patient wants to see uploaded/missing documents
5. "general"           — general info question

You extract entities:
- department name (Cardiology, Neurology, etc.)
- date (specific date like "July 27" or "next Wednesday")
- doctor name (if mentioned)

STRICT RULES:
- You NEVER book, cancel, or change anything
- You NEVER give medical advice
- You NEVER interpret medical results
- ALWAYS respond in the SAME LANGUAGE the patient used (Hindi→Hindi, Telugu→Telugu, Tamil→Tamil, English→English) for the friendly_response field

Respond ONLY in this exact JSON format:
{
  "query_type": "list_slots or list_appointments or list_doctors or list_documents or general",
  "department_name": "extracted department in English or null",
  "doctor_name": "extracted doctor name or null",
  "date_reference": "the date phrase mentioned, or null",
  "reasoning": "brief explanation of your classification",
  "friendly_response": "a warm 1-2 sentence intro to the results IN THE PATIENT'S LANGUAGE"
}"""


# Add this helper function at the top of the file
from services.llm_service import llm_service

def _translate_to_english(text: str, source_lang: str = "auto") -> str:
    """Translate non-English text to English for intent detection."""
    if not text or len(text) < 3:
        return text
    
    # Simple heuristic: if text has no ASCII letters, translate
    has_english = any(c.isascii() and c.isalpha() for c in text)
    
    # If mostly English, skip translation
    if has_english and sum(1 for c in text if c.isascii() and c.isalpha()) > len(text) * 0.5:
        return text
    
    try:
        prompt = f"""Translate the following healthcare-related text to English. 
Only return the English translation, nothing else. 
Preserve intent (e.g., "show", "book", "list", "cancel").

Text: {text}

English translation:"""
        
        response = llm_service.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        return response.strip()
    except Exception:
        return text  # Fallback to original


class QueryAgent:
    """
    Query Agent — handles READ-ONLY conversational queries.
    Distinct from action agents because it never modifies state.
    """

    def __init__(self):
        self.llm = llm_service

    # ══════════════════════════════════════════════════════
    # MAIN ENTRY POINT
    # ══════════════════════════════════════════════════════
    def process_query(
        self,
        request_text: str,
        patient_id: int,
        patient_user_id: int,
    ) -> Dict[str, Any]:
        """
        Handles read-only patient queries.
        Returns structured data + friendly message.
        """
        db = get_db_session()
        try:
            logger.info(
                f"[QUERY AGENT] Processing query for patient {patient_id}: "
                f"{request_text[:80]}"
            )

            # ── STEP 1: LLM classifies the query ──────────────
            departments = list_all_departments(db)
            dept_list = ", ".join(d["name"] for d in departments)

            classification = self.llm.chat_json(
                system_prompt=QUERY_SYSTEM_PROMPT,
                user_message=(
                    f"Available departments: {dept_list}\n\n"
                    f"Patient query: \"{request_text}\"\n\n"
                    f"Classify the query and extract entities."
                ),
            )

            query_type = classification.get("query_type", "general")
            dept_name = classification.get("department_name")
            doctor_name = classification.get("doctor_name")
            date_ref = classification.get("date_reference")

            logger.info(
                f"[QUERY AGENT] Type={query_type} | "
                f"Dept={dept_name} | Doctor={doctor_name} | Date={date_ref}"
            )

            # ── STEP 2: Route to correct handler ─────────────
            if query_type == "list_slots":
                return self._handle_list_slots(
                    db, patient_id, dept_name, doctor_name, date_ref, classification
                )

            elif query_type == "list_appointments":
                return self._handle_list_appointments(
                    db, patient_id, classification
                )

            elif query_type == "list_doctors":
                return self._handle_list_doctors(
                    db, dept_name, classification
                )

            elif query_type == "list_documents":
                return self._handle_list_documents(
                    db, patient_id, dept_name, classification
                )

            else:
                return self._handle_general(db, request_text, classification)

        except Exception as e:
            logger.error(f"[QUERY AGENT] Failed: {e}")
            return {
                "success":  False,
                "type":     "error",
                "message":  f"Sorry, I couldn't process your query: {str(e)}",
                "data":     None,
            }
        finally:
            db.close()

    # ══════════════════════════════════════════════════════
    # HANDLER 1 — List Slots
    # ══════════════════════════════════════════════════════
    def _handle_list_slots(
        self, db, patient_id, dept_name, doctor_name, date_ref, classification
    ):
        """
        Enhanced handler that works with:
        - Just department name
        - Just doctor name
        - Both
        - Neither (returns error)
        """
        dept = None
        doctor = None

        # ── Priority 1: If doctor name given, look up doctor first ───
        if doctor_name:
            doctor = find_doctor_by_name(db, doctor_name)
            if doctor:
                logger.info(
                    f"[QUERY AGENT] Found doctor: {doctor['name']} "
                    f"in department: {doctor['department_name']}"
                )
                dept_name = doctor["department_name"]
                dept = get_department_by_name(db, dept_name)

        # ── Priority 2: If no doctor or doctor not found, use dept name ───
        if not dept and dept_name:
            dept = get_department_by_name(db, dept_name)

        # ── If we still have nothing, ask for clarification ────
        if not dept and not doctor:
            return {
                "success": False,
                "type":    "list_slots",
                "message": (
                    "Please specify either a department (e.g., Cardiology) "
                    "or a doctor name (e.g., Dr. Aisha Sharma) so I can "
                    "look up the right slots."
                ),
                "data":    {
                    "departments": [d["name"] for d in list_all_departments(db)]
                },
            }

        # ── Parse date if provided ─────────────────────────────
        target_date = None
        if date_ref:
            target_date = self._parse_date(date_ref)

        # ── Fetch slots ────────────────────────────────────────
        if doctor:
            slots = get_available_slots(
                db=db,
                doctor_id=doctor["id"],
                days_ahead=30,
                exclude_patient_id=patient_id,
            )
            logger.info(
                f"[QUERY AGENT] Fetched {len(slots)} slots for "
                f"doctor {doctor['name']} (id={doctor['id']})"
            )
        else:
            slots = get_available_slots(
                db=db,
                department_id=dept["id"],
                days_ahead=30,
                exclude_patient_id=patient_id,
            )
            logger.info(
                f"[QUERY AGENT] Fetched {len(slots)} slots for "
                f"department {dept['name']} (id={dept['id']})"
            )

        # ── Filter by date if specified ────────────────────────
        if target_date:
            slots = [s for s in slots if s["date"] == target_date]

        # ── Build friendly message ─────────────────────────────
        if not slots:
            date_str = f" on {target_date}" if target_date else ""
            if doctor:
                msg = (
                    f"No available slots found for {doctor['name']}"
                    f"{date_str}. Try a different date."
                )
            else:
                msg = (
                    f"No available slots found for {dept['name']}"
                    f"{date_str}. Try a different date."
                )
        else:
            date_str = f" on {target_date}" if target_date else " in the next 30 days"
            if doctor:
                msg = (
                    f"Found {len(slots)} available slot(s) for "
                    f"{doctor['name']}{date_str}."
                )
            else:
                msg = (
                    f"Found {len(slots)} available slot(s) for "
                    f"{dept['name']}{date_str}."
                )

        return {
            "success": True,
            "type":    "list_slots",
            "message": msg,
            "friendly_intro": classification.get(
                "friendly_response", "Here's what I found:"
            ),
            "data": {
                "department":    dept["name"] if dept else None,
                "doctor":        doctor["name"] if doctor else None,
                "date_filter":   target_date,
                "doctor_filter": doctor_name,
                "slots":         slots[:20],
                "total_found":   len(slots),
            },
        }
    # ══════════════════════════════════════════════════════
    # HANDLER 2 — List Appointments
    # ══════════════════════════════════════════════════════
    def _handle_list_appointments(self, db, patient_id, classification):
        appointments = get_patient_appointments(db, patient_id)

        active = [
            a for a in appointments
            if a["status"] in ("confirmed", "pending", "rescheduled")
        ]
        past = [
            a for a in appointments
            if a["status"] in ("completed", "cancelled")
        ]

        if not appointments:
            msg = "You don't have any appointments yet."
        else:
            msg = (
                f"You have {len(active)} upcoming and "
                f"{len(past)} past appointment(s)."
            )

        return {
            "success": True,
            "type":    "list_appointments",
            "message": msg,
            "friendly_intro": classification.get(
                "friendly_response", "Here are your appointments:"
            ),
            "data": {
                "active": active,
                "past":   past,
                "total":  len(appointments),
            },
        }

    # ══════════════════════════════════════════════════════
    # HANDLER 3 — List Doctors
    # ══════════════════════════════════════════════════════
    def _handle_list_doctors(self, db, dept_name, classification):
        if dept_name:
            dept = get_department_by_name(db, dept_name)
            if dept:
                doctors = get_doctors_by_department(db, dept["id"])
                msg = f"Found {len(doctors)} doctor(s) in {dept['name']}."
                return {
                    "success": True,
                    "type":    "list_doctors",
                    "message": msg,
                    "friendly_intro": classification.get(
                        "friendly_response",
                        f"Here are the doctors in {dept['name']}:"
                    ),
                    "data": {
                        "department": dept["name"],
                        "doctors":    doctors,
                    },
                }

        # No department specified — show all departments summary
        departments = list_all_departments(db)
        all_data = []
        for d in departments:
            docs = get_doctors_by_department(db, d["id"])
            all_data.append({
                "department": d["name"],
                "doctors":    docs,
            })

        return {
            "success": True,
            "type":    "list_doctors",
            "message": f"Showing doctors across all {len(departments)} departments.",
            "friendly_intro": classification.get(
                "friendly_response", "Here are all our departments and doctors:"
            ),
            "data": {
                "all_departments": all_data,
            },
        }

    # ══════════════════════════════════════════════════════
    # HANDLER 4 — List Documents
    # ══════════════════════════════════════════════════════
    def _handle_list_documents(self, db, patient_id, dept_name, classification):
        documents = get_patient_documents(db, patient_id)

        missing = []
        if dept_name:
            dept = get_department_by_name(db, dept_name)
            if dept:
                missing = check_missing_documents(db, patient_id, dept["name"])

        if not documents:
            msg = "You haven't uploaded any documents yet."
        else:
            msg = f"You have {len(documents)} document(s) on file."
            if missing:
                msg += f" Still needed for {dept_name}: {', '.join(missing)}."

        return {
            "success": True,
            "type":    "list_documents",
            "message": msg,
            "friendly_intro": classification.get(
                "friendly_response", "Here are your documents:"
            ),
            "data": {
                "documents":         documents,
                "missing_documents": missing,
                "department_filter": dept_name,
            },
        }

    # ══════════════════════════════════════════════════════
    # HANDLER 5 — General Info
    # ══════════════════════════════════════════════════════
    def _handle_general(self, db, request_text, classification):
        return {
            "success": True,
            "type":    "general",
            "message": (
                "I can help you with:\n"
                "• Showing available appointment slots\n"
                "• Listing your appointments\n"
                "• Showing doctor information\n"
                "• Reviewing your uploaded documents\n\n"
                "For booking or changing appointments, "
                "please specify a date and time."
            ),
            "friendly_intro": classification.get(
                "friendly_response", "Here's what I can do:"
            ),
            "data": None,
        }

    # ══════════════════════════════════════════════════════
    # DATE PARSING HELPER
    # ══════════════════════════════════════════════════════
    def _parse_date(self, date_ref: str) -> Optional[str]:
        """
        Parses natural language dates like:
        - 'July 27' → 2026-07-27
        - 'next Wednesday' → correct date
        - '27th July' → 2026-07-27
        - '2026-07-27' → 2026-07-27
        """
        if not date_ref:
            return None

        text = date_ref.lower().strip()
        today = datetime.now().date()

        # Direct YYYY-MM-DD
        match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
        if match:
            return match.group(1)

        # Weekday names
        weekday_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
        }
        for name, idx in weekday_map.items():
            if name in text:
                today_idx = today.weekday()
                days_ahead = (idx - today_idx) % 7
                if days_ahead == 0:
                    days_ahead = 7
                target = today + timedelta(days=days_ahead)
                return target.strftime("%Y-%m-%d")

        # Tomorrow
        if "tomorrow" in text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")

        # "July 27", "27 July", "27th July", "July 27th"
        months = {
            "jan": 1, "january": 1, "feb": 2, "february": 2,
            "mar": 3, "march": 3, "apr": 4, "april": 4,
            "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
            "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
            "oct": 10, "october": 10, "nov": 11, "november": 11,
            "dec": 12, "december": 12,
        }

        # Try "Month Day" pattern
        for mname, mnum in months.items():
            match = re.search(rf'{mname}\s+(\d{{1,2}})', text)
            if match:
                day = int(match.group(1))
                year = today.year
                try:
                    parsed = datetime(year, mnum, day).date()
                    # If it's already past, use next year
                    if parsed < today:
                        parsed = datetime(year + 1, mnum, day).date()
                    return parsed.strftime("%Y-%m-%d")
                except ValueError:
                    pass

            # Try "Day Month" pattern (e.g., "27 July")
            match = re.search(rf'(\d{{1,2}})(?:st|nd|rd|th)?\s+{mname}', text)
            if match:
                day = int(match.group(1))
                year = today.year
                try:
                    parsed = datetime(year, mnum, day).date()
                    if parsed < today:
                        parsed = datetime(year + 1, mnum, day).date()
                    return parsed.strftime("%Y-%m-%d")
                except ValueError:
                    pass

        return None


# ── Singleton ─────────────────────────────────────────────────
query_agent = QueryAgent()