# api/workflow_routes.py

from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form, status
)
from sqlalchemy.orm import Session
from typing import Optional

from database.connection import get_db
from database.models import User, WorkflowRun
from auth.dependencies import get_current_user, require_patient
from agents.coordinator import coordinator_agent
from tools.audit_tools import log_audit_event
from config import settings
import logging

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])
logger = logging.getLogger(__name__)


@router.post("/submit")
async def submit_request(
    request_text: str = Form(...),
    file: Optional[UploadFile] = File(None),
    file_description: Optional[str] = Form(None),
    chat_history: Optional[str] = Form(None),   # ← NEW
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Main endpoint — patient submits an administrative request.
    Optionally attaches a document.

    The Coordinator Agent handles the full workflow:
    Safety → Routing → Appointment → Document → Follow-up
    """
    # Validate request text
    if not request_text or not request_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request text cannot be empty.",
        )

    # Read file if provided
    file_content = None
    file_name    = None

    if file:
        # Check file size
        file_content = await file.read()
        file_name    = file.filename

        size_mb = len(file_content) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"File size {size_mb:.1f}MB exceeds "
                    f"limit of {settings.MAX_FILE_SIZE_MB}MB."
                ),
            )

        # Check extension
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"File type '.{ext}' not allowed. "
                    f"Allowed: {settings.ALLOWED_EXTENSIONS}"
                ),
            )

    # Run coordinator agent
        # Parse chat history if provided
    parsed_history = []
    if chat_history:
        try:
            import json as json_module
            parsed_history = json_module.loads(chat_history)
            if not isinstance(parsed_history, list):
                parsed_history = []
        except Exception as e:
            logger.warning(f"[WORKFLOW] Could not parse chat_history: {e}")
            parsed_history = []
    
    # Run coordinator agent
    try:
        result = coordinator_agent.run(
            user_id=current_user.id,
            request_text=request_text.strip(),
            file_content=file_content,
            file_name=file_name,
            file_description=file_description,
            patient_email=current_user.email,
            patient_name=current_user.name,
            chat_history=parsed_history,   # ← NEW
        )

        return result

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[WORKFLOW] Coordinator failed for user {current_user.id}:\n{error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow processing failed: {str(e)}",
        )


@router.get("/status/{workflow_id}")
def get_workflow_status(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the current status of a workflow run.
    Patients can only view their own workflows.
    """
    from database.models import UserRole, PatientProfile

    workflow = db.query(WorkflowRun).filter(
        WorkflowRun.id == workflow_id
    ).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow #{workflow_id} not found.",
        )

    # Patients can only see their own workflows
    if current_user.role == UserRole.patient:
        patient = db.query(PatientProfile).filter(
            PatientProfile.user_id == current_user.id
        ).first()

        if not patient or workflow.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own workflows.",
            )

    return {
        "workflow_id":   workflow.id,
        "patient_id":    workflow.patient_id,
        "current_step":  workflow.current_step,
        "status":        workflow.status.value,
        "request_text":  workflow.request_text,
        "result":        workflow.result,
        "created_at":    workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at":    workflow.updated_at.isoformat() if workflow.updated_at else None,
    }


@router.get("/history")
def get_my_workflow_history(
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Returns all workflows for the current patient.
    """
    from database.models import PatientProfile

    patient = db.query(PatientProfile).filter(
        PatientProfile.user_id == current_user.id
    ).first()

    if not patient:
        return {"workflows": [], "total": 0}

    workflows = db.query(WorkflowRun).filter(
        WorkflowRun.patient_id == patient.id
    ).order_by(WorkflowRun.created_at.desc()).limit(20).all()

    return {
        "workflows": [
            {
                "workflow_id":  w.id,
                "current_step": w.current_step,
                "status":       w.status.value,
                "request_text": w.request_text,
                "created_at":   w.created_at.isoformat() if w.created_at else None,
            }
            for w in workflows
        ],
        "total": len(workflows),
    }