# tools/document_tools.py

import os
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from database.models import PatientDocument, DocumentType
from tools.audit_tools import log_audit_event
from config import settings

logger = logging.getLogger(__name__)

# ── Keyword map for document classification ───────────────────
DOCUMENT_KEYWORDS = {
    DocumentType.ecg: [
        "ecg", "electrocardiogram", "ekg", "cardiac rhythm", "heart rate"
    ],
    DocumentType.blood_report: [
        "blood", "cbc", "hemoglobin", "platelet", "rbc", "wbc",
        "glucose", "hba1c", "cholesterol", "lipid", "serum"
    ],
    DocumentType.xray: [
        "xray", "x-ray", "radiograph", "chest x", "bone scan"
    ],
    DocumentType.mri: [
        "mri", "magnetic resonance", "brain mri", "spine mri"
    ],
    DocumentType.ct_scan: [
        "ct scan", "computed tomography", "ct chest", "ct abdomen"
    ],
    DocumentType.prescription: [
        "prescription", "rx", "medicine", "tablet", "capsule", "prescribed"
    ],
    DocumentType.discharge_summary: [
        "discharge", "hospital summary", "discharge note", "inpatient"
    ],
    DocumentType.insurance: [
        "insurance", "policy", "coverage", "claim", "tpa", "mediclaim"
    ],
    DocumentType.identity: [
        "aadhar", "passport", "pan card", "driving licence",
        "voter id", "identity proof"
    ],
}


def classify_document_type(
    filename: str,
    description: str = ""
) -> DocumentType:
    """
    Classifies a document type based on filename and description keywords.
    Falls back to DocumentType.other if no match found.
    """
    combined = (filename + " " + (description or "")).lower()

    for doc_type, keywords in DOCUMENT_KEYWORDS.items():
        for kw in keywords:
            if kw in combined:
                logger.info(
                    f"[DOC] Classified '{filename}' as "
                    f"'{doc_type.value}' (matched: '{kw}')"
                )
                return doc_type

    logger.info(
        f"[DOC] Could not classify '{filename}', defaulting to 'other'"
    )
    return DocumentType.other


def compute_file_checksum(file_path: str) -> str:
    """
    Computes SHA256 checksum of a file.
    Used for duplicate detection.
    """
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f"[DOC] Checksum failed for {file_path}: {e}")
        return ""


def check_duplicate_document(
    db: Session,
    patient_id: int,
    checksum: str,
) -> Optional[Dict[str, Any]]:
    """
    Checks if a document with the same SHA256 checksum
    already exists for this patient.
    Returns existing doc dict if duplicate, else None.
    """
    try:
        existing = db.query(PatientDocument).filter(
            PatientDocument.patient_id == patient_id,
            PatientDocument.checksum == checksum,
        ).first()

        if existing:
            logger.warning(
                f"[DOC] Duplicate detected for patient {patient_id}: "
                f"checksum={checksum[:16]}..."
            )
            return {
                "id":                existing.id,
                "document_type":     existing.document_type.value,
                "original_filename": existing.original_filename,
                "created_at": (
                    existing.created_at.isoformat()
                    if existing.created_at else None
                ),
            }

        return None

    except Exception as e:
        logger.error(f"[DOC] Duplicate check failed: {e}")
        return None


