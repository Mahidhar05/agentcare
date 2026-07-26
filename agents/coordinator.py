# agents/coordinator.py

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from services.llm_service import llm_service
from services.notification_service import notification_service

from agents.safety_agent     import safety_agent
from agents.routing_agent    import routing_agent
from agents.appointment_agent import appointment_agent
from agents.document_agent   import document_agent
from agents.followup_agent   import followup_agent
from agents.query_agent      import query_agent
from agents.knowledge_agent  import knowledge_agent

from tools.patient_tools     import get_or_create_patient_profile
from tools.escalation_tools  import create_escalation
from tools.audit_tools       import log_audit_event

from database.connection import get_db_session
from database.models     import WorkflowRun, WorkflowStatus

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# KEYWORDS
# ══════════════════════════════════════════════════════════════

APPT_KEYWORDS = [
    "book", "schedule", "appointment", "visit", "consult", "see a doctor",
    "checkup", "check-up", "check up", "follow-up", "followup", "follow up",
    "cardiologist", "neurologist", "orthopedic", "orthopedist",
    "pediatrician", "gynecologist", "dermatologist", "ophthalmologist",
    "radiologist", "gastroenterologist",
    "cardiology", "neurology", "orthopedics", "pediatrics",
    "gynecology", "dermatology", "radiology", "ophthalmology",
    "gastroenterology", "general medicine",
]

RESCHEDULE_KEYWORDS = ["reschedule", "change my appointment", "move my appointment"]
CANCEL_KEYWORDS = ["cancel"]

# ══════════════════════════════════════════════════════════════
# KNOWLEDGE QUERY KEYWORDS — For RAG-based answers
# ══════════════════════════════════════════════════════════════
KNOWLEDGE_KEYWORDS = [
    # Hospital info
    "visiting hours", "visiting time", "visit hours", "opening hours",
    "phone number", "contact", "phone", "email", "address",
    "location", "where is", "where are",
    "how much", "how many", "cost", "price", "fee", "charge",
    
    # Insurance / Billing
    "insurance", "insurance plans", "insurance accept", "cashless",
    "payment", "billing", "refund",
    
    # Procedures / Preparation
    "prepare", "preparation", "how to prep", "before",
    "fasting", "fast for", "instructions for",
    "mri", "ct scan", "x-ray", "blood test", "surgery",
    
    # Emergency info
    "emergency", "ambulance", "urgent",
    
    # Department / Services info
    "services", "what does", "what treatment", "what conditions",
    "specialists", "who is", "tell me about",
    
    # Facility / General
    "parking", "cafeteria", "wifi", "accessibility",
    "hospital", "about", "facilities",
    
    # Policy questions
    "policy", "rules", "what if", "can i",
]

QUERY_KEYWORDS = [
    # Show/display verbs
    "show me", "show ", "display ", "list ", "view ", "get ",
    
    # Question words
    "what are", "what is", "what can", "what do",
    "which ", "who is", "who are", "when is", "when are",
    "how many", "how much", "how can", "how do",
    "tell me", "tell about", "info about", "information about",
    "can you help", "can you show",
    
    # Slot queries
    "available slots", "available slot", "slot for", "slots for",
    "slots on", "slots in", "check availability",
    
    # My-data queries
    "my appointment", "my appointments", "my documents",
    "my document", "my records", "my reminders", "my profile",
    "my visits", "my history", "my bookings",
    
    # Doctor queries
    "doctors in", "doctor in", "doctors available", "doctors for",
    "list doctors", "list of doctors", "specialists in",
    
    # Document queries
    "documents needed", "documents required", "what documents",
    "what do i need", "do i need", "am i missing",
]


