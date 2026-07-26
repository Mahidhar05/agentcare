# tools/department_tools.py

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from database.models import Department, Doctor

logger = logging.getLogger(__name__)


def list_all_departments(db: Session) -> List[Dict[str, Any]]:
    """Returns all active departments."""
    try:
        departments = db.query(Department).filter(
            Department.active == True
        ).all()

        return [
            {
                "id":          d.id,
                "name":        d.name,
                "description": d.description,
            }
            for d in departments
        ]

    except Exception as e:
        logger.error(f"[DEPT] Error listing departments: {e}")
        return []


def get_department_by_name(
    db: Session,
    name: str
) -> Optional[Dict[str, Any]]:
    """
    Finds a department by exact or partial name match.
    Case-insensitive.
    """
    try:
        # Exact match first
        dept = db.query(Department).filter(
            Department.active == True,
            Department.name.ilike(name)
        ).first()

        if dept:
            return {
                "id":          dept.id,
                "name":        dept.name,
                "description": dept.description
            }

        # Partial match fallback
        dept = db.query(Department).filter(
            Department.active == True,
            Department.name.ilike(f"%{name}%")
        ).first()

        if dept:
            return {
                "id":          dept.id,
                "name":        dept.name,
                "description": dept.description
            }

        return None

    except Exception as e:
        logger.error(f"[DEPT] Error searching department '{name}': {e}")
        return None


def get_department_by_id(
    db: Session,
    dept_id: int
) -> Optional[Dict[str, Any]]:
    """Fetches a department by its primary key."""
    try:
        dept = db.query(Department).filter(
            Department.id == dept_id,
            Department.active == True
        ).first()

        if not dept:
            return None

        return {
            "id":          dept.id,
            "name":        dept.name,
            "description": dept.description
        }

    except Exception as e:
        logger.error(f"[DEPT] Error fetching dept_id={dept_id}: {e}")
        return None


def get_doctors_by_department(
    db: Session,
    department_id: int
) -> List[Dict[str, Any]]:
    """Returns all active doctors in a given department."""
    try:
        doctors = db.query(Doctor).filter(
            Doctor.department_id == department_id,
            Doctor.active == True
        ).all()

        return [
            {
                "id":             d.id,
                "name":           d.name,
                "specialization": d.specialization,
                "qualification":  d.qualification,
                "department_id":  d.department_id,
            }
            for d in doctors
        ]

    except Exception as e:
        logger.error(
            f"[DEPT] Error fetching doctors for dept {department_id}: {e}"
        )
        return []


def get_department_summary(db: Session) -> List[Dict[str, Any]]:
    """Returns departments with doctor count — for staff dashboard."""
    try:
        departments = db.query(Department).filter(
            Department.active == True
        ).all()

        result = []
        for d in departments:
            doctor_count = db.query(Doctor).filter(
                Doctor.department_id == d.id,
                Doctor.active == True
            ).count()

            result.append({
                "id":           d.id,
                "name":         d.name,
                "description":  d.description,
                "doctor_count": doctor_count,
            })

        return result

    except Exception as e:
        logger.error(f"[DEPT] Error building department summary: {e}")
        return []
    
def find_doctor_by_name(
    db: Session,
    name: str
) -> Optional[Dict[str, Any]]:
    """
    Finds a doctor by partial name match (case-insensitive).
    Handles: 'Aisha Sharma', 'Dr. Aisha', 'Sharma', etc.
    """
    try:
        search_term = name.strip().lower()
        # Remove common prefixes
        for prefix in ["dr.", "dr ", "doctor ", "doc ", "doc."]:
            if search_term.startswith(prefix):
                search_term = search_term[len(prefix):].strip()

        # Try full name match first
        doctor = db.query(Doctor).filter(
            Doctor.active == True,
            Doctor.name.ilike(f"%{search_term}%")
        ).first()

        if not doctor:
            # Try each word of the search term
            for word in search_term.split():
                if len(word) < 3:
                    continue
                doctor = db.query(Doctor).filter(
                    Doctor.active == True,
                    Doctor.name.ilike(f"%{word}%")
                ).first()
                if doctor:
                    break

        if not doctor:
            return None

        # Get department
        dept = db.query(Department).filter(
            Department.id == doctor.department_id
        ).first()

        return {
            "id":              doctor.id,
            "name":            doctor.name,
            "specialization":  doctor.specialization,
            "qualification":   doctor.qualification,
            "department_id":   doctor.department_id,
            "department_name": dept.name if dept else "Unknown",
        }

    except Exception as e:
        logger.error(f"[DEPT] Error finding doctor by name '{name}': {e}")
        return None    