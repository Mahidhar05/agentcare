# tests/test_safety.py

import pytest
from agents.safety_agent import safety_agent


class TestSafetyAgent:
    """Tests for the Safety Agent — critical for hackathon compliance."""

    def test_safe_appointment_request(self):
        """Normal appointment request should pass safety check."""
        result = safety_agent.check_request(
            request_text="I need to book a cardiology appointment next week",
            patient_id=1,
        )
        assert result.get("is_safe") is True
        assert result.get("is_emergency") is False

    def test_emergency_detection_chest_pain(self):
        """Chest pain should trigger emergency."""
        is_emergency = safety_agent.is_emergency(
            "I'm having severe chest pain right now"
        )
        assert is_emergency is True

    def test_emergency_detection_stroke(self):
        """Stroke keywords should trigger emergency."""
        is_emergency = safety_agent.is_emergency(
            "My father just had a stroke"
        )
        assert is_emergency is True

    def test_non_emergency_normal_request(self):
        """Normal booking request is not an emergency."""
        is_emergency = safety_agent.is_emergency(
            "Book me a general checkup"
        )
        assert is_emergency is False

    def test_keyword_scan_diagnosis(self):
        """Diagnosis words should be flagged."""
        result = safety_agent._keyword_scan(
            "Can you diagnose what disease I have?"
        )
        assert result["flagged"] is True
        assert len(result["matched_keywords"]) > 0

    def test_keyword_scan_prescription(self):
        """Prescription words should be flagged."""
        result = safety_agent._keyword_scan(
            "What medicine should I prescribe for headache?"
        )
        assert result["flagged"] is True

    def test_keyword_scan_clean_request(self):
        """Clean administrative request should pass."""
        result = safety_agent._keyword_scan(
            "Please book my appointment for tomorrow"
        )
        assert result["flagged"] is False

    def test_keyword_scan_administrative(self):
        """Pure administrative language is safe."""
        result = safety_agent._keyword_scan(
            "I want to reschedule my visit and upload my previous reports"
        )
        assert result["flagged"] is False