# api/doctor_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from database.connection import get_db
from database.models import (
    User, Doctor, Appointment, AppointmentSlot,
    PatientProfile, PatientDocument, AppointmentStatus, SlotStatus
)
from auth.dependencies import require_doctor
from tools.audit_tools import log_audit_event
import logging

router = APIRouter(prefix="/api/doctor", tags=["Doctor"])
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# HELPER — Get Doctor from logged-in User
# ═══════════════════════════════════════════════════════════════

def _get_doctor_from_user(db: Session, user_id: int) -> Doctor:
    """Get Doctor record from user_id."""
    doctor = db.query(Doctor).filter(Doctor.user_id == user_id).first()
    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor profile not found for this user.",
        )
    return doctor


# ═══════════════════════════════════════════════════════════════
# ENDPOINT 1: Doctor Dashboard Summary
# ═══════════════════════════════════════════════════════════════

@router.get("/dashboard")
def get_doctor_dashboard(
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Returns doctor's dashboard stats."""
    doctor = _get_doctor_from_user(db, current_user.id)
    
    # Today's date range
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)
    
    # Today's appointments
    today_appts = db.query(Appointment).join(AppointmentSlot).filter(
        Appointment.doctor_id == doctor.id,
        AppointmentSlot.start_time >= today,
        AppointmentSlot.start_time < tomorrow,
        Appointment.status.in_([
            AppointmentStatus.confirmed,
            AppointmentStatus.rescheduled,
            AppointmentStatus.completed,
        ])
    ).count()
    
    today_completed = db.query(Appointment).join(AppointmentSlot).filter(
        Appointment.doctor_id == doctor.id,
        AppointmentSlot.start_time >= today,
        AppointmentSlot.start_time < tomorrow,
        Appointment.status == AppointmentStatus.completed,
    ).count()
    
    # This week's stats
    week_total = db.query(Appointment).join(AppointmentSlot).filter(
        Appointment.doctor_id == doctor.id,
        AppointmentSlot.start_time >= today,
        AppointmentSlot.start_time < week_end,
    ).count()
    
    week_completed = db.query(Appointment).join(AppointmentSlot).filter(
        Appointment.doctor_id == doctor.id,
        AppointmentSlot.start_time >= today,
        AppointmentSlot.start_time < week_end,
        Appointment.status == AppointmentStatus.completed,
    ).count()
    
    week_cancelled = db.query(Appointment).join(AppointmentSlot).filter(
        Appointment.doctor_id == doctor.id,
        AppointmentSlot.start_time >= today,
        AppointmentSlot.start_time < week_end,
        Appointment.status == AppointmentStatus.cancelled,
    ).count()
    
    # Total unique patients seen (all-time)
    total_patients = db.query(Appointment.patient_id).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status.in_([
            AppointmentStatus.completed,
            AppointmentStatus.confirmed,
        ])
    ).distinct().count()
    
    # Upcoming (next 7 days, not completed/cancelled)
    upcoming = db.query(Appointment).join(AppointmentSlot).filter(
        Appointment.doctor_id == doctor.id,
        AppointmentSlot.start_time >= tomorrow,
        AppointmentSlot.start_time < week_end,
        Appointment.status.in_([
            AppointmentStatus.confirmed,
            AppointmentStatus.rescheduled,
        ])
    ).count()
    
    return {
        "doctor": {
            "id": doctor.id,
            "name": doctor.name,
            "specialization": doctor.specialization,
            "qualification": doctor.qualification,
        },
        "today": {
            "total": today_appts,
            "completed": today_completed,
            "pending": today_appts - today_completed,
        },
        "this_week": {
            "total": week_total,
            "completed": week_completed,
            "cancelled": week_cancelled,
            "upcoming": upcoming,
        },
        "total_patients_seen": total_patients,
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT 2: Today's Appointments
# ═══════════════════════════════════════════════════════════════

@router.get("/appointments/today")
def get_today_appointments(
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Returns doctor's appointments for today."""
    doctor = _get_doctor_from_user(db, current_user.id)
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    appointments = db.query(Appointment).join(AppointmentSlot).filter(
        Appointment.doctor_id == doctor.id,
        AppointmentSlot.start_time >= today,
        AppointmentSlot.start_time < tomorrow,
    ).order_by(AppointmentSlot.start_time).all()
    
    result = []
    for a in appointments:
        slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == a.slot_id).first()
        patient_profile = db.query(PatientProfile).filter(
            PatientProfile.id == a.patient_id
        ).first()
        patient_user = None
        if patient_profile:
            patient_user = db.query(User).filter(
                User.id == patient_profile.user_id
            ).first()
        
        result.append({
            "appointment_id": a.id,
            "patient_id": a.patient_id,
            "patient_name": patient_user.name if patient_user else "Unknown",
            "patient_email": patient_user.email if patient_user else None,
            "patient_phone": patient_profile.phone if patient_profile else None,
            "patient_age": patient_profile.age if patient_profile else None,
            "patient_gender": patient_profile.gender if patient_profile else None,
            "date": slot.start_time.strftime("%Y-%m-%d") if slot else None,
            "time": slot.start_time.strftime("%I:%M %p") if slot else None,
            "start_time": slot.start_time.isoformat() if slot else None,
            "status": a.status.value,
            "reason": a.reason,
            "doctor_notes": a.doctor_notes,
            "consultation_summary": a.consultation_summary,
        })
    
    return {
        "appointments": result,
        "total": len(result),
        "date": today.strftime("%Y-%m-%d"),
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT 3: Upcoming Appointments (next 7 days)
# ═══════════════════════════════════════════════════════════════

@router.get("/appointments/upcoming")
def get_upcoming_appointments(
    days: int = 7,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Returns doctor's upcoming appointments."""
    doctor = _get_doctor_from_user(db, current_user.id)
    
    tomorrow = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    end_date = tomorrow + timedelta(days=days)
    
    appointments = db.query(Appointment).join(AppointmentSlot).filter(
        Appointment.doctor_id == doctor.id,
        AppointmentSlot.start_time >= tomorrow,
        AppointmentSlot.start_time < end_date,
        Appointment.status.in_([
            AppointmentStatus.confirmed,
            AppointmentStatus.rescheduled,
            AppointmentStatus.pending,
        ])
    ).order_by(AppointmentSlot.start_time).all()
    
    result = []
    for a in appointments:
        slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == a.slot_id).first()
        patient_profile = db.query(PatientProfile).filter(
            PatientProfile.id == a.patient_id
        ).first()
        patient_user = None
        if patient_profile:
            patient_user = db.query(User).filter(
                User.id == patient_profile.user_id
            ).first()
        
        result.append({
            "appointment_id": a.id,
            "patient_id": a.patient_id,
            "patient_name": patient_user.name if patient_user else "Unknown",
            "patient_phone": patient_profile.phone if patient_profile else None,
            "date": slot.start_time.strftime("%Y-%m-%d") if slot else None,
            "time": slot.start_time.strftime("%I:%M %p") if slot else None,
            "start_time": slot.start_time.isoformat() if slot else None,
            "status": a.status.value,
            "reason": a.reason,
        })
    
    return {
        "appointments": result,
        "total": len(result),
        "days_ahead": days,
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT 4: All Doctor's Appointments (paginated)
# ═══════════════════════════════════════════════════════════════

@router.get("/appointments/all")
def get_all_doctor_appointments(
    status_filter: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Returns all appointments for this doctor."""
    doctor = _get_doctor_from_user(db, current_user.id)
    
    query = db.query(Appointment).filter(Appointment.doctor_id == doctor.id)
    
    if status_filter:
        try:
            status_enum = AppointmentStatus(status_filter)
            query = query.filter(Appointment.status == status_enum)
        except ValueError:
            pass
    
    appointments = query.order_by(Appointment.created_at.desc()).limit(limit).all()
    
    result = []
    for a in appointments:
        slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == a.slot_id).first()
        patient_profile = db.query(PatientProfile).filter(
            PatientProfile.id == a.patient_id
        ).first()
        patient_user = None
        if patient_profile:
            patient_user = db.query(User).filter(
                User.id == patient_profile.user_id
            ).first()
        
        result.append({
            "appointment_id": a.id,
            "patient_name": patient_user.name if patient_user else "Unknown",
            "patient_email": patient_user.email if patient_user else None,
            "date": slot.start_time.strftime("%Y-%m-%d") if slot else None,
            "time": slot.start_time.strftime("%I:%M %p") if slot else None,
            "status": a.status.value,
            "reason": a.reason,
            "doctor_notes": a.doctor_notes,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })
    
    return {
        "appointments": result,
        "total": len(result),
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT 5: Get Patient Details
# ═══════════════════════════════════════════════════════════════

@router.get("/patients/{patient_id}")
def get_patient_details(
    patient_id: int,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """
    Returns patient details + past/upcoming appointments + documents.
    Only accessible if this doctor has (or has had) an appointment with the patient.
    """
    doctor = _get_doctor_from_user(db, current_user.id)
    
    # Check doctor-patient relationship
    has_relationship = db.query(Appointment).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.patient_id == patient_id,
    ).first()
    
    if not has_relationship:
        raise HTTPException(
            status_code=403,
            detail="You don't have any appointment with this patient.",
        )
    
    # Get patient info
    patient_profile = db.query(PatientProfile).filter(
        PatientProfile.id == patient_id
    ).first()
    
    if not patient_profile:
        raise HTTPException(status_code=404, detail="Patient not found.")
    
    patient_user = db.query(User).filter(
        User.id == patient_profile.user_id
    ).first()
    
    # Get past appointments with THIS doctor
    past_appts = db.query(Appointment).join(AppointmentSlot).filter(
        Appointment.patient_id == patient_id,
        Appointment.doctor_id == doctor.id,
        Appointment.status.in_([
            AppointmentStatus.completed,
            AppointmentStatus.cancelled,
        ])
    ).order_by(AppointmentSlot.start_time.desc()).limit(10).all()
    
    past_list = []
    for a in past_appts:
        slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == a.slot_id).first()
        past_list.append({
            "appointment_id": a.id,
            "date": slot.start_time.strftime("%Y-%m-%d") if slot else None,
            "time": slot.start_time.strftime("%I:%M %p") if slot else None,
            "status": a.status.value,
            "reason": a.reason,
            "doctor_notes": a.doctor_notes,
            "consultation_summary": a.consultation_summary,
        })
    
    # Get patient's documents
    documents = db.query(PatientDocument).filter(
        PatientDocument.patient_id == patient_id
    ).order_by(PatientDocument.created_at.desc()).limit(20).all()
    
    docs_list = [
        {
            "document_id": d.id,
            "document_type": d.document_type.value,
            "original_filename": d.original_filename,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in documents
    ]
    
    return {
        "patient": {
            "id": patient_profile.id,
            "name": patient_user.name if patient_user else "Unknown",
            "email": patient_user.email if patient_user else None,
            "phone": patient_profile.phone,
            "age": patient_profile.age,
            "gender": patient_profile.gender,
            "date_of_birth": patient_profile.date_of_birth,
            "blood_group": patient_profile.blood_group,
            "emergency_contact": patient_profile.emergency_contact,
            "address": patient_profile.address,
        },
        "past_appointments": past_list,
        "documents": docs_list,
        "total_past_appointments": len(past_list),
        "total_documents": len(docs_list),
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT 6: Add/Update Clinical Notes
# ═══════════════════════════════════════════════════════════════

class DoctorNotesUpdate(BaseModel):
    doctor_notes: Optional[str] = None
    consultation_summary: Optional[str] = None
    mark_completed: Optional[bool] = False


@router.put("/appointments/{appointment_id}/notes")
def update_appointment_notes(
    appointment_id: int,
    request: DoctorNotesUpdate,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Doctor adds clinical notes to an appointment."""
    doctor = _get_doctor_from_user(db, current_user.id)
    
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    
    if appointment.doctor_id != doctor.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own appointments.",
        )
    
    # Update notes
    updated_fields = []
    if request.doctor_notes is not None:
        appointment.doctor_notes = request.doctor_notes
        updated_fields.append("doctor_notes")
    
    if request.consultation_summary is not None:
        appointment.consultation_summary = request.consultation_summary
        updated_fields.append("consultation_summary")
    
    if request.mark_completed:
        appointment.status = AppointmentStatus.completed
        updated_fields.append("status → completed")
    
    appointment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appointment)
    
    log_audit_event(
        db=db,
        action="doctor_notes_updated",
        actor_id=current_user.id,
        entity_type="Appointment",
        entity_id=appointment.id,
        metadata={"updated_fields": updated_fields},
    )
    
    logger.info(
        f"[DOCTOR] Notes updated for appointment #{appointment_id} "
        f"by Dr. {doctor.name}: {updated_fields}"
    )
    
    return {
        "success": True,
        "message": f"Appointment notes updated: {', '.join(updated_fields)}",
        "appointment_id": appointment.id,
        "status": appointment.status.value,
        "doctor_notes": appointment.doctor_notes,
        "consultation_summary": appointment.consultation_summary,
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT 7: Doctor's Patient List (unique patients)
# ═══════════════════════════════════════════════════════════════

@router.get("/patients")
def get_my_patients(
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Returns list of unique patients this doctor has seen or has upcoming appointments with."""
    doctor = _get_doctor_from_user(db, current_user.id)
    
    # Get unique patient IDs
    patient_ids = db.query(Appointment.patient_id).filter(
        Appointment.doctor_id == doctor.id
    ).distinct().all()
    patient_ids = [pid[0] for pid in patient_ids]
    
    result = []
    for pid in patient_ids:
        profile = db.query(PatientProfile).filter(PatientProfile.id == pid).first()
        if not profile:
            continue
        user = db.query(User).filter(User.id == profile.user_id).first()
        
        # Get appointment count with this doctor
        total_appts = db.query(Appointment).filter(
            Appointment.patient_id == pid,
            Appointment.doctor_id == doctor.id,
        ).count()
        
        # Get last appointment date
        last_appt = db.query(Appointment).join(AppointmentSlot).filter(
            Appointment.patient_id == pid,
            Appointment.doctor_id == doctor.id,
        ).order_by(AppointmentSlot.start_time.desc()).first()
        
        last_visit = None
        if last_appt:
            slot = db.query(AppointmentSlot).filter(
                AppointmentSlot.id == last_appt.slot_id
            ).first()
            if slot:
                last_visit = slot.start_time.strftime("%Y-%m-%d")
        
        result.append({
            "patient_id": profile.id,
            "name": user.name if user else "Unknown",
            "email": user.email if user else None,
            "phone": profile.phone,
            "age": profile.age,
            "gender": profile.gender,
            "total_appointments": total_appts,
            "last_visit": last_visit,
        })
    
    return {
        "patients": result,
        "total": len(result),
    }