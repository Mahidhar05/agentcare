# tests/test_doctor.py
"""Tests for Doctor Portal endpoints."""

import pytest


class TestDoctorLogin:
    """Doctor should be able to login with the doctor role."""
    
    def test_doctor_login_success(self, client):
        response = client.post(
            "/api/auth/login",
            data={
                "username": "aisha.sharma@agentcare.com",
                "password": "Doctor@123",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "doctor"
        assert data["name"] == "Dr. Aisha Sharma"
    
    def test_multiple_doctors_can_login(self, client):
        for email in [
            "aisha.sharma@agentcare.com",
            "rajan.mehta@agentcare.com",
            "priya.nair@agentcare.com",
        ]:
            response = client.post(
                "/api/auth/login",
                data={"username": email, "password": "Doctor@123"}
            )
            assert response.status_code == 200
            assert response.json()["role"] == "doctor"
    
    def test_doctor_wrong_password(self, client):
        response = client.post(
            "/api/auth/login",
            data={
                "username": "aisha.sharma@agentcare.com",
                "password": "WrongPass",
            }
        )
        assert response.status_code == 401


@pytest.fixture
def doctor_token(client):
    """Returns auth token for Dr. Aisha Sharma."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "aisha.sharma@agentcare.com",
            "password": "Doctor@123",
        }
    )
    return response.json()["access_token"]


class TestDoctorRoleEnforcement:
    """Doctors have their own permissions."""
    
    def test_patient_cannot_access_doctor_endpoints(self, client, patient_token):
        response = client.get(
            "/api/doctor/dashboard",
            headers={"Authorization": f"Bearer {patient_token}"}
        )
        assert response.status_code == 403
    
    def test_staff_cannot_access_doctor_endpoints(self, client, staff_token):
        response = client.get(
            "/api/doctor/dashboard",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert response.status_code == 403
    
    def test_doctor_can_access_dashboard(self, client, doctor_token):
        response = client.get(
            "/api/doctor/dashboard",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
    
    def test_no_token_rejected(self, client):
        response = client.get("/api/doctor/dashboard")
        assert response.status_code == 401


class TestDoctorDashboard:
    """Doctor dashboard returns correct data."""
    
    def test_dashboard_structure(self, client, doctor_token):
        response = client.get(
            "/api/doctor/dashboard",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "doctor" in data
        assert "today" in data
        assert "this_week" in data
        assert "total_patients_seen" in data
    
    def test_dashboard_doctor_info(self, client, doctor_token):
        response = client.get(
            "/api/doctor/dashboard",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        data = response.json()
        doctor = data["doctor"]
        
        assert doctor["name"] == "Dr. Aisha Sharma"
        assert doctor["specialization"] == "Interventional Cardiology"
        assert doctor["qualification"] == "MD, DM Cardiology"
    
    def test_dashboard_stats_are_integers(self, client, doctor_token):
        response = client.get(
            "/api/doctor/dashboard",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        data = response.json()
        
        assert isinstance(data["today"]["total"], int)
        assert isinstance(data["today"]["completed"], int)
        assert isinstance(data["this_week"]["total"], int)
        assert isinstance(data["total_patients_seen"], int)


class TestDoctorAppointments:
    """Doctor appointment endpoints."""
    
    def test_today_appointments_endpoint(self, client, doctor_token):
        response = client.get(
            "/api/doctor/appointments/today",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "appointments" in data
        assert "total" in data
        assert "date" in data
        assert isinstance(data["appointments"], list)
    
    def test_upcoming_appointments_endpoint(self, client, doctor_token):
        response = client.get(
            "/api/doctor/appointments/upcoming",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "appointments" in data
        assert "days_ahead" in data
        assert data["days_ahead"] == 7
    
    def test_upcoming_with_custom_days(self, client, doctor_token):
        response = client.get(
            "/api/doctor/appointments/upcoming",
            params={"days": 14},
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
        assert response.json()["days_ahead"] == 14
    
    def test_all_appointments_endpoint(self, client, doctor_token):
        response = client.get(
            "/api/doctor/appointments/all",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "appointments" in data
        assert isinstance(data["appointments"], list)
    
    def test_all_appointments_status_filter(self, client, doctor_token):
        response = client.get(
            "/api/doctor/appointments/all",
            params={"status_filter": "confirmed"},
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200


class TestDoctorPatients:
    """Doctor's patient list endpoints."""
    
    def test_my_patients_endpoint(self, client, doctor_token):
        response = client.get(
            "/api/doctor/patients",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "patients" in data
        assert "total" in data
        assert isinstance(data["patients"], list)
    
    def test_get_patient_without_relationship(self, client, doctor_token):
        """Doctor cannot view patients they've never seen."""
        # Try patient ID that has no appointment with this doctor
        response = client.get(
            "/api/doctor/patients/999",
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        # Should be 403 (no relationship) or 404 (doesn't exist)
        assert response.status_code in [403, 404]


class TestDoctorNotes:
    """Doctor can add clinical notes to appointments."""
    
    def test_notes_endpoint_requires_valid_appointment(self, client, doctor_token):
        response = client.put(
            "/api/doctor/appointments/99999/notes",
            json={"doctor_notes": "Test note"},
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        assert response.status_code == 404
    
    def test_notes_payload_structure(self, client, doctor_token):
        # Structure test - even if appointment doesn't exist, error should be 404 not 422
        response = client.put(
            "/api/doctor/appointments/1/notes",
            json={
                "doctor_notes": "Patient stable",
                "consultation_summary": "Routine checkup",
                "mark_completed": False,
            },
            headers={"Authorization": f"Bearer {doctor_token}"}
        )
        # 404 (no such appointment for this doctor) or 200 (success)
        assert response.status_code in [200, 403, 404]


class TestDoctorPortalIsolation:
    """Doctor A should not see Doctor B's data."""
    
    def test_different_doctors_have_different_dashboards(self, client):
        # Login as Dr. Aisha
        r1 = client.post(
            "/api/auth/login",
            data={"username": "aisha.sharma@agentcare.com", "password": "Doctor@123"}
        )
        token1 = r1.json()["access_token"]
        
        # Login as Dr. Rajan
        r2 = client.post(
            "/api/auth/login",
            data={"username": "rajan.mehta@agentcare.com", "password": "Doctor@123"}
        )
        token2 = r2.json()["access_token"]
        
        # Get dashboards
        d1 = client.get(
            "/api/doctor/dashboard",
            headers={"Authorization": f"Bearer {token1}"}
        ).json()
        d2 = client.get(
            "/api/doctor/dashboard",
            headers={"Authorization": f"Bearer {token2}"}
        ).json()
        
        # Should be different doctors
        assert d1["doctor"]["name"] != d2["doctor"]["name"]
        assert d1["doctor"]["id"] != d2["doctor"]["id"]