COORDINATOR_SYSTEM_PROMPT = """You are the AgentCare Coordinator Agent.

You are the master orchestrator of a healthcare administration system.
You understand patient requests and create a clear action plan.

RULES FOR DETECTING NEEDS:

Set "needs_appointment" to TRUE if the request mentions ANY of:
- "book", "schedule", "appointment", "visit", "consult", "see a doctor"
- Any specialist (cardiologist, neurologist, orthopedic, pediatrician, etc.)
- Any body part (heart, brain, knee, eye, skin, stomach, etc.)
- Any department (cardiology, neurology, orthopedics, etc.)
- "follow-up", "checkup", "check-up"
- "reschedule", "change appointment", "move appointment"
- "cancel appointment"

Set "needs_appointment" to FALSE only if request is purely:
- Just uploading documents with no appointment mention
- Only asking to view existing appointments
- General inquiry with no booking intent

Set "needs_document_processing" to TRUE only if a file is attached.

Set "needs_routing" to TRUE unless the request is just viewing/canceling.

STRICT RULES:
- You coordinate ADMINISTRATIVE tasks only
- You NEVER diagnose, prescribe, or recommend treatments
- When in doubt, set needs_appointment=true and needs_routing=true

Respond ONLY in this exact JSON format:
{
  "primary_intent": "book_appointment or reschedule or cancel or upload_document or view_status or general_inquiry",
  "needs_appointment": true or false,
  "needs_document_processing": true or false,
  "needs_routing": true or false,
  "patient_preference": "any scheduling preference mentioned or null",
  "document_hint": "any document type mentioned or null",
  "summary": "one sentence plain-english summary of what needs to be done",
  "coordinator_message": "friendly message to patient about what is happening"
}"""


