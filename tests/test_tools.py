# tests/test_tools.py
"""Tests for tool functions."""

import pytest


class TestDepartmentTools:
    def test_list_all_departments(self, db_session):
        from tools.department_tools import list_all_departments
        result = list_all_departments(db_session)
        assert isinstance(result, list)
        assert len(result) > 0
        assert any(d["name"] == "Cardiology" for d in result)
    
    def test_get_department_by_name_exact(self, db_session):
        from tools.department_tools import get_department_by_name
        result = get_department_by_name(db_session, "Cardiology")
        assert result is not None
        assert result["name"] == "Cardiology"
    
    def test_get_department_by_name_case_insensitive(self, db_session):
        from tools.department_tools import get_department_by_name
        result = get_department_by_name(db_session, "cardiology")
        assert result is not None
    
    def test_get_department_partial_match(self, db_session):
        from tools.department_tools import get_department_by_name
        result = get_department_by_name(db_session, "Cardio")
        assert result is not None
    
    def test_nonexistent_department_returns_none(self, db_session):
        from tools.department_tools import get_department_by_name
        result = get_department_by_name(db_session, "NonExistentDept")
        assert result is None
    
    def test_find_doctor_by_full_name(self, db_session):
        from tools.department_tools import find_doctor_by_name
        result = find_doctor_by_name(db_session, "Dr. Aisha Sharma")
        assert result is not None
        assert result["name"] == "Dr. Aisha Sharma"
        assert result["department_name"] == "Cardiology"
    
    def test_find_doctor_by_last_name(self, db_session):
        from tools.department_tools import find_doctor_by_name
        result = find_doctor_by_name(db_session, "Sharma")
        assert result is not None
        assert "Sharma" in result["name"]
    
    def test_find_doctor_case_insensitive(self, db_session):
        from tools.department_tools import find_doctor_by_name
        result = find_doctor_by_name(db_session, "aisha sharma")
        assert result is not None
    
    def test_find_nonexistent_doctor(self, db_session):
        from tools.department_tools import find_doctor_by_name
        result = find_doctor_by_name(db_session, "Dr. Nobody")
        assert result is None


class TestAppointmentTools:
    def test_get_available_slots_by_department(self, db_session):
        from tools.appointment_tools import get_available_slots
        result = get_available_slots(db_session, department_id=1)
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_get_available_slots_by_doctor(self, db_session):
        from tools.appointment_tools import get_available_slots
        result = get_available_slots(db_session, doctor_id=1)
        assert isinstance(result, list)
        assert all(s["doctor_id"] == 1 for s in result)
    
    def test_slot_fields_present(self, db_session):
        from tools.appointment_tools import get_available_slots
        slots = get_available_slots(db_session, department_id=1)
        if slots:
            slot = slots[0]
            assert "slot_id" in slot
            assert "doctor_name" in slot
            assert "date" in slot
            assert "time" in slot


class TestDocumentTools:
    def test_classify_ecg_document(self):
        from tools.document_tools import classify_document_type
        from database.models import DocumentType
        result = classify_document_type("john_ecg_report.pdf")
        assert result == DocumentType.ecg
    
    def test_classify_blood_report(self):
        from tools.document_tools import classify_document_type
        from database.models import DocumentType
        result = classify_document_type("cbc_blood_test.pdf")
        assert result == DocumentType.blood_report
    
    def test_classify_xray(self):
        from tools.document_tools import classify_document_type
        from database.models import DocumentType
        result = classify_document_type("chest_xray.jpg")
        assert result == DocumentType.xray
    
    def test_classify_unknown_defaults_to_other(self):
        from tools.document_tools import classify_document_type
        from database.models import DocumentType
        result = classify_document_type("random_file.pdf")
        assert result == DocumentType.other


class TestAuditTools:
    def test_audit_event_creation(self, db_session):
        from tools.audit_tools import log_audit_event
        result = log_audit_event(
            db=db_session,
            action="test_action",
            actor_id=1,
            entity_type="Test",
            entity_id=999,
        )
        assert result is not None
        assert result.action == "test_action"