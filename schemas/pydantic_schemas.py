# schemas/pydantic_schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime


# ─────────────────────────────────────────────
# AUTH SCHEMAS
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    name: str
    email: str
    role: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

class RegisterResponse(BaseModel):
    user_id: int
    profile_id: int
    name: str
    email: str
    role: str
    message: str


# ─────────────────────────────────────────────
# PATIENT SCHEMAS
# ─────────────────────────────────────────────

class PatientProfileUpdate(BaseModel):
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact: Optional[str] = None
    blood_group: Optional[str] = None

class PatientProfileResponse(BaseModel):
    profile_id: int
    user_id: int
    name: str
    email: str
    date_of_birth: Optional[str]
    age: Optional[int]
    phone: Optional[str]
    gender: Optional[str]
    address: Optional[str]
    preferred_language: Optional[str]
    emergency_contact: Optional[str]
    blood_group: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


# ─────────────────────────────────────────────
# WORKFLOW SCHEMAS
# ─────────────────────────────────────────────

class WorkflowRequest(BaseModel):
    request_text: str

class WorkflowResponse(BaseModel):
    success: bool
    workflow_id: Optional[int]
    message: str
    intent: Optional[str] = None
    department: Optional[Dict[str, Any]] = None
    appointment: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None
    followup: Optional[Dict[str, Any]] = None
    safety: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────
# APPOINTMENT SCHEMAS
# ─────────────────────────────────────────────

class AppointmentBookRequest(BaseModel):
    slot_id: int
    reason: Optional[str] = None

class AppointmentRescheduleRequest(BaseModel):
    appointment_id: int
    new_slot_id: int

class AppointmentCancelRequest(BaseModel):
    appointment_id: int
    reason: Optional[str] = None

class AppointmentResponse(BaseModel):
    appointment_id: int
    patient_id: int
    doctor_id: int
    doctor_name: str
    slot_id: int
    start_time: Optional[str]
    end_time: Optional[str]
    date: Optional[str]
    time: Optional[str]
    status: str
    reason: Optional[str]
    created_at: Optional[str]


# ─────────────────────────────────────────────
# DOCUMENT SCHEMAS
# ─────────────────────────────────────────────

class DocumentResponse(BaseModel):
    document_id: int
    patient_id: int
    document_type: str
    original_filename: str
    file_size_kb: Optional[float]
    document_date: Optional[str]
    description: Optional[str]
    is_duplicate: bool
    created_at: Optional[str]


# ─────────────────────────────────────────────
# ESCALATION SCHEMAS
# ─────────────────────────────────────────────

class EscalationResolveRequest(BaseModel):
    resolution_note: str
    new_status: Optional[str] = "resolved"

class EscalationResponse(BaseModel):
    escalation_id: int
    workflow_run_id: Optional[int]
    reason: str
    details: Optional[str]
    status: str
    reviewed_by: Optional[int]
    resolution_note: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


# ─────────────────────────────────────────────
# STAFF SCHEMAS
# ─────────────────────────────────────────────

class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    doctor_count: Optional[int] = None

class DoctorResponse(BaseModel):
    id: int
    name: str
    specialization: Optional[str]
    qualification: Optional[str]
    department_id: int

class SlotResponse(BaseModel):
    slot_id: int
    doctor_id: int
    doctor_name: str
    start_time: str
    end_time: str
    date: str
    time: str
    status: str


# ─────────────────────────────────────────────
# GENERIC SCHEMAS
# ─────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True

class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database: str
    llm: Optional[Dict[str, Any]] = None