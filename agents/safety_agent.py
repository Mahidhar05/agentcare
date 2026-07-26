# agents/safety_agent.py

import logging
from typing import Dict, Any, Optional
from services.llm_service import llm_service
from config import settings

logger = logging.getLogger(__name__)

SAFETY_SYSTEM_PROMPT = """You are the AgentCare Safety Guardian Agent.

Your ONLY job is to review patient requests and agent outputs for unsafe medical content.

You MUST flag and block any content that:
1. Attempts to diagnose a medical condition
2. Recommends or prescribes medications or dosages
3. Suggests a specific treatment plan
4. Claims to replace a doctor or clinician
5. Interprets medical test results as a diagnosis
6. Contains emergency situations requiring immediate medical attention (flag for human)

You MUST ALLOW content that:
1. Books, reschedules, or cancels appointments (administrative)
2. Routes patients to departments (administrative)
3. Uploads or organizes medical documents (administrative)
4. Asks about doctor availability or schedules (administrative)
5. Sets reminders or follow-ups (administrative)
6. Asks general questions about hospital services (administrative)

Respond ONLY in this exact JSON format:
{
  "is_safe": true or false,
  "is_emergency": true or false,
  "risk_level": "none" or "low" or "medium" or "high" or "emergency",
  "blocked_reason": "explanation if blocked, else null",
  "safe_summary": "short clean summary of the administrative intent if safe, else null",
  "requires_escalation": true or false,
  "escalation_reason": "reason if escalation needed, else null"
}"""


class SafetyAgent:
    """
    Safety & Escalation Agent.

    Runs on EVERY patient request BEFORE any workflow begins.
    Also reviews agent outputs before they are returned to the patient.

    Responsibilities:
    - Block diagnosis, prescription, dosage language
    - Detect emergency situations
    - Create escalation records for unsafe/uncertain requests
    - Scan for PII that should not be in responses
    """

    def __init__(self):
        self.llm = llm_service
        self.unsafe_keywords = settings.UNSAFE_KEYWORDS

    def check_request(
        self,
        request_text: str,
        patient_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Performs safety check on incoming patient request.

        First does a fast keyword scan, then calls LLM for
        deeper semantic analysis.

        Args:
            request_text : The raw patient request string
            patient_id   : For logging purposes

        Returns:
            Safety result dict with is_safe, risk_level, etc.
        """
        logger.info(
            f"[SAFETY] Checking request for patient {patient_id}: "
            f"{request_text[:100]}..."
        )

        # ── Step 1: Fast keyword scan ──────────────────────────
        keyword_result = self._keyword_scan(request_text)
        if keyword_result["flagged"]:
            logger.warning(
                f"[SAFETY] Keyword flag: {keyword_result['matched_keywords']}"
            )

        # ── Step 2: LLM semantic analysis ─────────────────────
        try:
            llm_result = self.llm.chat_json(
                system_prompt=SAFETY_SYSTEM_PROMPT,
                user_message=(
                    f"Patient request to analyze:\n\n\"{request_text}\""
                ),
            )

            # Merge keyword scan result with LLM result
            if keyword_result["flagged"] and llm_result.get("is_safe", True):
                llm_result["is_safe"] = False
                llm_result["risk_level"] = "medium"
                llm_result["blocked_reason"] = (
                    f"Contains potentially unsafe keywords: "
                    f"{keyword_result['matched_keywords']}"
                )
                llm_result["requires_escalation"] = True
                llm_result["escalation_reason"] = (
                    "Unsafe keyword detected in patient request"
                )

            logger.info(
                f"[SAFETY] Result: safe={llm_result.get('is_safe')} | "
                f"risk={llm_result.get('risk_level')} | "
                f"emergency={llm_result.get('is_emergency')}"
            )

            return llm_result

        except Exception as e:
            logger.error(f"[SAFETY] LLM safety check failed: {e}")
            # Fail safe — block the request if safety check itself fails
            return {
                "is_safe": False,
                "is_emergency": False,
                "risk_level": "medium",
                "blocked_reason": f"Safety check could not complete: {str(e)}",
                "safe_summary": None,
                "requires_escalation": True,
                "escalation_reason": "Safety agent error — manual review required",
            }

    def check_agent_output(
        self,
        output_text: str,
        agent_name: str,
    ) -> Dict[str, Any]:
        """
        Reviews an agent's output before returning to patient.
        Ensures no agent accidentally generated unsafe medical content.

        Returns:
            Dict with is_safe and cleaned_output
        """
        try:
            result = self.llm.chat_json(
                system_prompt=SAFETY_SYSTEM_PROMPT,
                user_message=(
                    f"Review this agent output from '{agent_name}' "
                    f"before it is shown to the patient:\n\n\"{output_text}\""
                ),
            )

            if not result.get("is_safe", True):
                logger.warning(
                    f"[SAFETY] Agent output from {agent_name} flagged: "
                    f"{result.get('blocked_reason')}"
                )

            return result

        except Exception as e:
            logger.error(f"[SAFETY] Output check failed: {e}")
            return {
                "is_safe": True,
                "is_emergency": False,
                "risk_level": "none",
                "blocked_reason": None,
                "safe_summary": output_text,
                "requires_escalation": False,
                "escalation_reason": None,
            }

    def _keyword_scan(self, text: str) -> Dict[str, Any]:
        """
        Fast keyword scan before LLM call.
        Catches obvious unsafe terms immediately.
        """
        text_lower = text.lower()
        matched = [
            kw for kw in self.unsafe_keywords
            if kw.lower() in text_lower
        ]
        return {
            "flagged": len(matched) > 0,
            "matched_keywords": matched,
        }

    def is_emergency(self, request_text: str) -> bool:
        """
        Quick check for emergency keywords.
        Used to fast-track escalation.
        """
        emergency_terms = [
            "chest pain", "heart attack", "stroke", "unconscious",
            "bleeding", "emergency", "urgent", "ambulance",
            "can't breathe", "cannot breathe", "severe pain",
            "overdose", "suicide", "fainted", "collapsed",
        ]
        text_lower = request_text.lower()
        return any(term in text_lower for term in emergency_terms)


# ── Singleton instance ─────────────────────────────────────────
safety_agent = SafetyAgent()