# api/staff_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database.connection import get_db
from database.models import User, PatientProfile, Appointment
from auth.dependencies import require_staff
from tools.department_tools import (
    list_all_departments,
    get_department_summary,
    get_doctors_by_department,
)
from tools.appointment_tools import get_available_slots
from tools.audit_tools import get_full_audit_log
from tools.patient_tools import get_patient_profile
import logging

router = APIRouter(prefix="/api/staff", tags=["Staff"])
logger = logging.getLogger(__name__)


@router.get("/dashboard")
def get_staff_dashboard(
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Returns summary stats for staff dashboard.
    Staff/Admin only.
    """
    from database.models import (
        WorkflowRun, Escalation, EscalationStatus,
        WorkflowStatus, AppointmentStatus
    )

    total_patients   = db.query(PatientProfile).count()
    total_workflows  = db.query(WorkflowRun).count()
    open_escalations = db.query(Escalation).filter(
        Escalation.status == EscalationStatus.open
    ).count()
    total_appointments = db.query(Appointment).count()
    active_appointments = db.query(Appointment).filter(
        Appointment.status.in_([
            AppointmentStatus.confirmed,
            AppointmentStatus.pending,
        ])
    ).count()

    return {
        "stats": {
            "total_patients":      total_patients,
            "total_workflows":     total_workflows,
            "open_escalations":    open_escalations,
            "total_appointments":  total_appointments,
            "active_appointments": active_appointments,
        },
        "logged_in_as": {
            "name":  current_user.name,
            "email": current_user.email,
            "role":  current_user.role.value,
        },
    }


@router.get("/departments")
def list_departments(
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns all departments with doctor counts."""
    summary = get_department_summary(db)
    return {"departments": summary, "total": len(summary)}


@router.get("/departments/{dept_id}/doctors")
def get_department_doctors(
    dept_id: int,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns doctors in a specific department."""
    doctors = get_doctors_by_department(db, dept_id)
    return {"doctors": doctors, "total": len(doctors)}


@router.get("/departments/{dept_id}/slots")
def get_department_slots(
    dept_id: int,
    days_ahead: int = 7,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns available slots for a department."""
    slots = get_available_slots(
        db=db,
        department_id=dept_id,
        days_ahead=days_ahead,
    )
    return {"slots": slots, "total": len(slots)}


@router.get("/patients")
def list_all_patients(
    limit: int = 50,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns list of all patients. Staff/Admin only."""
    patients = db.query(PatientProfile).limit(limit).all()

    result = []
    for p in patients:
        profile = get_patient_profile(db, p.user_id)
        if profile:
            result.append(profile)

    return {"patients": result, "total": len(result)}


@router.get("/patients/{user_id}")
def get_patient_detail(
    user_id: int,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns detailed patient info. Staff/Admin only."""
    profile = get_patient_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return profile


@router.get("/workflows")
def list_all_workflows(
    limit: int = 50,
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns all workflow runs. Staff/Admin only."""
    from database.models import WorkflowRun, WorkflowStatus

    query = db.query(WorkflowRun)

    if status_filter:
        try:
            status_enum = WorkflowStatus(status_filter)
            query = query.filter(WorkflowRun.status == status_enum)
        except ValueError:
            pass

    workflows = query.order_by(
        WorkflowRun.created_at.desc()
    ).limit(limit).all()

    return {
        "workflows": [
            {
                "workflow_id":  w.id,
                "patient_id":   w.patient_id,
                "current_step": w.current_step,
                "status":       w.status.value,
                "request_text": w.request_text,
                "created_at":   w.created_at.isoformat() if w.created_at else None,
            }
            for w in workflows
        ],
        "total": len(workflows),
    }


@router.get("/audit-log")
def get_audit_log(
    limit: int = 100,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns the full audit log. Staff/Admin only."""
    events = get_full_audit_log(db, limit=limit)
    return {"events": events, "total": len(events)}


# ═══════════════════════════════════════════════════════════════
# NEW ENDPOINTS: All Appointments + Slot Statistics
# ═══════════════════════════════════════════════════════════════

@router.get("/appointments")
def list_all_appointments(
    status_filter: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns all appointments across all patients. Staff/Admin only."""
    from database.models import (
        Appointment, AppointmentSlot,
        AppointmentStatus, Doctor, PatientProfile, User as UserModel
    )

    query = db.query(Appointment)

    if status_filter:
        try:
            status_enum = AppointmentStatus(status_filter)
            query = query.filter(Appointment.status == status_enum)
        except ValueError:
            pass

    appointments = query.order_by(
        Appointment.created_at.desc()
    ).limit(limit).all()

    result = []
    for a in appointments:
        # Get slot
        slot = db.query(AppointmentSlot).filter(
            AppointmentSlot.id == a.slot_id
        ).first()

        # Get doctor
        doctor = db.query(Doctor).filter(
            Doctor.id == a.doctor_id
        ).first()

        # Get patient
        patient_profile = db.query(PatientProfile).filter(
            PatientProfile.id == a.patient_id
        ).first()
        patient_user = None
        if patient_profile:
            patient_user = db.query(UserModel).filter(
                UserModel.id == patient_profile.user_id
            ).first()

        result.append({
            "appointment_id":  a.id,
            "patient_id":      a.patient_id,
            "patient_name":    patient_user.name if patient_user else "Unknown",
            "patient_email":   patient_user.email if patient_user else "Unknown",
            "doctor_id":       a.doctor_id,
            "doctor_name":     doctor.name if doctor else "Unknown",
            "specialization":  doctor.specialization if doctor else None,
            "slot_id":         a.slot_id,
            "date":            slot.start_time.strftime("%Y-%m-%d") if slot else None,
            "time":            slot.start_time.strftime("%I:%M %p") if slot else None,
            "start_time":      slot.start_time.isoformat() if slot else None,
            "status":          a.status.value,
            "reason":          a.reason,
            "created_at":      a.created_at.isoformat() if a.created_at else None,
        })

    return {
        "appointments": result,
        "total":        len(result),
    }


@router.get("/slots/stats")
def get_slots_stats(
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns booking statistics across all doctors and departments."""
    from database.models import AppointmentSlot, SlotStatus, Doctor, Department

    total     = db.query(AppointmentSlot).count()
    available = db.query(AppointmentSlot).filter(
        AppointmentSlot.status == SlotStatus.available
    ).count()
    booked    = db.query(AppointmentSlot).filter(
        AppointmentSlot.status == SlotStatus.booked
    ).count()

    # Per department stats
    dept_stats = []
    departments = db.query(Department).filter(Department.active == True).all()
    for dept in departments:
        doctor_ids = [
            d.id for d in db.query(Doctor).filter(
                Doctor.department_id == dept.id
            ).all()
        ]
        if not doctor_ids:
            continue

        dept_total = db.query(AppointmentSlot).filter(
            AppointmentSlot.doctor_id.in_(doctor_ids)
        ).count()
        dept_booked = db.query(AppointmentSlot).filter(
            AppointmentSlot.doctor_id.in_(doctor_ids),
            AppointmentSlot.status == SlotStatus.booked,
        ).count()
        dept_available = dept_total - dept_booked

        dept_stats.append({
            "department":  dept.name,
            "total":       dept_total,
            "booked":      dept_booked,
            "available":   dept_available,
            "utilization": round(
                (dept_booked / dept_total * 100) if dept_total > 0 else 0, 1
            ),
        })

    return {
        "overall": {
            "total":       total,
            "available":   available,
            "booked":      booked,
            "utilization": round(
                (booked / total * 100) if total > 0 else 0, 1
            ),
        },
        "by_department": dept_stats,
    }
@router.get("/notifications")
def list_notifications(
    limit: int = 50,
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns all notifications sent by the system. Staff/Admin only."""
    from database.models import Notification, NotificationStatus

    query = db.query(Notification)

    if status_filter:
        try:
            status_enum = NotificationStatus(status_filter)
            query = query.filter(Notification.status == status_enum)
        except ValueError:
            pass

    notifications = query.order_by(
        Notification.created_at.desc()
    ).limit(limit).all()

    return {
        "notifications": [
            {
                "id":                n.id,
                "recipient_email":   n.recipient_email,
                "recipient_name":    n.recipient_name,
                "subject":           n.subject,
                "notification_type": n.notification_type.value,
                "status":            n.status.value,
                "escalation_id":     n.escalation_id,
                "workflow_run_id":   n.workflow_run_id,
                "created_at":        n.created_at.isoformat() if n.created_at else None,
                "sent_at":           n.sent_at.isoformat() if n.sent_at else None,
                "error_message":     n.error_message,
            }
            for n in notifications
        ],
        "total": len(notifications),
    }


@router.get("/notifications/{notification_id}")
def get_notification_detail(
    notification_id: int,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns full notification with HTML body for preview."""
    from database.models import Notification

    n = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()

    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {
        "id":                n.id,
        "recipient_email":   n.recipient_email,
        "recipient_name":    n.recipient_name,
        "subject":           n.subject,
        "body_html":         n.body_html,
        "body_plain":        n.body_plain,
        "notification_type": n.notification_type.value,
        "status":            n.status.value,
        "escalation_id":     n.escalation_id,
        "workflow_run_id":   n.workflow_run_id,
        "created_at":        n.created_at.isoformat() if n.created_at else None,
        "sent_at":           n.sent_at.isoformat() if n.sent_at else None,
        "error_message":     n.error_message,
    }

# ═══════════════════════════════════════════════════════════════
# ANALYTICS ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics/overview")
def get_analytics_overview(
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns high-level analytics metrics."""
    from database.models import (
        Appointment, AppointmentSlot, AppointmentStatus,
        Doctor, Department, PatientProfile, WorkflowRun, Escalation
    )
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    
    # Basic counts
    total_patients = db.query(PatientProfile).count()
    total_doctors = db.query(Doctor).filter(Doctor.active == True).count()
    total_departments = db.query(Department).filter(Department.active == True).count()
    total_appointments = db.query(Appointment).count()
    
    # Recent activity
    appts_7d = db.query(Appointment).filter(
        Appointment.created_at >= seven_days_ago
    ).count()
    appts_30d = db.query(Appointment).filter(
        Appointment.created_at >= thirty_days_ago
    ).count()
    
    # Workflow stats
    total_workflows = db.query(WorkflowRun).count()
    workflows_7d = db.query(WorkflowRun).filter(
        WorkflowRun.created_at >= seven_days_ago
    ).count()
    
    # Escalations
    total_escalations = db.query(Escalation).count()
    open_escalations = db.query(Escalation).filter(
        Escalation.status == "open"
    ).count()
    
    # Average appointments per day (last 7 days)
    avg_appointments_per_day = round(appts_7d / 7, 1) if appts_7d else 0
    
    return {
        "totals": {
            "patients": total_patients,
            "doctors": total_doctors,
            "departments": total_departments,
            "appointments": total_appointments,
            "workflows": total_workflows,
            "escalations": total_escalations,
        },
        "recent": {
            "appointments_last_7_days": appts_7d,
            "appointments_last_30_days": appts_30d,
            "workflows_last_7_days": workflows_7d,
            "open_escalations": open_escalations,
        },
        "averages": {
            "appointments_per_day": avg_appointments_per_day,
        },
    }


@router.get("/analytics/appointment-trends")
def get_appointment_trends(
    days: int = 7,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns appointment count per day for the last N days."""
    from database.models import Appointment
    from datetime import datetime, timedelta
    from sqlalchemy import func, cast, Date
    
    end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=days)
    
    # Query appointments grouped by day
    results = db.query(
        cast(Appointment.created_at, Date).label("date"),
        func.count(Appointment.id).label("count")
    ).filter(
        Appointment.created_at >= start_date
    ).group_by(
        cast(Appointment.created_at, Date)
    ).order_by(
        cast(Appointment.created_at, Date)
    ).all()
    
    # Build a complete series (fill missing days with 0)
    date_map = {r.date.strftime("%Y-%m-%d"): r.count for r in results}
    
    trend = []
    for i in range(days + 1):
        d = (start_date + timedelta(days=i)).date()
        date_str = d.strftime("%Y-%m-%d")
        trend.append({
            "date": date_str,
            "day_name": d.strftime("%a"),
            "count": date_map.get(date_str, 0),
        })
    
    return {
        "trend": trend,
        "total": sum(t["count"] for t in trend),
        "peak_day": max(trend, key=lambda x: x["count"])["date"] if trend else None,
    }


@router.get("/analytics/department-utilization")
def get_department_utilization(
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns appointment count per department."""
    from database.models import (
        Appointment, Doctor, Department, AppointmentStatus
    )
    from sqlalchemy import func
    
    results = db.query(
        Department.name.label("department"),
        func.count(Appointment.id).label("total"),
    ).join(
        Doctor, Doctor.department_id == Department.id
    ).join(
        Appointment, Appointment.doctor_id == Doctor.id
    ).group_by(
        Department.name
    ).order_by(
        func.count(Appointment.id).desc()
    ).all()
    
    departments = [
        {"department": r.department, "appointments": r.total}
        for r in results
    ]
    
    # Also get status breakdown per department
    status_breakdown = {}
    for dept in departments:
        for status_val in ["confirmed", "pending", "completed", "cancelled", "rescheduled"]:
            count = db.query(Appointment).join(Doctor).join(Department).filter(
                Department.name == dept["department"],
                Appointment.status == status_val,
            ).count()
            status_breakdown.setdefault(dept["department"], {})[status_val] = count
    
    return {
        "departments": departments,
        "status_breakdown": status_breakdown,
        "total_departments": len(departments),
    }


@router.get("/analytics/doctor-workload")
def get_doctor_workload(
    limit: int = 10,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns top N doctors by appointment count."""
    from database.models import Appointment, Doctor, Department
    from sqlalchemy import func
    
    results = db.query(
        Doctor.name.label("doctor"),
        Doctor.specialization.label("specialization"),
        Department.name.label("department"),
        func.count(Appointment.id).label("total"),
    ).join(
        Department, Department.id == Doctor.department_id
    ).outerjoin(
        Appointment, Appointment.doctor_id == Doctor.id
    ).group_by(
        Doctor.name, Doctor.specialization, Department.name
    ).order_by(
        func.count(Appointment.id).desc()
    ).limit(limit).all()
    
    doctors = [
        {
            "doctor": r.doctor,
            "specialization": r.specialization,
            "department": r.department,
            "appointments": r.total,
        }
        for r in results
    ]
    
    return {
        "doctors": doctors,
        "total_shown": len(doctors),
    }


@router.get("/analytics/appointment-status")
def get_appointment_status_breakdown(
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns count of appointments by status."""
    from database.models import Appointment, AppointmentStatus
    from sqlalchemy import func
    
    results = db.query(
        Appointment.status,
        func.count(Appointment.id).label("count"),
    ).group_by(Appointment.status).all()
    
    breakdown = [
        {"status": r.status.value, "count": r.count}
        for r in results
    ]
    
    return {
        "breakdown": breakdown,
        "total": sum(b["count"] for b in breakdown),
    }


@router.get("/analytics/peak-hours")
def get_peak_hours(
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns appointment count per hour of the day."""
    from database.models import Appointment, AppointmentSlot
    from sqlalchemy import func
    
    # Get all appointments with their slot times
    results = db.query(
        func.strftime('%H', AppointmentSlot.start_time).label("hour"),
        func.count(Appointment.id).label("count"),
    ).join(
        AppointmentSlot, AppointmentSlot.id == Appointment.slot_id
    ).group_by(
        func.strftime('%H', AppointmentSlot.start_time)
    ).order_by(
        func.strftime('%H', AppointmentSlot.start_time)
    ).all()
    
    # Convert to human-readable format
    hours_data = []
    hour_map = {r.hour: r.count for r in results if r.hour}
    
    for hour_num in range(9, 20):  # 9 AM to 7 PM
        hour_str = f"{hour_num:02d}"
        display = f"{hour_num % 12 or 12} {'AM' if hour_num < 12 else 'PM'}"
        hours_data.append({
            "hour": display,
            "hour_24": hour_num,
            "count": hour_map.get(hour_str, 0),
        })
    
    peak = max(hours_data, key=lambda x: x["count"]) if hours_data else None
    
    return {
        "hours": hours_data,
        "peak_hour": peak["hour"] if peak else None,
        "peak_count": peak["count"] if peak else 0,
    }


@router.get("/analytics/patient-growth")
def get_patient_growth(
    days: int = 30,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns patient signup count per day."""
    from database.models import User, UserRole
    from datetime import datetime, timedelta
    from sqlalchemy import func, cast, Date
    
    end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=days)
    
    results = db.query(
        cast(User.created_at, Date).label("date"),
        func.count(User.id).label("count"),
    ).filter(
        User.role == UserRole.patient,
        User.created_at >= start_date,
    ).group_by(
        cast(User.created_at, Date)
    ).order_by(
        cast(User.created_at, Date)
    ).all()
    
    date_map = {r.date.strftime("%Y-%m-%d"): r.count for r in results}
    
    growth = []
    cumulative = db.query(User).filter(
        User.role == UserRole.patient,
        User.created_at < start_date,
    ).count()
    
    for i in range(days + 1):
        d = (start_date + timedelta(days=i)).date()
        date_str = d.strftime("%Y-%m-%d")
        new_signups = date_map.get(date_str, 0)
        cumulative += new_signups
        growth.append({
            "date": date_str,
            "new_signups": new_signups,
            "cumulative": cumulative,
        })
    
    return {
        "growth": growth,
        "total_new_last_period": sum(g["new_signups"] for g in growth),
        "current_total": cumulative,
    }    


# ═══════════════════════════════════════════════════════════════
# SEARCH & FILTER ENDPOINTS (Feature #4)
# ═══════════════════════════════════════════════════════════════

@router.get("/search/patients")
def search_patients(
    q: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    gender: Optional[str] = None,
    blood_group: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Search and filter patients.
    - q: search in name, email, phone
    - min_age/max_age: age range filter
    - gender: filter by gender
    - blood_group: filter by blood group
    """
    from database.models import User as UserModel, UserRole
    
    query = db.query(PatientProfile).join(
        UserModel, UserModel.id == PatientProfile.user_id
    )
    
    # Text search
    if q:
        search_pattern = f"%{q.lower()}%"
        query = query.filter(
            (UserModel.name.ilike(search_pattern)) |
            (UserModel.email.ilike(search_pattern)) |
            (PatientProfile.phone.ilike(search_pattern))
        )
    
    # Age range
    if min_age is not None:
        query = query.filter(PatientProfile.age >= min_age)
    if max_age is not None:
        query = query.filter(PatientProfile.age <= max_age)
    
    # Gender filter
    if gender and gender != "All":
        query = query.filter(PatientProfile.gender == gender)
    
    # Blood group
    if blood_group and blood_group != "All":
        query = query.filter(PatientProfile.blood_group == blood_group)
    
    patients = query.limit(limit).all()
    
    result = []
    for p in patients:
        user = db.query(UserModel).filter(UserModel.id == p.user_id).first()
        if user:
            result.append({
                "profile_id": p.id,
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": p.phone,
                "age": p.age,
                "gender": p.gender,
                "blood_group": p.blood_group,
                "address": p.address,
                "emergency_contact": p.emergency_contact,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })
    
    return {
        "patients": result,
        "total": len(result),
        "filters_applied": {
            "search": q,
            "min_age": min_age,
            "max_age": max_age,
            "gender": gender,
            "blood_group": blood_group,
        },
    }


@router.get("/search/appointments")
def search_appointments(
    q: Optional[str] = None,
    department_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Advanced appointment search with multiple filters.
    """
    from database.models import (
        Appointment, AppointmentSlot, AppointmentStatus,
        Doctor, PatientProfile, User as UserModel, Department
    )
    from datetime import datetime
    
    query = db.query(Appointment).join(
        AppointmentSlot, AppointmentSlot.id == Appointment.slot_id
    ).join(
        Doctor, Doctor.id == Appointment.doctor_id
    ).join(
        PatientProfile, PatientProfile.id == Appointment.patient_id
    ).join(
        UserModel, UserModel.id == PatientProfile.user_id
    )
    
    # Text search in patient name / email
    if q:
        search_pattern = f"%{q.lower()}%"
        query = query.filter(
            (UserModel.name.ilike(search_pattern)) |
            (UserModel.email.ilike(search_pattern)) |
            (Doctor.name.ilike(search_pattern))
        )
    
    # Filters
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if status_filter and status_filter != "All":
        try:
            status_enum = AppointmentStatus(status_filter)
            query = query.filter(Appointment.status == status_enum)
        except ValueError:
            pass
    
    # Date range
    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date)
            query = query.filter(AppointmentSlot.start_time >= from_dt)
        except (ValueError, TypeError):
            pass
    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date)
            query = query.filter(AppointmentSlot.start_time <= to_dt)
        except (ValueError, TypeError):
            pass
    
    appointments = query.order_by(
        AppointmentSlot.start_time.desc()
    ).limit(limit).all()
    
    result = []
    for a in appointments:
        slot = db.query(AppointmentSlot).filter(
            AppointmentSlot.id == a.slot_id
        ).first()
        doctor = db.query(Doctor).filter(Doctor.id == a.doctor_id).first()
        dept = db.query(Department).filter(
            Department.id == doctor.department_id
        ).first() if doctor else None
        patient = db.query(PatientProfile).filter(
            PatientProfile.id == a.patient_id
        ).first()
        p_user = db.query(UserModel).filter(
            UserModel.id == patient.user_id
        ).first() if patient else None
        
        result.append({
            "appointment_id": a.id,
            "patient_name": p_user.name if p_user else "Unknown",
            "patient_email": p_user.email if p_user else None,
            "doctor_name": doctor.name if doctor else "Unknown",
            "department": dept.name if dept else "Unknown",
            "date": slot.start_time.strftime("%Y-%m-%d") if slot else None,
            "time": slot.start_time.strftime("%I:%M %p") if slot else None,
            "status": a.status.value,
            "reason": a.reason,
        })
    
    return {
        "appointments": result,
        "total": len(result),
        "filters": {
            "search": q,
            "department_id": department_id,
            "doctor_id": doctor_id,
            "status": status_filter,
            "from_date": from_date,
            "to_date": to_date,
        },
    }


@router.get("/search/doctors")
def search_doctors(
    q: Optional[str] = None,
    department_id: Optional[int] = None,
    specialization: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Search doctors by name, department, or specialization.
    """
    from database.models import Doctor, Department
    
    query = db.query(Doctor).join(
        Department, Department.id == Doctor.department_id
    ).filter(Doctor.active == True)
    
    if q:
        search_pattern = f"%{q.lower()}%"
        query = query.filter(
            (Doctor.name.ilike(search_pattern)) |
            (Doctor.specialization.ilike(search_pattern)) |
            (Doctor.qualification.ilike(search_pattern))
        )
    
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    
    if specialization and specialization != "All":
        query = query.filter(
            Doctor.specialization.ilike(f"%{specialization}%")
        )
    
    doctors = query.limit(limit).all()
    
    result = []
    for d in doctors:
        dept = db.query(Department).filter(
            Department.id == d.department_id
        ).first()
        result.append({
            "id": d.id,
            "name": d.name,
            "specialization": d.specialization,
            "qualification": d.qualification,
            "department": dept.name if dept else "Unknown",
            "department_id": d.department_id,
        })
    
    return {
        "doctors": result,
        "total": len(result),
    }


@router.get("/search/global")
def global_search(
    q: str,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Universal search across patients, doctors, and departments.
    Returns top matches from all categories.
    """
    from database.models import (
        Doctor, Department, PatientProfile,
        User as UserModel, UserRole
    )
    
    if not q or len(q) < 2:
        return {
            "query": q,
            "patients": [],
            "doctors": [],
            "departments": [],
            "total_results": 0,
        }
    
    search_pattern = f"%{q.lower()}%"
    
    # Patient results (top 5)
    patients = db.query(PatientProfile).join(
        UserModel, UserModel.id == PatientProfile.user_id
    ).filter(
        (UserModel.name.ilike(search_pattern)) |
        (UserModel.email.ilike(search_pattern))
    ).limit(5).all()
    
    patient_results = []
    for p in patients:
        u = db.query(UserModel).filter(UserModel.id == p.user_id).first()
        if u:
            patient_results.append({
                "type": "patient",
                "id": p.id,
                "user_id": u.id,
                "name": u.name,
                "email": u.email,
                "phone": p.phone,
            })
    
    # Doctor results (top 5)
    doctors = db.query(Doctor).filter(
        Doctor.active == True,
        (Doctor.name.ilike(search_pattern)) |
        (Doctor.specialization.ilike(search_pattern))
    ).limit(5).all()
    
    doctor_results = []
    for d in doctors:
        dept = db.query(Department).filter(
            Department.id == d.department_id
        ).first()
        doctor_results.append({
            "type": "doctor",
            "id": d.id,
            "name": d.name,
            "specialization": d.specialization,
            "department": dept.name if dept else "Unknown",
        })
    
    # Department results (top 5)
    departments = db.query(Department).filter(
        Department.active == True,
        Department.name.ilike(search_pattern)
    ).limit(5).all()
    
    dept_results = [
        {
            "type": "department",
            "id": d.id,
            "name": d.name,
            "description": d.description,
        }
        for d in departments
    ]
    
    total = len(patient_results) + len(doctor_results) + len(dept_results)
    
    return {
        "query": q,
        "patients": patient_results,
        "doctors": doctor_results,
        "departments": dept_results,
        "total_results": total,
    }    