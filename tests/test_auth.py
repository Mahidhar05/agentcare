# tests/test_auth.py
"""Tests for authentication and authorization."""

import pytest


class TestLogin:
    def test_login_patient_success(self, client):
        response = client.post(
            "/api/auth/login",
            data={"username": "john.doe@example.com", "password": "Patient@123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["role"] == "patient"
        assert data["email"] == "john.doe@example.com"
    
    def test_login_staff_success(self, client):
        response = client.post(
            "/api/auth/login",
            data={"username": "staff1@agentcare.com", "password": "Staff@123"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == "staff"
    
    def test_login_admin_success(self, client):
        response = client.post(
            "/api/auth/login",
            data={"username": "admin@agentcare.com", "password": "Admin@123"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"
    
    def test_login_wrong_password(self, client):
        response = client.post(
            "/api/auth/login",
            data={"username": "john.doe@example.com", "password": "WrongPass"},
        )
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/auth/login",
            data={"username": "nobody@example.com", "password": "Any"},
        )
        assert response.status_code == 401
    
    def test_login_empty_credentials(self, client):
        response = client.post(
            "/api/auth/login",
            data={"username": "", "password": ""},
        )
        assert response.status_code in [401, 422]


class TestRoleEnforcement:
    """Verify backend enforces roles (not just UI)."""
    
    def test_patient_cannot_access_staff_endpoint(self, client, patient_token):
        response = client.get(
            "/api/staff/dashboard",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 403
    
    def test_patient_cannot_view_escalations(self, client, patient_token):
        response = client.get(
            "/api/escalations/open",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 403
    
    def test_staff_can_access_dashboard(self, client, staff_token):
        response = client.get(
            "/api/staff/dashboard",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == 200
    
    def test_staff_can_view_escalations(self, client, staff_token):
        response = client.get(
            "/api/escalations/open",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == 200
    
    def test_no_token_rejected(self, client):
        response = client.get("/api/staff/dashboard")
        assert response.status_code == 401
    
    def test_invalid_token_rejected(self, client):
        response = client.get(
            "/api/staff/dashboard",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert response.status_code == 401


class TestPasswordSecurity:
    def test_passwords_are_hashed(self, db_session):
        from database.models import User
        user = db_session.query(User).filter(
            User.email == "john.doe@example.com"
        ).first()
        assert user is not None
        # Passwords should never be stored in plaintext
        assert user.password_hash != "Patient@123"
        # bcrypt hashes start with $2b$
        assert user.password_hash.startswith("$2b$")