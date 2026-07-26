# tests/test_api.py
"""End-to-end API tests."""

import pytest


class TestHealthEndpoints:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert data["app"] == "AgentCare"
    
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestPatientRoutes:
    def test_get_own_profile(self, client, patient_token):
        response = client.get(
            "/api/patients/profile",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "john.doe@example.com"
    
    def test_update_profile(self, client, patient_token):
        response = client.put(
            "/api/patients/profile",
            json={"blood_group": "A+"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200


class TestAppointmentRoutes:
    def test_get_available_slots(self, client, patient_token):
        response = client.get(
            "/api/appointments/slots",
            params={"department_id": 1},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
    
    def test_get_my_appointments(self, client, patient_token):
        response = client.get(
            "/api/appointments/my",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200


class TestStaffRoutes:
    def test_dashboard_stats(self, client, staff_token):
        response = client.get(
            "/api/staff/dashboard",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
    
    def test_list_all_appointments(self, client, staff_token):
        response = client.get(
            "/api/staff/appointments",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == 200
    
    def test_slot_statistics(self, client, staff_token):
        response = client.get(
            "/api/staff/slots/stats",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "by_department" in data
    
    def test_audit_log(self, client, staff_token):
        response = client.get(
            "/api/staff/audit-log",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == 200


class TestWorkflowRoutes:
    def test_submit_query_workflow(self, client, patient_token):
        response = client.post(
            "/api/workflow/submit",
            data={"request_text": "What can you do?"},
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("is_query") is True