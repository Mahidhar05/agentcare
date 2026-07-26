# tools/appointment_tools.py

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from database.models import (
    Appointment, AppointmentSlot, Doctor,
    AppointmentStatus, SlotStatus, PatientProfile
)
from tools.audit_tools import log_audit_event

logger = logging.getLogger(__name__)


def get_available_slots(
    db: Session,
    department_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    days_ahead: int = 14,
    exclude_patient_id: Optional[int] = None,   # ← NEW parameter
) -> List[Dict[str, Any]]:
    """
    Returns available appointment slots for a department or specific doctor.
    Filters out past slots and already-booked slots.

    If exclude_patient_id is provided, also excludes slots whose start_time
    conflicts with any existing pending/confirmed appointment for that patient.
    """
    try:
        now = datetime.utcnow()
        future_limit = now + timedelta(days=days_ahead)

        query = db.query(AppointmentSlot).join(Doctor).filter(
            AppointmentSlot.status == SlotStatus.available,
            AppointmentSlot.start_time > now,
            AppointmentSlot.start_time <= future_limit,
            Doctor.active == True,
        )

        if doctor_id:
            query = query.filter(AppointmentSlot.doctor_id == doctor_id)
        elif department_id:
            query = query.filter(Doctor.department_id == department_id)

        slots = query.order_by(AppointmentSlot.start_time).limit(500).all()

        # ── Filter out conflicting slots for this patient ─────
        conflict_times = set()
        if exclude_patient_id:
            existing_appts = db.query(Appointment).join(AppointmentSlot).filter(
                Appointment.patient_id == exclude_patient_id,
                Appointment.status.in_([
                    AppointmentStatus.pending,
                    AppointmentStatus.confirmed,
                    AppointmentStatus.rescheduled,
                ]),
            ).all()

            for appt in existing_appts:
                slot = db.query(AppointmentSlot).filter(
                    AppointmentSlot.id == appt.slot_id
                ).first()
                if slot:
                    conflict_times.add(slot.start_time)

            if conflict_times:
                logger.info(
                    f"[APPT] Filtering out {len(conflict_times)} conflicting "
                    f"time(s) for patient {exclude_patient_id}"
                )

        # Return only non-conflicting slots
        filtered = []
        for s in slots:
            if s.start_time in conflict_times:
                continue
            filtered.append({
                "slot_id":        s.id,
                "doctor_id":      s.doctor_id,
                "doctor_name":    s.doctor.name,
                "specialization": s.doctor.specialization,
                "department_id":  s.doctor.department_id,
                "start_time":     s.start_time.isoformat(),
                "end_time":       s.end_time.isoformat(),
                "status":         s.status.value,
                "date":           s.start_time.strftime("%Y-%m-%d"),
                "time":           s.start_time.strftime("%I:%M %p"),
            })

        # Return top 50 after filtering
        return filtered[:200]

    except Exception as e:
        logger.error(f"[APPT] Error fetching available slots: {e}")
        return []