def save_document_file(
    file_content: bytes,
    original_filename: str,
    patient_id: int,
) -> Tuple[str, float]:
    """
    Saves uploaded file bytes to the uploads directory.
    Creates a patient-specific subfolder.
    Returns (saved_file_path, file_size_kb).
    """
    try:
        patient_folder = os.path.join(
            settings.UPLOAD_DIR, f"patient_{patient_id}"
        )
        os.makedirs(patient_folder, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(
            c if c.isalnum() or c in (".", "-", "_") else "_"
            for c in original_filename
        )
        filename  = f"{timestamp}_{safe_name}"
        file_path = os.path.join(patient_folder, filename)

        with open(file_path, "wb") as f:
            f.write(file_content)

        file_size_kb = len(file_content) / 1024
        logger.info(f"[DOC] Saved: {file_path} ({file_size_kb:.1f} KB)")

        return file_path, file_size_kb

    except Exception as e:
        logger.error(f"[DOC] File save failed: {e}")
        raise


def store_document_metadata(
    db: Session,
    patient_id: int,
    file_path: str,
    original_filename: str,
    file_size_kb: float,
    checksum: str,
    document_type: DocumentType,
    description: Optional[str] = None,
    document_date: Optional[str] = None,
    actor_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Saves document metadata to DB after file is stored.
    Marks as duplicate if checksum already exists.
    """
    try:
        is_duplicate = (
            check_duplicate_document(db, patient_id, checksum) is not None
        )

        doc = PatientDocument(
            patient_id=patient_id,
            document_type=document_type,
            original_filename=original_filename,
            file_path=file_path,
            file_size_kb=file_size_kb,
            checksum=checksum,
            description=description,
            document_date=(
                document_date or datetime.utcnow().strftime("%Y-%m-%d")
            ),
            is_duplicate=is_duplicate,
            created_at=datetime.utcnow(),
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        log_audit_event(
            db=db,
            action="document_uploaded",
            actor_id=actor_id,
            entity_type="PatientDocument",
            entity_id=doc.id,
            metadata={
                "patient_id":    patient_id,
                "filename":      original_filename,
                "document_type": document_type.value,
                "is_duplicate":  is_duplicate,
                "size_kb":       round(file_size_kb, 2),
            },
        )

        logger.info(
            f"[DOC] Stored doc #{doc.id} for patient {patient_id}: "
            f"{document_type.value} "
            f"({'DUPLICATE' if is_duplicate else 'new'})"
        )

                # ── Send document receipt email to patient ─────────
        try:
            from services.email_service import email_service
            from database.models import User, PatientProfile
            
            patient = db.query(PatientProfile).filter(
                PatientProfile.id == patient_id
            ).first()
            if patient:
                patient_user = db.query(User).filter(
                    User.id == patient.user_id
                ).first()
                if patient_user:
                    email_service.send_document_upload_receipt(
                        patient_email=patient_user.email,
                        patient_name=patient_user.name,
                        document_type=document_type.value,
                        filename=original_filename,
                        is_duplicate=is_duplicate,
                    )
        except Exception as email_err:
            logger.error(f"[DOC] Email failed: {email_err}")

        return {
            "document_id":      doc.id,
            "patient_id":       patient_id,
            "document_type":    document_type.value,
            "original_filename": original_filename,
            "file_path":        file_path,
            "file_size_kb":     round(file_size_kb, 2),
            "checksum":         checksum,
            "description":      description,
            "document_date":    doc.document_date,
            "is_duplicate":     is_duplicate,
            "created_at":       doc.created_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"[DOC] Metadata storage failed: {e}")
        db.rollback()
        raise


def get_patient_documents(
    db: Session,
    patient_id: int,
    doc_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Returns all documents for a patient."""
    try:
        query = db.query(PatientDocument).filter(
            PatientDocument.patient_id == patient_id
        )

        if doc_type:
            try:
                type_enum = DocumentType(doc_type)
                query = query.filter(
                    PatientDocument.document_type == type_enum
                )
            except ValueError:
                pass

        docs = query.order_by(PatientDocument.created_at.desc()).all()

        return [
            {
                "document_id":      d.id,
                "patient_id":       d.patient_id,
                "document_type":    d.document_type.value,
                "original_filename": d.original_filename,
                "file_size_kb":     d.file_size_kb,
                "document_date":    d.document_date,
                "description":      d.description,
                "is_duplicate":     d.is_duplicate,
                "created_at": (
                    d.created_at.isoformat() if d.created_at else None
                ),
            }
            for d in docs
        ]

    except Exception as e:
        logger.error(
            f"[DOC] Error fetching documents for patient {patient_id}: {e}"
        )
        return []


def check_missing_documents(
    db: Session,
    patient_id: int,
    department_name: str,
) -> List[str]:
    """
    Checks what standard documents are expected but missing
    for a given department visit.
    Returns list of missing document type strings.
    """
    DEPT_REQUIRED_DOCS = {
        "Cardiology":       ["ecg", "blood_report"],
        "Neurology":        ["mri", "blood_report"],
        "Orthopedics":      ["xray"],
        "Radiology":        [],
        "General Medicine": ["blood_report"],
        "Dermatology":      [],
        "Ophthalmology":    [],
        "Pediatrics":       ["blood_report"],
        "Gynecology":       ["blood_report"],
        "Gastroenterology": ["blood_report"],
    }

    try:
        required = DEPT_REQUIRED_DOCS.get(department_name, [])
        if not required:
            return []

        existing_docs = db.query(PatientDocument.document_type).filter(
            PatientDocument.patient_id == patient_id
        ).all()

        existing_types = {d[0].value for d in existing_docs}
        missing = [r for r in required if r not in existing_types]

        if missing:
            logger.info(
                f"[DOC] Patient {patient_id} missing docs "
                f"for {department_name}: {missing}"
            )

        return missing

    except Exception as e:
        logger.error(f"[DOC] Missing document check failed: {e}")
        return []