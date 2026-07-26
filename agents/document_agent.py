# agents/document_agent.py

import logging
from typing import Dict, Any, Optional, List
from services.llm_service import llm_service
from services.notification_service import notification_service
from tools.document_tools import (
    classify_document_type,
    compute_file_checksum,
    save_document_file,
    store_document_metadata,
    get_patient_documents,
    check_missing_documents,
    check_duplicate_document,
)
from database.connection import get_db_session

logger = logging.getLogger(__name__)

DOCUMENT_SYSTEM_PROMPT = """You are the AgentCare Document Coordination Agent.

Your job is to classify, organize, and validate medical documents
uploaded by patients for administrative purposes.

You receive information about uploaded documents and must:
1. Confirm or improve the document type classification
2. Identify if documents are relevant for the patient's appointment
3. Check if required documents are missing
4. Provide a clear status summary

STRICT RULES:
- You classify documents ADMINISTRATIVELY only
- You NEVER interpret medical results or findings
- You NEVER say what a test result means medically
- You only confirm: "this appears to be an ECG document" not "your ECG shows..."

Respond ONLY in this exact JSON format:
{
  "confirmed_document_type": "ecg/blood_report/xray/mri/ct_scan/prescription/discharge_summary/insurance/identity/other",
  "classification_confidence": 0.0 to 1.0,
  "is_relevant_for_appointment": true or false,
  "relevance_reason": "brief administrative reason",
  "patient_message": "friendly confirmation message (no medical interpretation)",
  "additional_notes": "any administrative notes or null"
}"""


class DocumentAgent:
    """
    Document Coordination Agent.

    Responsibilities:
    - Receive uploaded file content
    - Classify document type using keywords + LLM
    - Compute SHA256 checksum for duplicate detection
    - Store file and metadata in database
    - Check for missing required documents
    - Map documents to patient record
    - Notify patient of upload status
    """

    def __init__(self):
        self.llm = llm_service

    def process_upload(
        self,
        file_content: bytes,
        original_filename: str,
        patient_id: int,
        patient_name: str,
        patient_email: str,
        department_name: Optional[str] = None,
        description: Optional[str] = None,
        actor_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Full document processing pipeline:
        1. Classify document type
        2. Save file to disk
        3. Compute checksum
        4. Check for duplicates
        5. Store metadata in DB
        6. LLM confirms classification
        7. Check missing docs for department
        8. Notify patient

        Args:
            file_content      : Raw bytes of uploaded file
            original_filename : Original filename from upload
            patient_id        : PatientProfile.id
            patient_name      : For notifications
            patient_email     : For notifications
            department_name   : For missing doc check
            description       : Optional description from patient
            actor_id          : For audit

        Returns:
            Full document processing result dict
        """
        db = get_db_session()
        try:
            logger.info(
                f"[DOC AGENT] Processing upload: {original_filename} "
                f"for patient {patient_id}"
            )

            # ── Step 1: Keyword-based classification ───────────
            doc_type = classify_document_type(
                original_filename, description or ""
            )

            # ── Step 2: Save file to disk ──────────────────────
            file_path, file_size_kb = save_document_file(
                file_content=file_content,
                original_filename=original_filename,
                patient_id=patient_id,
            )

            # ── Step 3: Compute checksum ───────────────────────
            checksum = compute_file_checksum(file_path)

            # ── Step 4: Check for duplicate ────────────────────
            duplicate = check_duplicate_document(db, patient_id, checksum)
            is_duplicate = duplicate is not None

            # ── Step 5: Store metadata in DB ───────────────────
            doc_record = store_document_metadata(
                db=db,
                patient_id=patient_id,
                file_path=file_path,
                original_filename=original_filename,
                file_size_kb=file_size_kb,
                checksum=checksum,
                document_type=doc_type,
                description=description,
                actor_id=actor_id,
            )

            # ── Step 6: LLM confirms classification ───────────
            llm_result = self._llm_classify(
                filename=original_filename,
                initial_type=doc_type.value,
                description=description,
                department_name=department_name,
            )

            # ── Step 7: Check missing documents ───────────────
            missing_docs = []
            if department_name:
                missing_docs = check_missing_documents(
                    db=db,
                    patient_id=patient_id,
                    department_name=department_name,
                )

            # ── Step 8: Notify patient ─────────────────────────
            notification_service.send_document_upload_confirmation(
                patient_name=patient_name,
                patient_email=patient_email,
                document_type=doc_type.value,
                filename=original_filename,
                is_duplicate=is_duplicate,
            )

            result = {
                "success":           True,
                "document":          doc_record,
                "is_duplicate":      is_duplicate,
                "duplicate_info":    duplicate,
                "llm_classification": llm_result,
                "missing_documents": missing_docs,
                "message":           llm_result.get(
                    "patient_message",
                    f"Document '{original_filename}' uploaded successfully "
                    f"as {doc_type.value}."
                ),
            }

            if is_duplicate:
                result["message"] = (
                    f"Document '{original_filename}' appears to be a duplicate "
                    f"of an existing document. It has been stored but flagged."
                )

            if missing_docs:
                result["missing_docs_message"] = (
                    f"For your {department_name} appointment, "
                    f"we still need: {', '.join(missing_docs)}. "
                    f"Please upload them before your visit."
                )

            logger.info(
                f"[DOC AGENT] Processed: {original_filename} | "
                f"type={doc_type.value} | "
                f"duplicate={is_duplicate} | "
                f"missing={missing_docs}"
            )

            return result

        except Exception as e:
            logger.error(f"[DOC AGENT] Upload processing failed: {e}")
            return {
                "success":   False,
                "document":  None,
                "message":   f"Document processing failed: {str(e)}",
            }
        finally:
            db.close()

    def get_document_status(
        self,
        patient_id: int,
        department_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns current document status for a patient.
        Includes uploaded docs and missing required docs.
        """
        db = get_db_session()
        try:
            documents = get_patient_documents(db, patient_id)
            missing   = []

            if department_name:
                missing = check_missing_documents(
                    db=db,
                    patient_id=patient_id,
                    department_name=department_name,
                )

            return {
                "total_documents":   len(documents),
                "documents":         documents,
                "missing_documents": missing,
                "is_complete": len(missing) == 0,
            }

        except Exception as e:
            logger.error(
                f"[DOC AGENT] Status check failed for patient {patient_id}: {e}"
            )
            return {
                "total_documents":   0,
                "documents":         [],
                "missing_documents": [],
                "is_complete":       True,
            }
        finally:
            db.close()

    def _llm_classify(
        self,
        filename: str,
        initial_type: str,
        description: Optional[str],
        department_name: Optional[str],
    ) -> Dict[str, Any]:
        """
        Uses LLM to confirm or improve document classification.
        """
        try:
            result = self.llm.chat_json(
                system_prompt=DOCUMENT_SYSTEM_PROMPT,
                user_message=(
                    f"Document filename  : {filename}\n"
                    f"Initial type guess : {initial_type}\n"
                    f"Patient description: {description or 'none provided'}\n"
                    f"Department context : {department_name or 'not specified'}\n\n"
                    f"Confirm or improve the document classification."
                ),
            )
            return result

        except Exception as e:
            logger.error(f"[DOC AGENT] LLM classification failed: {e}")
            return {
                "confirmed_document_type":     initial_type,
                "classification_confidence":   0.5,
                "is_relevant_for_appointment": True,
                "relevance_reason":            "Classification based on filename",
                "patient_message": (
                    f"Document '{filename}' has been uploaded successfully."
                ),
                "additional_notes": None,
            }


# ── Singleton instance ─────────────────────────────────────────
document_agent = DocumentAgent()