# api/appointment_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from database.connection import get_db
from database.models import User, PatientProfile
from auth.dependencies import get_current_user, require_patient
from tools.appointment_tools import (
    get_available_slots,
    get_patient_appointments,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    get_appointment_by_id,
)
from tools.audit_tools import log_audit_event
from schemas.pydantic_schemas import (
    AppointmentBookRequest,
    AppointmentRescheduleRequest,
    AppointmentCancelRequest,
)
import logging

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])
logger = logging.getLogger(__name__)


def _get_patient_id(db: Session, user_id: int) -> int:
    """Helper to get PatientProfile.id from user_id."""
    patient = db.query(PatientProfile).filter(
        PatientProfile.user_id == user_id
    ).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found. Please complete your profile first.",
        )
    return patient.id


@router.get("/slots")
def list_available_slots(
    department_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    days_ahead: int = 14,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns available appointment slots.
    Can filter by department or doctor.
    """
    slots = get_available_slots(
        db=db,
        department_id=department_id,
        doctor_id=doctor_id,
        days_ahead=days_ahead,
    )

    return {
        "slots": slots,
        "total": len(slots),
        "filter": {
            "department_id": department_id,
            "doctor_id":     doctor_id,
            "days_ahead":    days_ahead,
        },
    }


@router.get("/my")
def get_my_appointments(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Returns all appointments for the current patient."""
    patient_id   = _get_patient_id(db, current_user.id)
    appointments = get_patient_appointments(
        db=db,
        patient_id=patient_id,
        status_filter=status_filter,
    )

    return {
        "appointments": appointments,
        "total":        len(appointments),
    }


@router.post("/book", status_code=201)
def book_appointment_route(
    request: AppointmentBookRequest,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Books an appointment for the current patient.
    Enforced: patients can only book for themselves.
    """
    patient_id = _get_patient_id(db, current_user.id)

    try:
        appointment = book_appointment(
            db=db,
            patient_id=patient_id,
            slot_id=request.slot_id,
            reason=request.reason,
            actor_id=current_user.id,
        )

        return {
            "success":     True,
            "message":     (
                f"Appointment booked with {appointment['doctor_name']} "
                f"on {appointment['date']} at {appointment['time']}."
            ),
            "appointment": appointment,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/reschedule")
def reschedule_appointment_route(
    request: AppointmentRescheduleRequest,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Reschedules an existing appointment.
    Patients can only reschedule their own appointments.
    """
    patient_id = _get_patient_id(db, current_user.id)

    # Verify this appointment belongs to the patient
    appt = get_appointment_by_id(db, request.appointment_id)
    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )
    if appt["patient_id"] != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reschedule your own appointments.",
        )

    try:
        updated = reschedule_appointment(
            db=db,
            appointment_id=request.appointment_id,
            new_slot_id=request.new_slot_id,
            actor_id=current_user.id,
        )

        return {
            "success":     True,
            "message":     (
                f"Appointment rescheduled to {updated['date']} "
                f"at {updated['time']}."
            ),
            "appointment": updated,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/cancel")
def cancel_appointment_route(
    request: AppointmentCancelRequest,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Cancels an appointment.
    Patients can only cancel their own appointments.
    """
    patient_id = _get_patient_id(db, current_user.id)

    appt = get_appointment_by_id(db, request.appointment_id)
    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )
    if appt["patient_id"] != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own appointments.",
        )

    try:
        cancelled = cancel_appointment(
            db=db,
            appointment_id=request.appointment_id,
            actor_id=current_user.id,
            reason=request.reason,
        )

        return {
            "success":     True,
            "message":     "Appointment cancelled successfully.",
            "appointment": cancelled,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{appointment_id}")
def get_appointment_detail(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns details of a specific appointment."""
    from database.models import UserRole

    appt = get_appointment_by_id(db, appointment_id)
    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    # Patients can only view their own
    if current_user.role == UserRole.patient:
        patient_id = _get_patient_id(db, current_user.id)
        if appt["patient_id"] != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own appointments.",
            )

    return appt