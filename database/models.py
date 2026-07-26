# database/models.py

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Text, Float, Enum as SAEnum
)
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class UserRole(str, enum.Enum):
    patient = "patient"
    staff   = "staff"
    admin   = "admin"
    doctor  = "doctor"


class AppointmentStatus(str, enum.Enum):
    pending    = "pending"
    confirmed  = "confirmed"
    rescheduled = "rescheduled"
    cancelled  = "cancelled"
    completed  = "completed"


class SlotStatus(str, enum.Enum):
    available = "available"
    booked    = "booked"
    blocked   = "blocked"


class DocumentType(str, enum.Enum):
    ecg             = "ecg"
    blood_report    = "blood_report"
    xray            = "xray"
    mri             = "mri"
    ct_scan         = "ct_scan"
    prescription    = "prescription"
    discharge_summary = "discharge_summary"
    insurance       = "insurance"
    identity        = "identity"
    other           = "other"


class WorkflowStatus(str, enum.Enum):
    started    = "started"
    in_progress = "in_progress"
    completed  = "completed"
    failed     = "failed"
    escalated  = "escalated"


class ReminderType(str, enum.Enum):
    appointment = "appointment"
    document    = "document"
    follow_up   = "follow_up"


class ReminderStatus(str, enum.Enum):
    pending = "pending"
    sent    = "sent"
    missed  = "missed"


class EscalationStatus(str, enum.Enum):
    open     = "open"
    reviewed = "reviewed"
    resolved = "resolved"

class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent    = "sent"
    failed  = "failed"


class NotificationType(str, enum.Enum):
    escalation_alert       = "escalation_alert"
    appointment_confirm    = "appointment_confirm"
    reminder               = "reminder"
    document_confirm       = "document_confirm"
    followup               = "followup"    


# ─────────────────────────────────────────────
# TABLE 1 — User
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(SAEnum(UserRole), default=UserRole.patient, nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False)
    audit_events    = relationship("AuditEvent", back_populates="actor")


# ─────────────────────────────────────────────
# TABLE 2 — PatientProfile
# ─────────────────────────────────────────────

class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id                = Column(Integer, primary_key=True, index=True)
    user_id           = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    date_of_birth     = Column(String(20), nullable=True)
    age               = Column(Integer, nullable=True)
    phone             = Column(String(20), nullable=True)
    gender            = Column(String(20), nullable=True)
    address           = Column(Text, nullable=True)
    preferred_language = Column(String(50), default="English")
    emergency_contact = Column(String(150), nullable=True)
    blood_group       = Column(String(10), nullable=True)
    created_at        = Column(DateTime, default=datetime.utcnow)
    updated_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user          = relationship("User", back_populates="patient_profile")
    appointments  = relationship("Appointment", back_populates="patient")
    documents     = relationship("PatientDocument", back_populates="patient")
    workflow_runs = relationship("WorkflowRun", back_populates="patient")
    reminders     = relationship("Reminder", back_populates="patient")


# ─────────────────────────────────────────────
# TABLE 3 — Department
# ─────────────────────────────────────────────

class Department(Base):
    __tablename__ = "departments"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    active      = Column(Boolean, default=True)

    # Relationships
    doctors = relationship("Doctor", back_populates="department")


# ─────────────────────────────────────────────
# TABLE 4 — Doctor
# ─────────────────────────────────────────────