class CoordinatorAgent:
    """
    Coordinator Agent — Master Orchestrator.
    """

    def __init__(self):
        self.llm = llm_service

    # ══════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════

    def _has_appt_intent(self, text: str) -> bool:
        """Deterministic check — does request mention appointment stuff?"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in APPT_KEYWORDS)

    def _has_cancel_intent(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in CANCEL_KEYWORDS)

    def _is_query_intent(self, text: str) -> bool:
        """Deterministic check — is this a read-only query? Multilingual support."""
        text_lower = text.lower().strip()

        # ═══ ENGLISH strong action words (definitely NOT a query) ═══
        strong_action_words = [
            "book me", "book a", "book an", "book cardiology",
            "book neurology", "book orthopedic", "book dermatology",
            "schedule me", "schedule a", "schedule an", "schedule cardiology",
            "reschedule my", "reschedule the",
            "cancel my", "cancel the", "cancel appointment",
            "upload my", "upload a", "attach my",
        ]
        if any(w in text_lower for w in strong_action_words):
            return False

        if text_lower.startswith(("book ", "schedule ", "reschedule ", "cancel ", "upload ")):
            return False

        # ═══ HINDI action verbs (book/schedule) — NOT a query ═══
        hindi_action_words = [
            "बुक कर", "बुक करें", "बुक करो", "अपॉइंटमेंट बुक",
            "शेड्यूल कर", "शेड्यूल करें",
            "रद्द कर", "कैंसिल कर",
        ]
        if any(w in text for w in hindi_action_words):
            return False

        # ═══ TELUGU action verbs — NOT a query ═══
        telugu_action_words = [
            "బుక్ చేయ", "బుక్ చే", "అపాయింట్‌మెంట్ బుక్",
            "షెడ్యూల్ చే", "రద్దు చే",
        ]
        if any(w in text for w in telugu_action_words):
            return False

        # ═══ TAMIL action verbs — NOT a query ═══
        tamil_action_words = [
            "பதிவு செய்", "முன்பதிவு", "ரத்து செய்",
        ]
        if any(w in text for w in tamil_action_words):
            return False

        # ═══ HINDI query keywords (show/list/view) — IS a query ═══
        hindi_query_words = [
            "दिखाओ", "दिखाएं", "दिखा", "दिखाइए",
            "बताओ", "बताएं", "बताइए",
            "मेरे appointments", "मेरे अपॉइंटमेंट", "मेरी अपॉइंटमेंट",
            "मेरे डॉक्टर", "मेरे documents", "मेरे दस्तावेज़",
            "उपलब्ध slots", "उपलब्ध स्लॉट",
            "क्या है", "कौन है", "कब है", "कहाँ है",
        ]
        if any(w in text for w in hindi_query_words):
            return True

        # ═══ TELUGU query keywords — IS a query ═══
        telugu_query_words = [
            "చూపించు", "చూపించండి", "చూపు",
            "చెప్పు", "చెప్పండి",
            "నా appointments", "నా అపాయింట్‌మెంట్", "నా అపాయింట్‌మెంట్స్",
            "నా డాక్టర్", "నా పత్రాలు",
            "అందుబాటులో", "అందుబాటులో ఉన్న",
            "ఏమిటి", "ఎవరు", "ఎప్పుడు", "ఎక్కడ",
        ]
        if any(w in text for w in telugu_query_words):
            return True

        # ═══ TAMIL query keywords — IS a query ═══
        tamil_query_words = [
            "காட்டு", "காட்டுங்கள்", "காண்பி",
            "சொல்லு", "சொல்லுங்கள்",
            "என் appointments", "என் சந்திப்பு", "என் சந்திப்புகள்",
            "என் மருத்துவர்", "என் ஆவணங்கள்",
            "கிடைக்கும்", "இருக்கும்",
        ]
        if any(w in text for w in tamil_query_words):
            return True

        # ═══ ENGLISH question starters ═══
        question_starters = [
            "what ", "who ", "which ", "when ", "where ", "why ", "how ",
            "tell me", "can you", "could you", "do i", "am i",
            "is there", "are there",
        ]
        if any(text_lower.startswith(q) for q in question_starters):
            return True

        # ═══ ENGLISH query starters ═══
        query_starters = ["show ", "list ", "view ", "display ", "get ", "check "]
        if any(text_lower.startswith(q) for q in query_starters):
            return True

        return any(kw in text_lower for kw in QUERY_KEYWORDS)

    def _is_knowledge_query(self, text: str) -> bool:
        """
        Deterministic check — is this a question needing RAG?
        Knowledge questions ask about hospital info, policies, procedures.
        These are different from action queries (show my appointments).
        """
        text_lower = text.lower().strip()
        
        # Explicit action words override knowledge classification
        strong_action_words = [
            "book me", "book a", "book an", "book cardiology",
            "schedule me", "schedule a", "cancel my", "reschedule my",
        ]
        if any(w in text_lower for w in strong_action_words):
            return False
        
        # "Show me" queries with "my" are user-data queries, not knowledge
        if "show me my" in text_lower or "show my" in text_lower:
            return False
        
        # Check for knowledge keywords
        return any(kw in text_lower for kw in KNOWLEDGE_KEYWORDS)

    # ══════════════════════════════════════════════════════════
    # NEW: CONVERSATIONAL MEMORY
    # ══════════════════════════════════════════════════════════

    def _resolve_with_context(
        self,
        current_message: str,
        chat_history: List[Dict[str, str]],
    ) -> str:
        """Uses LLM to resolve vague pronouns using chat history."""
        if not chat_history or len(chat_history) < 2:
            return current_message

        vague_indicators = [
            "the first", "the second", "the third",
            "that one", "this one", "the one",
            "book it", "cancel it", "reschedule it",
            "take the", "book that", "the 10", "the 11",
        ]
        # Only pronouns need context - be strict about single words
        pronoun_only = [" it ", " it.", " it?", " it!", " them ", " those ", " these "]

        msg_lower = " " + current_message.lower() + " "
        needs_resolution = (
            any(ind in current_message.lower() for ind in vague_indicators) or
            any(pron in msg_lower for pron in pronoun_only)
        )

        if not needs_resolution:
            return current_message

        logger.info(
            f"[COORDINATOR] Message may need context resolution: '{current_message}'"
        )

        try:
            history_text = self._format_history_for_context(chat_history)

            resolution_prompt = """You rewrite vague user messages into complete standalone messages using conversation history.

RULES:
- If user says "book the 10 AM one" and history shows cardiology slots, rewrite as "Book cardiology appointment for [date] at 10 AM"
- If user says "reschedule it" and history mentions an appointment, rewrite as "Reschedule my [department] appointment"
- If user says "the first one" and bot listed doctors, use the first doctor's name
- Preserve the user's intent exactly
- If message is already clear, return it unchanged
- Do NOT invent details not in the history

