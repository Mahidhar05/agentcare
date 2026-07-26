# services/llm_service.py

import json
import logging
import time
from typing import Optional, Dict, Any, List
from groq import Groq
from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Wrapper around the Groq LLM API.
    All agents use this service to make LLM calls.
    Includes retry logic, error handling, and JSON parsing.
    """

    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.warning(
                "[LLM] GROQ_API_KEY not set. "
                "LLM calls will fail until key is configured."
            )
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model       = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens  = settings.LLM_MAX_TOKENS
        self.max_retries = 3
        self.retry_delay = 2  # seconds between retries

    # ──────────────────────────────────────────────────────────
    # CORE: Chat completion
    # ──────────────────────────────────────────────────────────
    def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Sends a chat completion request to Groq.

        Args:
            system_prompt : Agent's system/role prompt
            user_message  : The user or task message
            temperature   : Override default temperature
            max_tokens    : Override default max tokens
            json_mode     : If True, instructs LLM to return valid JSON

        Returns:
            Raw string response from LLM

        Raises:
            Exception on all retry failures
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ]

        # Add JSON instruction if needed
        if json_mode:
            messages[0]["content"] += (
                "\n\nIMPORTANT: You MUST respond with valid JSON only. "
                "No extra text, no markdown, no explanation outside the JSON."
            )

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    f"[LLM] Attempt {attempt}/{self.max_retries} | "
                    f"model={self.model} | "
                    f"prompt_len={len(user_message)}"
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                )

                content = response.choices[0].message.content.strip()
                logger.debug(f"[LLM] Response length: {len(content)} chars")
                return content

            except Exception as e:
                logger.warning(
                    f"[LLM] Attempt {attempt} failed: {e}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)
                else:
                    logger.error(
                        f"[LLM] All {self.max_retries} attempts failed."
                    )
                    raise

    # ──────────────────────────────────────────────────────────
    # JSON Chat — returns parsed dict
    # ──────────────────────────────────────────────────────────
    def chat_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calls the LLM and parses the response as JSON.

        Returns:
            Parsed dict from LLM response

        Raises:
            ValueError if response cannot be parsed as JSON
        """
        raw = self.chat(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            json_mode=True,
        )

        return self._parse_json_response(raw)

    def chat_json_with_history(
        self,
        system_prompt: str,
        chat_history: List[Dict[str, str]],
        user_message: str,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Sends a chat completion with FULL conversation history.
        
        Args:
            system_prompt: Agent system prompt
            chat_history: List of {"role": "user"/"assistant", "content": "..."}
            user_message: The current message from user
            temperature: LLM temperature
        
        Returns:
            Parsed JSON response
        """
        # Build messages: system + full history + current message
        messages = [{"role": "system", "content": system_prompt + 
                     "\n\nIMPORTANT: You MUST respond with valid JSON only. "
                     "No extra text, no markdown."}]
        
        # Add historical messages (limit to last 10 to avoid token bloat)
        for msg in chat_history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ["user", "assistant"] and content:
                messages.append({
                    "role": role,
                    "content": str(content)[:500]  # Truncate long messages
                })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    f"[LLM] History call | messages={len(messages)} | "
                    f"attempt {attempt}"
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature or self.temperature,
                    max_tokens=self.max_tokens,
                )
                content = response.choices[0].message.content.strip()
                return self._parse_json_response(content)
                
            except Exception as e:
                logger.warning(f"[LLM] History attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)
                else:
                    logger.error(f"[LLM] All {self.max_retries} history attempts failed")
                    return {"error": "llm_call_failed", "message": str(e)}

    # ──────────────────────────────────────────────────────────
    # Multi-turn conversation
    # ──────────────────────────────────────────────────────────
    def chat_with_history(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
    ) -> str:
        """
        Sends a multi-turn conversation to the LLM.

        Args:
            system_prompt : Agent system message
            messages      : List of {"role": "user"/"assistant", "content": "..."}

        Returns:
            LLM response string
        """
        full_messages = [
            {"role": "system", "content": system_prompt}
        ] + messages

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=temperature or self.temperature,
                    max_tokens=self.max_tokens,
                )
                return response.choices[0].message.content.strip()

            except Exception as e:
                logger.warning(f"[LLM] Multi-turn attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)
                else:
                    raise

    # ──────────────────────────────────────────────────────────
    # Internal: JSON parser with cleanup
    # ──────────────────────────────────────────────────────────
    def _parse_json_response(self, raw: str) -> Dict[str, Any]:
        """
        Parses a JSON string from LLM response.
        Handles markdown code blocks and extra whitespace.
        """
        # Strip markdown code blocks if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line (```json or ```) and last line (```)
            lines = lines[1:] if lines[0].startswith("```") else lines
            lines = lines[:-1] if lines and lines[-1].strip() == "```" else lines
            cleaned = "\n".join(lines).strip()

        # Try to extract JSON if there's surrounding text
        if not cleaned.startswith("{") and not cleaned.startswith("["):
            start = cleaned.find("{")
            if start == -1:
                start = cleaned.find("[")
            if start != -1:
                cleaned = cleaned[start:]

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(
                f"[LLM] JSON parse failed: {e}\nRaw response: {raw[:300]}"
            )
            # Return a safe fallback dict instead of crashing
            return {
                "error": "json_parse_failed",
                "raw_response": raw[:500],
            }

    # ──────────────────────────────────────────────────────────
    # Health check
    # ──────────────────────────────────────────────────────────
    def health_check(self) -> Dict[str, Any]:
        """
        Tests the LLM connection with a simple ping.
        Returns status dict.
        """
        try:
            response = self.chat(
                system_prompt="You are a helpful assistant.",
                user_message="Reply with only the word: OK",
                max_tokens=10,
            )
            return {
                "status":  "healthy",
                "model":   self.model,
                "response": response.strip(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "model":  self.model,
                "error":  str(e),
            }


# ── Singleton instance used by all agents ─────────────────────
llm_service = LLMService()