class Doctor(Base):
    __tablename__ = "doctors"

    id            = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)  # ← NEW
    name          = Column(String(100), nullable=False)
    specialization = Column(String(100), nullable=True)
    qualification  = Column(String(150), nullable=True)
    active        = Column(Boolean, default=True)

    # Relationships
    department   = relationship("Department", back_populates="doctors")
    slots        = relationship("AppointmentSlot", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")
    user         = relationship("User", foreign_keys=[user_id])   # ← NEW


# ─────────────────────────────────────────────
# TABLE 5 — AppointmentSlot
# ─────────────────────────────────────────────

class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id         = Column(Integer, primary_key=True, index=True)
    doctor_id  = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time   = Column(DateTime, nullable=False)
    status     = Column(SAEnum(SlotStatus), default=SlotStatus.available)

    # Relationships
    doctor      = relationship("Doctor", back_populates="slots")
    appointment = relationship("Appointment", back_populates="slot", uselist=False)


# ─────────────────────────────────────────────
# TABLE 6 — Appointment
# ─────────────────────────────────────────────

class Appointment(Base):
    __tablename__ = "appointments"

    id                   = Column(Integer, primary_key=True, index=True)
    patient_id           = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    doctor_id            = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    slot_id              = Column(Integer, ForeignKey("appointment_slots.id"), nullable=False)
    status               = Column(SAEnum(AppointmentStatus), default=AppointmentStatus.pending)
    reason               = Column(Text, nullable=True)
    notes                = Column(Text, nullable=True)
    doctor_notes         = Column(Text, nullable=True)          # ← NEW clinical notes
    consultation_summary = Column(Text, nullable=True)          # ← NEW visit summary
    created_at           = Column(DateTime, default=datetime.utcnow)
    updated_at           = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient   = relationship("PatientProfile", back_populates="appointments")
    doctor    = relationship("Doctor", back_populates="appointments")
    slot      = relationship("AppointmentSlot", back_populates="appointment")
    reminders = relationship("Reminder", back_populates="appointment")


# ─────────────────────────────────────────────
# TABLE 7 — PatientDocument
# ─────────────────────────────────────────────

class PatientDocument(Base):
    __tablename__ = "patient_documents"

    id                 = Column(Integer, primary_key=True, index=True)
    patient_id         = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    document_type      = Column(SAEnum(DocumentType), default=DocumentType.other)
    original_filename  = Column(String(255), nullable=False)
    file_path          = Column(String(500), nullable=False)
    file_size_kb       = Column(Float, nullable=True)
    checksum           = Column(String(64), nullable=True)          # SHA256
    document_date      = Column(String(50), nullable=True)
    description        = Column(Text, nullable=True)
    is_duplicate       = Column(Boolean, default=False)
    created_at         = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("PatientProfile", back_populates="documents")


# ─────────────────────────────────────────────
# TABLE 8 — WorkflowRun
# ─────────────────────────────────────────────

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id           = Column(Integer, primary_key=True, index=True)
    patient_id   = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    current_step = Column(String(100), nullable=True)
    state        = Column(Text, nullable=True)       # JSON string of full agent state
    status       = Column(SAEnum(WorkflowStatus), default=WorkflowStatus.started)
    request_text = Column(Text, nullable=True)       # original patient request
    result       = Column(Text, nullable=True)       # final agent output
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient     = relationship("PatientProfile", back_populates="workflow_runs")
    escalations = relationship("Escalation", back_populates="workflow_run")


# ─────────────────────────────────────────────
# TABLE 9 — Reminder
# ─────────────────────────────────────────────

class Reminder(Base):
    __tablename__ = "reminders"

    id             = Column(Integer, primary_key=True, index=True)
    patient_id     = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    reminder_type  = Column(SAEnum(ReminderType), default=ReminderType.appointment)
    message        = Column(Text, nullable=True)
    scheduled_at   = Column(DateTime, nullable=False)
    status         = Column(SAEnum(ReminderStatus), default=ReminderStatus.pending)
    created_at     = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient     = relationship("PatientProfile", back_populates="reminders")
    appointment = relationship("Appointment", back_populates="reminders")


# ─────────────────────────────────────────────
# TABLE 10 — Escalation
# ─────────────────────────────────────────────

class Escalation(Base):
    __tablename__ = "escalations"

    id              = Column(Integer, primary_key=True, index=True)
    workflow_run_id = Column(Integer, ForeignKey("workflow_runs.id"), nullable=True)
    reason          = Column(Text, nullable=False)
    details         = Column(Text, nullable=True)
    status          = Column(SAEnum(EscalationStatus), default=EscalationStatus.open)
    reviewed_by     = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_note = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflow_run = relationship("WorkflowRun", back_populates="escalations")
    reviewer     = relationship("User", foreign_keys=[reviewed_by])


# ─────────────────────────────────────────────
# TABLE 11 — AuditEvent
# ─────────────────────────────────────────────

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id          = Column(Integer, primary_key=True, index=True)
    actor_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    action      = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id   = Column(Integer, nullable=True)
    meta_data   = Column(Text, nullable=True)       # ✅ renamed from 'metadata' → 'meta_data'
    ip_address  = Column(String(50), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    # Relationships
    actor = relationship("User", back_populates="audit_events")

# ─────────────────────────────────────────────
# TABLE 12 — Notification
# ─────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id                = Column(Integer, primary_key=True, index=True)
    recipient_email   = Column(String(150), nullable=False)
    recipient_name    = Column(String(150), nullable=True)
    subject           = Column(String(255), nullable=False)
    body_html         = Column(Text, nullable=True)
    body_plain        = Column(Text, nullable=True)
    notification_type = Column(SAEnum(NotificationType), default=NotificationType.escalation_alert)
    status            = Column(SAEnum(NotificationStatus), default=NotificationStatus.pending)
    error_message     = Column(Text, nullable=True)

    # Optional links
    escalation_id     = Column(Integer, ForeignKey("escalations.id"), nullable=True)
    workflow_run_id   = Column(Integer, ForeignKey("workflow_runs.id"), nullable=True)

    created_at        = Column(DateTime, default=datetime.utcnow)
    sent_at           = Column(DateTime, nullable=True)    