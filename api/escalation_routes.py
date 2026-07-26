# api/escalation_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User
from auth.dependencies import require_staff, require_authenticated
from tools.escalation_tools import (
    get_open_escalations,
    get_all_escalations,
    resolve_escalation,
    get_escalation_by_id,
)
from schemas.pydantic_schemas import EscalationResolveRequest
import logging

router = APIRouter(prefix="/api/escalations", tags=["Escalations"])
logger = logging.getLogger(__name__)


@router.get("/open")
def list_open_escalations(
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Returns all open escalations requiring staff review.
    Staff/Admin only.
    """
    escalations = get_open_escalations(db)

    return {
        "escalations": escalations,
        "total":       len(escalations),
    }


@router.get("/all")
def list_all_escalations_route(
    limit: int = 100,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Returns all escalations (open, reviewed, resolved).
    Staff/Admin only.
    """
    escalations = get_all_escalations(db, limit=limit)

    return {
        "escalations": escalations,
        "total":       len(escalations),
    }


@router.get("/{escalation_id}")
def get_escalation_detail(
    escalation_id: int,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Returns a single escalation by ID. Staff/Admin only."""
    escalation = get_escalation_by_id(db, escalation_id)

    if not escalation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation #{escalation_id} not found.",
        )

    return escalation


@router.post("/{escalation_id}/resolve")
def resolve_escalation_route(
    escalation_id: int,
    request: EscalationResolveRequest,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Staff/Admin resolves an escalation.
    Records who reviewed it and the resolution note.
    """
    try:
        resolved = resolve_escalation(
            db=db,
            escalation_id=escalation_id,
            reviewer_user_id=current_user.id,
            resolution_note=request.resolution_note,
            new_status=request.new_status or "resolved",
        )

        return {
            "success":    True,
            "message":    f"Escalation #{escalation_id} marked as resolved.",
            "escalation": resolved,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"[ESCALATION ROUTE] Resolve failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve escalation.",
        )