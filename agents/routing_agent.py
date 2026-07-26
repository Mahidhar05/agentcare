# agents/routing_agent.py

import logging
from typing import Dict, Any, Optional, List
from services.llm_service import llm_service
from tools.department_tools import (
    list_all_departments,
    get_department_by_name,
    get_doctors_by_department,
)
from database.connection import get_db_session

logger = logging.getLogger(__name__)

ROUTING_SYSTEM_PROMPT = """You are the AgentCare Department Routing Agent.

Your job is to classify administrative patient requests and map them
to the correct hospital department.

You are given a list of available departments and a patient request.
You must select the most appropriate department for administrative routing.

STRICT RULES:
- You route based on ADMINISTRATIVE signals only (body part mentioned, type of visit)
- You NEVER diagnose conditions or interpret symptoms medically
- You NEVER say "you have", "you might have", or "this sounds like [disease]"
- If request is unclear, pick the closest department or "General Medicine"
- If request mentions multiple departments, pick the PRIMARY one
- Emergency requests must be flagged immediately

Respond ONLY in this exact JSON format:
{
  "department_name": "exact department name from the list",
  "department_id": null,
  "confidence": 0.0 to 1.0,
  "routing_reason": "one sentence explaining why this department (no diagnosis language)",
  "is_follow_up": true or false,
  "is_emergency": true or false,
  "alternative_departments": ["dept1", "dept2"],
  "needs_escalation": true or false,
  "escalation_reason": "reason if escalation needed, else null"
}"""


class RoutingAgent:
    """
    Department Routing Agent.

    Responsibilities:
    - Classify the administrative intent of a patient request
    - Map the request to a valid department in the database
    - Handle uncertainty by selecting closest match
    - Flag emergency or unsupported requests for escalation
    - NEVER use diagnosis language
    """

    def __init__(self):
        self.llm = llm_service

    def route(
        self,
        request_text: str,
        safe_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Routes a patient request to the correct department.

        Args:
            request_text : Original or safety-cleaned patient request
            safe_summary : Summary from Safety Agent (preferred input)

        Returns:
            Routing result dict with department_id, department_name, confidence
        """
        db = get_db_session()
        try:
            # ── Get available departments from DB ──────────────
            departments = list_all_departments(db)
            if not departments:
                logger.error("[ROUTING] No departments found in database")
                return self._fallback_routing("No departments available")

            dept_names = [d["name"] for d in departments]
            dept_list_str = "\n".join(
                f"- {d['name']}: {d['description']}"
                for d in departments
            )

            # ── Build prompt ───────────────────────────────────
            input_text = safe_summary or request_text
            user_message = (
                f"Available departments:\n{dept_list_str}\n\n"
                f"Patient request:\n\"{input_text}\"\n\n"
                f"Route this request to the most appropriate department."
            )

            # ── Call LLM ───────────────────────────────────────
            result = self.llm.chat_json(
                system_prompt=ROUTING_SYSTEM_PROMPT,
                user_message=user_message,
            )

            # ── Validate and enrich with DB lookup ────────────
            dept_name = result.get("department_name", "General Medicine")
            dept_info = get_department_by_name(db, dept_name)

            if dept_info:
                result["department_id"]   = dept_info["id"]
                result["department_name"] = dept_info["name"]
            else:
                # Fallback to General Medicine
                fallback = get_department_by_name(db, "General Medicine")
                result["department_id"]   = fallback["id"] if fallback else None
                result["department_name"] = "General Medicine"
                result["confidence"]      = 0.5
                logger.warning(
                    f"[ROUTING] Department '{dept_name}' not found, "
                    f"falling back to General Medicine"
                )

            # ── Get doctors for routed department ──────────────
            if result.get("department_id"):
                doctors = get_doctors_by_department(
                    db, result["department_id"]
                )
                result["available_doctors"] = doctors
            else:
                result["available_doctors"] = []

            logger.info(
                f"[ROUTING] Routed to: {result['department_name']} "
                f"(confidence={result.get('confidence', 0):.2f})"
            )

            return result

        except Exception as e:
            logger.error(f"[ROUTING] Routing failed: {e}")
            return self._fallback_routing(str(e))
        finally:
            db.close()

    def _fallback_routing(self, reason: str) -> Dict[str, Any]:
        """
        Returns a safe fallback routing to General Medicine.
        Used when LLM or DB call fails.
        """
        db = get_db_session()
        try:
            fallback = get_department_by_name(db, "General Medicine")
            doctors  = get_doctors_by_department(
                db, fallback["id"]
            ) if fallback else []

            return {
                "department_name":        "General Medicine",
                "department_id":          fallback["id"] if fallback else None,
                "confidence":             0.3,
                "routing_reason":         f"Fallback routing due to: {reason}",
                "is_follow_up":           False,
                "is_emergency":           False,
                "alternative_departments": [],
                "needs_escalation":       True,
                "escalation_reason":      f"Routing fallback triggered: {reason}",
                "available_doctors":      doctors,
            }
        finally:
            db.close()


# ── Singleton instance ─────────────────────────────────────────
routing_agent = RoutingAgent()