def book_appointment(
    db: Session,
    patient_id: int,
    slot_id: int,
    reason: Optional[str] = None,
    actor_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Books an appointment for a patient on a specific slot.
    Marks the slot as booked and creates the Appointment record.
    """
    try:
        # Verify slot
        slot = db.query(AppointmentSlot).filter(
            AppointmentSlot.id == slot_id
        ).first()

        if not slot:
            raise ValueError(f"Slot {slot_id} not found.")

        if slot.status != SlotStatus.available:
            raise ValueError(
                f"Slot {slot_id} is not available. "
                f"Current status: {slot.status.value}"
            )

        # Verify patient
        patient = db.query(PatientProfile).filter(
            PatientProfile.id == patient_id
        ).first()
        if not patient:
            raise ValueError(f"Patient profile {patient_id} not found.")

        # Check double-booking
        overlap = db.query(Appointment).join(AppointmentSlot).filter(
            Appointment.patient_id == patient_id,
            Appointment.status.in_([
                AppointmentStatus.pending,
                AppointmentStatus.confirmed
            ]),
            AppointmentSlot.start_time == slot.start_time,
        ).first()

        if overlap:
            raise ValueError(
                f"Patient already has an appointment at "
                f"{slot.start_time.strftime('%Y-%m-%d %I:%M %p')}"
            )

        # Create appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=slot.doctor_id,
            slot_id=slot_id,
            status=AppointmentStatus.confirmed,
            reason=reason,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(appointment)

        # Mark slot booked
        slot.status = SlotStatus.booked
        db.commit()
        db.refresh(appointment)

        log_audit_event(
            db=db,
            action="appointment_booked",
            actor_id=actor_id,
            entity_type="Appointment",
            entity_id=appointment.id,
            metadata={
                "patient_id":  patient_id,
                "doctor_id":   slot.doctor_id,
                "slot_id":     slot_id,
                "start_time":  slot.start_time.isoformat(),
                "reason":      reason,
            },
        )

        logger.info(
            f"[APPT] Booked appointment #{appointment.id} "
            f"for patient {patient_id} with doctor {slot.doctor_id}"
        )


                # ── Send email confirmation to patient ─────────────
        try:
            from services.email_service import email_service
            from database.models import User

            patient_user = db.query(User).filter(User.id == patient.user_id).first()
            if patient_user:
                email_service.send_appointment_confirmation(
                    patient_email=patient_user.email,
                    patient_name=patient_user.name,
                    appointment_id=appointment.id,
                    doctor_name=slot.doctor.name,
                    specialization=slot.doctor.specialization or "",
                    department=slot.doctor.department.name if slot.doctor.department else "",
                    date=slot.start_time.strftime("%Y-%m-%d"),
                    time=slot.start_time.strftime("%I:%M %p"),
                    reason=reason or "",
                )
        except Exception as email_err:
            logger.error(f"[APPT] Email send failed (non-fatal): {email_err}")


        return _appointment_to_dict(appointment, slot)

    except Exception as e:
        logger.error(f"[APPT] Booking failed: {e}")
        db.rollback()
        raise


def reschedule_appointment(
    db: Session,
    appointment_id: int,
    new_slot_id: int,
    actor_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Reschedules an existing appointment to a new slot.
    Frees the old slot and books the new one.
    """
    try:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found.")

        if appointment.status == AppointmentStatus.cancelled:
            raise ValueError("Cannot reschedule a cancelled appointment.")

        if appointment.status == AppointmentStatus.completed:
            raise ValueError("Cannot reschedule a completed appointment.")

        new_slot = db.query(AppointmentSlot).filter(
            AppointmentSlot.id == new_slot_id
        ).first()

        if not new_slot:
            raise ValueError(f"New slot {new_slot_id} not found.")

        if new_slot.status != SlotStatus.available:
            raise ValueError(f"New slot {new_slot_id} is not available.")

        old_slot_id = appointment.slot_id

        # Free old slot
        old_slot = db.query(AppointmentSlot).filter(
            AppointmentSlot.id == old_slot_id
        ).first()
        if old_slot:
            old_slot.status = SlotStatus.available

        # Book new slot
        new_slot.status = SlotStatus.booked
        appointment.slot_id = new_slot_id
        appointment.doctor_id = new_slot.doctor_id
        appointment.status = AppointmentStatus.rescheduled
        appointment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(appointment)

        log_audit_event(
            db=db,
            action="appointment_rescheduled",
            actor_id=actor_id,
            entity_type="Appointment",
            entity_id=appointment_id,
            metadata={
                "old_slot_id": old_slot_id,
                "new_slot_id": new_slot_id,
                "new_start":   new_slot.start_time.isoformat(),
            },
        )

        logger.info(
            f"[APPT] Rescheduled appointment #{appointment_id} "
            f"from slot {old_slot_id} to slot {new_slot_id}"
        )

                # ── Send reschedule email to patient ───────────────
        try:
            from services.email_service import email_service
            from database.models import User, PatientProfile
            
            patient = db.query(PatientProfile).filter(
                PatientProfile.id == appointment.patient_id
            ).first()
            if patient:
                patient_user = db.query(User).filter(User.id == patient.user_id).first()
                if patient_user:
                    email_service.send_appointment_reschedule(
                        patient_email=patient_user.email,
                        patient_name=patient_user.name,
                        appointment_id=appointment.id,
                        doctor_name=new_slot.doctor.name,
                        department=new_slot.doctor.department.name if new_slot.doctor.department else "",
                        new_date=new_slot.start_time.strftime("%Y-%m-%d"),
                        new_time=new_slot.start_time.strftime("%I:%M %p"),
                    )
        except Exception as email_err:
            logger.error(f"[APPT] Reschedule email failed: {email_err}")


        return _appointment_to_dict(appointment, new_slot)

    except Exception as e:
        logger.error(f"[APPT] Reschedule failed: {e}")
        db.rollback()
        raise


def cancel_appointment(
    db: Session,
    appointment_id: int,
    actor_id: Optional[int] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cancels an appointment and frees the slot.
    """
    try:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found.")

        if appointment.status == AppointmentStatus.cancelled:
            raise ValueError("Appointment is already cancelled.")

        if appointment.status == AppointmentStatus.completed:
            raise ValueError("Cannot cancel a completed appointment.")

        # Free the slot
        slot = db.query(AppointmentSlot).filter(
            AppointmentSlot.id == appointment.slot_id
        ).first()
        if slot:
            slot.status = SlotStatus.available

        appointment.status = AppointmentStatus.cancelled
        appointment.notes = (
            f"Cancelled: {reason}" if reason else "Cancelled by user"
        )
        appointment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(appointment)

        log_audit_event(
            db=db,
            action="appointment_cancelled",
            actor_id=actor_id,
            entity_type="Appointment",
            entity_id=appointment_id,
            metadata={"reason": reason},
        )

        logger.info(f"[APPT] Cancelled appointment #{appointment_id}")

                # ── Send cancellation email to patient ─────────────
        try:
            from services.email_service import email_service
            from database.models import User, PatientProfile
            
            patient = db.query(PatientProfile).filter(
                PatientProfile.id == appointment.patient_id
            ).first()
            if patient and slot:
                patient_user = db.query(User).filter(User.id == patient.user_id).first()
                if patient_user:
                    email_service.send_appointment_cancellation(
                        patient_email=patient_user.email,
                        patient_name=patient_user.name,
                        appointment_id=appointment.id,
                        doctor_name=slot.doctor.name if slot.doctor else "Doctor",
                        date=slot.start_time.strftime("%Y-%m-%d") if slot else "N/A",
                        time=slot.start_time.strftime("%I:%M %p") if slot else "N/A",
                    )
        except Exception as email_err:
            logger.error(f"[APPT] Cancel email failed: {email_err}")


        return _appointment_to_dict(appointment, slot)

    except Exception as e:
        logger.error(f"[APPT] Cancellation failed: {e}")
        db.rollback()
        raise


def get_patient_appointments(
    db: Session,
    patient_id: int,
    status_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Returns all appointments for a patient."""
    try:
        query = db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        )

        if status_filter:
            try:
                status_enum = AppointmentStatus(status_filter)
                query = query.filter(Appointment.status == status_enum)
            except ValueError:
                pass

        appointments = query.order_by(
            Appointment.created_at.desc()
        ).all()

        result = []
        for appt in appointments:
            slot = db.query(AppointmentSlot).filter(
                AppointmentSlot.id == appt.slot_id
            ).first()
            result.append(_appointment_to_dict(appt, slot))

        return result

    except Exception as e:
        logger.error(
            f"[APPT] Error fetching appointments for patient {patient_id}: {e}"
        )
        return []


def get_appointment_by_id(
    db: Session,
    appointment_id: int
) -> Optional[Dict[str, Any]]:
    """Fetches a single appointment by ID."""
    try:
        appt = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appt:
            return None

        slot = db.query(AppointmentSlot).filter(
            AppointmentSlot.id == appt.slot_id
        ).first()

        return _appointment_to_dict(appt, slot)

    except Exception as e:
        logger.error(f"[APPT] Error fetching appointment {appointment_id}: {e}")
        return None


def _appointment_to_dict(
    appointment: Appointment,
    slot: Optional[AppointmentSlot]
) -> Dict[str, Any]:
    """Internal helper — converts ORM objects to dict."""
    return {
        "appointment_id": appointment.id,
        "patient_id":     appointment.patient_id,
        "doctor_id":      appointment.doctor_id,
        "doctor_name": (
            slot.doctor.name if slot and slot.doctor else "Unknown"
        ),
        "specialization": (
            slot.doctor.specialization if slot and slot.doctor else None
        ),
        "department_id": (
            slot.doctor.department_id if slot and slot.doctor else None
        ),
        "slot_id":    appointment.slot_id,
        "start_time": slot.start_time.isoformat() if slot else None,
        "end_time":   slot.end_time.isoformat()   if slot else None,
        "date": (
            slot.start_time.strftime("%Y-%m-%d")  if slot else None
        ),
        "time": (
            slot.start_time.strftime("%I:%M %p")  if slot else None
        ),
        "status":     appointment.status.value,
        "reason":     appointment.reason,
        "notes":      appointment.notes,
        "created_at": (
            appointment.created_at.isoformat() if appointment.created_at else None
        ),
        "updated_at": (
            appointment.updated_at.isoformat() if appointment.updated_at else None
        ),
    }