Respond ONLY in this JSON format:
{
  "resolved_message": "the rewritten complete message",
  "was_resolved": true or false,
  "reasoning": "brief explanation"
}"""

            result = self.llm.chat_json(
                system_prompt=resolution_prompt,
                user_message=(
                    f"CONVERSATION HISTORY:\n{history_text}\n\n"
                    f"CURRENT MESSAGE: \"{current_message}\"\n\n"
                    f"Rewrite the current message to be complete and standalone."
                ),
            )

            resolved = result.get("resolved_message", current_message)
            was_resolved = result.get("was_resolved", False)

            if was_resolved and resolved != current_message:
                logger.info(
                    f"[COORDINATOR] Context resolved: '{current_message}' → '{resolved}'"
                )
                return resolved

            return current_message

        except Exception as e:
            logger.warning(f"[COORDINATOR] Context resolution failed: {e}")
            return current_message

    def _format_history_for_context(
        self,
        chat_history: List[Dict[str, str]],
    ) -> str:
        """Formats chat history as readable text for LLM."""
        lines = []
        for msg in chat_history[-6:]:
            role = msg.get("role", "user")
            content = str(msg.get("content", ""))[:300]
            prefix = "PATIENT" if role == "user" else "AGENT"
            lines.append(f"{prefix}: {content}")
        return "\n".join(lines)

    # ══════════════════════════════════════════════════════════
    # MAIN RUN METHOD
    # ══════════════════════════════════════════════════════════

    def run(
        self,
        user_id: int,
        request_text: str,
        file_content: Optional[bytes] = None,
        file_name: Optional[str] = None,
        file_description: Optional[str] = None,
        patient_email: Optional[str] = None,
        patient_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Main orchestration method."""
        db = get_db_session()
        workflow_run = None

        try:
            logger.info(
                f"[COORDINATOR] Starting workflow for user {user_id}: "
                f"{request_text[:100]}..."
            )

            # ══════════════════════════════════════════════════
            # NEW: Resolve context from chat history
            # ══════════════════════════════════════════════════
            if chat_history and len(chat_history) >= 2:
                resolved_message = self._resolve_with_context(
                    current_message=request_text,
                    chat_history=chat_history,
                )
                if resolved_message != request_text:
                    logger.info(
                        f"[COORDINATOR] Using context-resolved message: "
                        f"'{resolved_message}'"
                    )
                    request_text = resolved_message

            # ══════════════════════════════════════════════════
            # STEP 1: Get/Create Patient Profile
            # ══════════════════════════════════════════════════
            patient = get_or_create_patient_profile(
                db=db, user_id=user_id, actor_id=user_id
            )
            patient_id = patient["profile_id"]

            # ══════════════════════════════════════════════════
            # STEP 2: Create WorkflowRun
            # ══════════════════════════════════════════════════
            workflow_run = WorkflowRun(
                patient_id=patient_id,
                request_text=request_text,
                current_step="safety_check",
                status=WorkflowStatus.started,
                state=json.dumps({
                    "user_id":      user_id,
                    "request_text": request_text,
                    "has_file":     file_content is not None,
                    "file_name":    file_name,
                }),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(workflow_run)
            db.commit()
            db.refresh(workflow_run)

            log_audit_event(
                db=db,
                action="workflow_started",
                actor_id=user_id,
                entity_type="WorkflowRun",
                entity_id=workflow_run.id,
                metadata={"patient_id": patient_id, "request_text": request_text[:200]},
            )

            # ══════════════════════════════════════════════════
            # STEP 3: Coordinator LLM
            # ══════════════════════════════════════════════════
            self._update_workflow(
                db, workflow_run, "coordinator_analysis",
                WorkflowStatus.in_progress
            )

            coord_result = self.llm.chat_json(
                system_prompt=COORDINATOR_SYSTEM_PROMPT,
                user_message=(
                    f"Patient request:\n\"{request_text}\"\n"
                    f"Has file attached: {file_content is not None}\n"
                    f"File name: {file_name or 'none'}"
                ),
            )

            # Smart override
            has_appt_kw = self._has_appt_intent(request_text)
            has_cancel_kw = self._has_cancel_intent(request_text)

            if has_appt_kw and not coord_result.get("needs_appointment"):
                coord_result["needs_appointment"] = True
                coord_result["needs_routing"] = True

            if has_appt_kw and not coord_result.get("needs_routing"):
                coord_result["needs_routing"] = True

            logger.info(
                f"[COORDINATOR] Intent: {coord_result.get('primary_intent')} | "
                f"needs_appt={coord_result.get('needs_appointment')} | "
                f"needs_docs={coord_result.get('needs_document_processing')} | "
                f"kw_appt={has_appt_kw} | kw_cancel={has_cancel_kw}"
            )

            # ══════════════════════════════════════════════════
            # STEP 4: Safety Agent
            # ══════════════════════════════════════════════════
            self._update_workflow(
                db, workflow_run, "safety_check",
                WorkflowStatus.in_progress
            )

            safety_result = safety_agent.check_request(
                request_text=request_text, patient_id=patient_id
            )

            if not safety_result.get("is_safe", True):
                escalation = None
                if safety_result.get("requires_escalation"):
                    escalation = create_escalation(
                        db=db,
                        reason=safety_result.get("blocked_reason", "Unsafe request"),
                        workflow_run_id=workflow_run.id,
                        details=(
                            f"Patient request: {request_text}\n"
                            f"Risk level: {safety_result.get('risk_level')}"
                        ),
                        actor_id=user_id,
                    )

                self._update_workflow(
                    db, workflow_run, "blocked_by_safety",
                    WorkflowStatus.escalated,
                    result=json.dumps({
                        "blocked": True,
                        "reason":  safety_result.get("blocked_reason"),
                    })
                )

                return {
                    "success":       False,
                    "blocked":       True,
                    "workflow_id":   workflow_run.id,
                    "message": (
                        "Your request could not be processed as it appears to "
                        "contain content outside our administrative scope. "
                        "For medical advice, please consult a qualified doctor. "
                        + ("This has been flagged for staff review." if escalation else "")
                    ),
                    "safety_result": safety_result,
                    "escalation":    escalation,
                    "patient":       patient,
                }

            if safety_result.get("is_emergency"):
                escalation = create_escalation(
                    db=db,
                    reason="Emergency situation detected",
                    workflow_run_id=workflow_run.id,
                    details=request_text,
                    actor_id=user_id,
                )

                self._update_workflow(
                    db, workflow_run, "emergency_escalated",
                    WorkflowStatus.escalated
                )

                return {
                    "success":     False,
                    "emergency":   True,
                    "workflow_id": workflow_run.id,
                    "message": (
                        "⚠️ Your message indicates a possible emergency. "
                        "Please call 112 immediately or go to the nearest ER. "
                        "A staff member has been alerted."
                    ),
                    "escalation": escalation,
                    "patient":    patient,
                }


            # ══════════════════════════════════════════════════
            # KNOWLEDGE QUERY (RAG-based questions)
            # ══════════════════════════════════════════════════
            if self._is_knowledge_query(request_text):
                logger.info(f"[COORDINATOR] Detected KNOWLEDGE query — using Knowledge Agent (RAG)")
                
                self._update_workflow(
                    db, workflow_run, "knowledge_processing",
                    WorkflowStatus.in_progress
                )
                
                knowledge_result = knowledge_agent.answer_question(request_text)
                
                self._update_workflow(
                    db, workflow_run, "completed",
                    WorkflowStatus.completed,
                    result=json.dumps({
                        "type": "knowledge",
                        "sources": knowledge_result.get("sources", []),
                    }),
                )
                
                log_audit_event(
                    db=db,
                    action="workflow_completed",
                    actor_id=user_id,
                    entity_type="WorkflowRun",
                    entity_id=workflow_run.id,
                    metadata={
                        "type": "knowledge_query",
                        "sources_used": knowledge_result.get("sources", []),
                    },
                )
                
                return {
                    "success":         True,
                    "workflow_id":     workflow_run.id,
                    "is_knowledge":    True,
                    "knowledge_result": knowledge_result,
                    "message":         knowledge_result.get("answer", ""),
                    "safety":          {"risk_level": safety_result.get("risk_level"), "is_safe": True},
                    "patient":         patient,
                }

            # ══════════════════════════════════════════════════
            # QUERY INTENT
            # ══════════════════════════════════════════════════
            if self._is_query_intent(request_text):
                logger.info(f"[COORDINATOR] Detected QUERY intent — using Query Agent")

                self._update_workflow(
                    db, workflow_run, "query_processing",
                    WorkflowStatus.in_progress
                )

                query_result = query_agent.process_query(
                    request_text=request_text,
                    patient_id=patient_id,
                    patient_user_id=user_id,
                )

                self._update_workflow(
                    db, workflow_run, "completed",
                    WorkflowStatus.completed,
                    result=json.dumps({"query_type": query_result.get("type")}),
                )

                log_audit_event(
                    db=db,
                    action="workflow_completed",
                    actor_id=user_id,
                    entity_type="WorkflowRun",
                    entity_id=workflow_run.id,
                    metadata={"query_type": query_result.get("type")},
                )

                return {
                    "success":       True,
                    "workflow_id":   workflow_run.id,
                    "is_query":      True,
                    "query_result":  query_result,
                    "message":       query_result.get("message", ""),
                    "safety":        {"risk_level": safety_result.get("risk_level"), "is_safe": True},
                    "patient":       patient,
                }

            # ══════════════════════════════════════════════════
            # STEP 5: Routing Agent
            # ══════════════════════════════════════════════════
            routing_result = None
            if coord_result.get("needs_routing", True) or has_appt_kw:
                self._update_workflow(
                    db, workflow_run, "department_routing",
                    WorkflowStatus.in_progress
                )

                routing_result = routing_agent.route(
                    request_text=request_text,
                    safe_summary=safety_result.get("safe_summary"),
                )

                if routing_result.get("needs_escalation"):
                    create_escalation(
                        db=db,
                        reason=routing_result.get("escalation_reason", "Routing uncertainty"),
                        workflow_run_id=workflow_run.id,
                        details=f"Request: {request_text}",
                        actor_id=user_id,
                    )

                logger.info(f"[COORDINATOR] Routed to: {routing_result.get('department_name')}")

            # ══════════════════════════════════════════════════
            # STEP 6: Appointment Agent
            # ══════════════════════════════════════════════════
            appointment_result = None
            should_book = (
                coord_result.get("needs_appointment", False)
                or has_appt_kw
                or has_cancel_kw
            )

            if should_book:
                logger.info(
                    f"[COORDINATOR] Proceeding to appointment agent "
                    f"(llm_flag={coord_result.get('needs_appointment')}, "
                    f"kw_match={has_appt_kw})"
                )
                self._update_workflow(
                    db, workflow_run, "appointment_processing",
                    WorkflowStatus.in_progress
                )

                dept_id = routing_result.get("department_id") if routing_result else None
                dept_name = routing_result.get("department_name", "General Medicine") if routing_result else "General Medicine"

                if dept_id:
                    appointment_result = appointment_agent.process(
                        request_text=request_text,
                        patient_id=patient_id,
                        department_id=dept_id,
                        department_name=dept_name,
                        actor_id=user_id,
                        workflow_run_id=workflow_run.id,
                    )

            # ══════════════════════════════════════════════════
            # STEP 7: Document Agent
            # ══════════════════════════════════════════════════
            document_result = None
            if file_content and file_name:
                self._update_workflow(
                    db, workflow_run, "document_processing",
                    WorkflowStatus.in_progress
                )

                dept_name_for_docs = (
                    routing_result.get("department_name")
                    if routing_result else None
                )

                document_result = document_agent.process_upload(
                    file_content=file_content,
                    original_filename=file_name,
                    patient_id=patient_id,
                    patient_name=patient_name or "Patient",
                    patient_email=patient_email or "",
                    department_name=dept_name_for_docs,
                    description=file_description,
                    actor_id=user_id,
                )

            # ══════════════════════════════════════════════════
            # STEP 8: Follow-up Agent
            # ══════════════════════════════════════════════════
            followup_result = None
            appt_data = (
                appointment_result.get("appointment")
                if appointment_result else None
            )

            if appt_data and appointment_result.get("success") and \
               appointment_result.get("action") in ("book", None):
                self._update_workflow(
                    db, workflow_run, "followup_scheduling",
                    WorkflowStatus.in_progress
                )

                try:
                    appt_datetime = datetime.fromisoformat(appt_data["start_time"])
                except Exception:
                    appt_datetime = datetime.utcnow()

                followup_result = followup_agent.process(
                    patient_id=patient_id,
                    patient_name=patient_name or "Patient",
                    patient_email=patient_email or "",
                    appointment_id=appt_data["appointment_id"],
                    appointment_datetime=appt_datetime,
                    department_name=(
                        routing_result.get("department_name", "General Medicine")
                        if routing_result else "General Medicine"
                    ),
                    doctor_name=appt_data.get("doctor_name", "Doctor"),
                    actor_id=user_id,
                )

            # ══════════════════════════════════════════════════
            # STEP 9: Complete
            # ══════════════════════════════════════════════════
            final_result = self._build_final_result(
                workflow_id=workflow_run.id,
                patient=patient,
                coord_result=coord_result,
                safety_result=safety_result,
                routing_result=routing_result,
                appointment_result=appointment_result,
                document_result=document_result,
                followup_result=followup_result,
            )

            self._update_workflow(
                db, workflow_run, "completed",
                WorkflowStatus.completed,
                result=json.dumps({"summary": final_result["summary"]}),
            )

            log_audit_event(
                db=db,
                action="workflow_completed",
                actor_id=user_id,
                entity_type="WorkflowRun",
                entity_id=workflow_run.id,
                metadata={"patient_id": patient_id},
            )

            logger.info(
                f"[COORDINATOR] Workflow #{workflow_run.id} completed "
                f"for patient {patient_id}"
            )

            return final_result

        except Exception as e:
            logger.error(f"[COORDINATOR] Workflow failed: {e}")

            if workflow_run:
                try:
                    self._update_workflow(
                        db, workflow_run, "failed",
                        WorkflowStatus.failed,
                        result=json.dumps({"error": str(e)}),
                    )
                    create_escalation(
                        db=db,
                        reason=f"Workflow system error: {str(e)}",
                        workflow_run_id=workflow_run.id,
                        details=f"Request: {request_text}",
                        actor_id=user_id,
                    )
                except Exception:
                    pass

            return {
                "success":     False,
                "workflow_id": workflow_run.id if workflow_run else None,
                "message": (
                    "We encountered an error processing your request. "
                    "Our staff has been notified. Please try again."
                ),
                "error": str(e),
            }
        finally:
            db.close()

    def _update_workflow(
        self,
        db: Any,
        workflow_run: WorkflowRun,
        step: str,
        status: WorkflowStatus,
        result: Optional[str] = None,
    ) -> None:
        """Updates WorkflowRun record."""
        try:
            workflow_run.current_step = step
            workflow_run.status       = status
            workflow_run.updated_at   = datetime.utcnow()
            if result:
                workflow_run.result = result
            db.commit()
        except Exception as e:
            logger.error(f"[COORDINATOR] Workflow update failed: {e}")

    def _build_final_result(
        self,
        workflow_id: int,
        patient: Dict,
        coord_result: Dict,
        safety_result: Dict,
        routing_result: Optional[Dict],
        appointment_result: Optional[Dict],
        document_result: Optional[Dict],
        followup_result: Optional[Dict],
    ) -> Dict[str, Any]:
        """Builds final combined result dict."""
        messages = []

        if appointment_result and appointment_result.get("success"):
            messages.append(appointment_result.get("message", ""))

        if document_result and document_result.get("success"):
            messages.append(document_result.get("message", ""))
            if document_result.get("missing_docs_message"):
                messages.append(document_result["missing_docs_message"])

        if followup_result and followup_result.get("success"):
            messages.append(followup_result.get("message", ""))

        if not messages:
            messages.append(
                coord_result.get(
                    "coordinator_message",
                    "Your request has been processed successfully."
                )
            )

        summary = " | ".join(m for m in messages if m)

        return {
            "success":     True,
            "workflow_id": workflow_id,
            "patient":     patient,
            "summary":     summary,
            "message":     summary,
            "intent":      coord_result.get("primary_intent"),
            "department":  routing_result,
            "appointment": appointment_result,
            "document":    document_result,
            "followup":    followup_result,
            "safety":      {
                "risk_level": safety_result.get("risk_level"),
                "is_safe":    safety_result.get("is_safe"),
            },
        }


# ── Singleton instance ─────────────────────────────────────────
coordinator_agent = CoordinatorAgent()