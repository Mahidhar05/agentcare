# api/document_routes.py

from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form, status
)
from sqlalchemy.orm import Session
from typing import Optional

from database.connection import get_db
from database.models import User, PatientProfile
from auth.dependencies import get_current_user, require_patient
from agents.document_agent import document_agent
from tools.document_tools import get_patient_documents
from config import settings
import logging
import os
from database.models import PatientDocument

router = APIRouter(prefix="/api/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


def _get_patient_id(db: Session, user_id: int) -> int:
    patient = db.query(PatientProfile).filter(
        PatientProfile.user_id == user_id
    ).first()
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found.",
        )
    return patient.id


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    department_name: Optional[str] = Form(None),
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Uploads a medical document for the current patient.
    Document Agent handles classification, dedup, and storage.
    """
    patient_id = _get_patient_id(db, current_user.id)

    # Validate file
    file_content = await file.read()
    file_name    = file.filename

    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB.",
        )

    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type .{ext} not allowed.",
        )

    # Process through Document Agent
    result = document_agent.process_upload(
        file_content=file_content,
        original_filename=file_name,
        patient_id=patient_id,
        patient_name=current_user.name,
        patient_email=current_user.email,
        department_name=department_name,
        description=description,
        actor_id=current_user.id,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Upload failed."),
        )

    return result


@router.get("/my")
def get_my_documents(
    doc_type: Optional[str] = None,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Returns all documents for the current patient."""
    patient_id = _get_patient_id(db, current_user.id)
    documents  = get_patient_documents(
        db=db,
        patient_id=patient_id,
        doc_type=doc_type,
    )

    return {
        "documents": documents,
        "total":     len(documents),
    }


@router.get("/status")
def get_document_status(
    department_name: Optional[str] = None,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Returns document completeness status for the current patient.
    Includes missing required documents for a department.
    """
    patient_id = _get_patient_id(db, current_user.id)
    status_result = document_agent.get_document_status(
        patient_id=patient_id,
        department_name=department_name,
    )

    return status_result

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Delete a patient's own document."""
    patient_id = _get_patient_id(db, current_user.id)
    
    doc = db.query(PatientDocument).filter_by(
        id=document_id,
        patient_id=patient_id,   # Ensures user owns this document
    ).first()
    
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Document not found or does not belong to you.",
        )
    
    filename = doc.original_filename
    
    # Delete physical file from disk (best effort)
    try:
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
            logger.info(f"Deleted file from disk: {doc.file_path}")
    except Exception as e:
        logger.warning(f"Could not delete file {doc.file_path}: {e}")
    
    # Delete DB record
    db.delete(doc)
    db.commit()
    
    logger.info(f"Patient {patient_id} deleted document: {filename}")
    
    return {
        "success": True,
        "message": f"Document '{filename}' deleted successfully",
        "deleted_id": document_id,
    }