# tests/test_agents.py
"""Tests for AI agents and their behaviors."""

import pytest


class TestSafetyAgent:
    """Critical: Safety agent must block unsafe medical requests."""
    
    def test_normal_booking_is_safe(self):
        from agents.safety_agent import safety_agent
        result = safety_agent.check_request(
            "Book me a cardiology appointment for tomorrow at 10 AM",
            patient_id=1,
        )
        assert result.get("is_safe") is True
    
    def test_medication_request_is_blocked(self):
        from agents.safety_agent import safety_agent
        result = safety_agent.check_request(
            "What medication should I take for chest pain?",
            patient_id=1,
        )
        assert result.get("is_safe") is False
    
    def test_diagnose_request_is_blocked(self):
        from agents.safety_agent import safety_agent
        result = safety_agent.check_request(
            "Can you diagnose my headache?",
            patient_id=1,
        )
        assert result.get("is_safe") is False
    
    def test_emergency_is_detected(self):
        from agents.safety_agent import safety_agent
        result = safety_agent.is_emergency("I'm having a heart attack right now")
        assert result is True
    
    def test_normal_text_is_not_emergency(self):
        from agents.safety_agent import safety_agent
        result = safety_agent.is_emergency("Book me a cardiology appointment")
        assert result is False
    
    def test_dosage_question_is_blocked(self):
        from agents.safety_agent import safety_agent
        result = safety_agent.check_request(
            "How many mg of aspirin should I take?",
            patient_id=1,
        )
        assert result.get("is_safe") is False


class TestRoutingAgent:
    """Routing agent maps requests to departments correctly."""
    
    def test_cardiology_routing(self):
        from agents.routing_agent import routing_agent
        result = routing_agent.route(
            "Book cardiology appointment for tomorrow at 10 AM"
        )
        assert result.get("department_name") == "Cardiology"
    
    def test_neurology_routing(self):
        from agents.routing_agent import routing_agent
        result = routing_agent.route(
            "I need to see a neurologist next Monday at 3 PM"
        )
        assert result.get("department_name") == "Neurology"
    
    def test_returns_valid_department_id(self):
        from agents.routing_agent import routing_agent
        result = routing_agent.route("Book cardiology appointment")
        assert result.get("department_id") is not None
        assert isinstance(result.get("department_id"), int)


class TestQueryAgent:
    """Query agent handles read-only queries."""
    
    def test_general_query(self):
        from agents.query_agent import query_agent
        result = query_agent.process_query(
            request_text="What can you do?",
            patient_id=1,
            patient_user_id=4,
        )
        assert result.get("success") is True
        assert result.get("type") == "general"
    
    def test_slot_query_by_department(self):
        from agents.query_agent import query_agent
        result = query_agent.process_query(
            request_text="Show me available cardiology slots",
            patient_id=1,
            patient_user_id=4,
        )
        assert result.get("success") is True
        assert result.get("type") == "list_slots"
    
    def test_slot_query_by_doctor(self):
        from agents.query_agent import query_agent
        result = query_agent.process_query(
            request_text="Show me slots for Dr. Aisha Sharma",
            patient_id=1,
            patient_user_id=4,
        )
        assert result.get("success") is True
        assert result.get("data", {}).get("doctor") == "Dr. Aisha Sharma"
    
    def test_doctor_listing_query(self):
        from agents.query_agent import query_agent
        result = query_agent.process_query(
            request_text="Show me doctors in Neurology",
            patient_id=1,
            patient_user_id=4,
        )
        assert result.get("success") is True
        assert result.get("type") == "list_doctors"


class TestCoordinatorAgent:
    """Coordinator orchestrates all other agents."""
    
    def test_query_intent_detection(self):
        from agents.coordinator import coordinator_agent
        
        assert coordinator_agent._is_query_intent("Show me my appointments") is True
        assert coordinator_agent._is_query_intent("What can you do?") is True
        assert coordinator_agent._is_query_intent("List all doctors") is True
    
    def test_action_intent_not_query(self):
        from agents.coordinator import coordinator_agent
        
        assert coordinator_agent._is_query_intent(
            "Book cardiology tomorrow at 10 AM"
        ) is False
        assert coordinator_agent._is_query_intent(
            "Cancel my appointment"
        ) is False
        assert coordinator_agent._is_query_intent(
            "Reschedule to next week"
        ) is False
    
    def test_appointment_keyword_detection(self):
        from agents.coordinator import coordinator_agent
        
        assert coordinator_agent._has_appt_intent("Book me a cardiologist") is True
        assert coordinator_agent._has_appt_intent("Schedule appointment") is True
        assert coordinator_agent._has_appt_intent("Random question") is False


class TestAppointmentAgent:
    """Appointment agent validation logic."""
    
    def test_date_extraction_tomorrow(self):
        from agents.appointment_agent import appointment_agent
        result = appointment_agent._extract_preferred_date("Book for tomorrow")
        assert result is not None
        assert "-" in result  # Should be YYYY-MM-DD format
    
    def test_date_extraction_weekday(self):
        from agents.appointment_agent import appointment_agent
        result = appointment_agent._extract_preferred_date("Book for Wednesday")
        assert result is not None
    
    def test_hour_extraction_am(self):
        from agents.appointment_agent import appointment_agent
        result = appointment_agent._extract_preferred_hour("Book at 10 AM")
        assert result == 10
    
    def test_hour_extraction_pm(self):
        from agents.appointment_agent import appointment_agent
        result = appointment_agent._extract_preferred_hour("Book at 3 PM")
        assert result == 15
    
    def test_hour_extraction_noon(self):
        from agents.appointment_agent import appointment_agent
        result = appointment_agent._extract_preferred_hour("Book at noon")
        assert result == 12
    
    def test_datetime_validation_both_missing(self):
        from agents.appointment_agent import appointment_agent
        result = appointment_agent._validate_datetime_specified(
            "Book me a cardiology appointment"
        )
        assert result["valid"] is False
        assert result["missing"] == "both"
    
    def test_datetime_validation_time_missing(self):
        from agents.appointment_agent import appointment_agent
        result = appointment_agent._validate_datetime_specified(
            "Book me a cardiology appointment tomorrow"
        )
        assert result["valid"] is False
        assert result["missing"] == "time"
    
    def test_datetime_validation_both_present(self):
        from agents.appointment_agent import appointment_agent
        result = appointment_agent._validate_datetime_specified(
            "Book me a cardiology appointment tomorrow at 10 AM"
        )
        assert result["valid"] is True