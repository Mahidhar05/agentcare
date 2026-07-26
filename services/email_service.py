# services/email_service.py

import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from database.connection import get_db_session
from database.models import (
    Notification, NotificationStatus, NotificationType,
    User, UserRole
)
from config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email notification service.

    Supports 4 modes:
    - 'console' : Prints email to terminal (for dev)
    - 'database': Stores in DB (visible in UI for demo)
    - 'smtp'    : Actually sends via SMTP
    - 'both'    : Stores in DB AND sends via SMTP (best for demo)
    """

    def __init__(self):
        self.mode = settings.EMAIL_MODE.lower()
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_name = settings.SMTP_FROM_NAME

    # ══════════════════════════════════════════════════════
    # PUBLIC — Send escalation email to all staff
    # ══════════════════════════════════════════════════════
    def send_escalation_alert_to_staff(
        self,
        escalation_id: int,
        reason: str,
        details: str,
        workflow_run_id: Optional[int] = None,
        patient_name: str = "A patient",
    ) -> List[Dict[str, Any]]:
        """
        Sends escalation alert to ALL staff/admin users.
        Returns list of notification records.
        """
        db = get_db_session()
        try:
            # Get all staff + admin users
            staff_users = db.query(User).filter(
                User.role.in_([UserRole.staff, UserRole.admin]),
                User.is_active == True,
            ).all()

            if not staff_users:
                logger.warning("[EMAIL] No staff users found to notify")
                return []

            subject = f"🚨 New Escalation #{escalation_id} — Requires Review"
            body_html = self._build_escalation_html(
                escalation_id=escalation_id,
                reason=reason,
                details=details,
                patient_name=patient_name,
                workflow_run_id=workflow_run_id,
            )
            body_plain = self._build_escalation_plain(
                escalation_id=escalation_id,
                reason=reason,
                details=details,
                patient_name=patient_name,
            )

            results = []
            for user in staff_users:
                result = self._dispatch_notification(
                    db=db,
                    recipient_email=user.email,
                    recipient_name=user.name,
                    subject=subject,
                    body_html=body_html,
                    body_plain=body_plain,
                    notification_type=NotificationType.escalation_alert,
                    escalation_id=escalation_id,
                    workflow_run_id=workflow_run_id,
                )
                results.append(result)

            logger.info(
                f"[EMAIL] Escalation #{escalation_id} alert dispatched to "
                f"{len(results)} staff member(s) via mode='{self.mode}'"
            )
            return results

        except Exception as e:
            logger.error(f"[EMAIL] Failed to send escalation alerts: {e}")
            return []
        finally:
            db.close()

    # ══════════════════════════════════════════════════════
    # PATIENT EMAILS
    # ══════════════════════════════════════════════════════
    
    def send_appointment_confirmation(
        self,
        patient_email: str,
        patient_name: str,
        appointment_id: int,
        doctor_name: str,
        specialization: str,
        department: str,
        date: str,
        time: str,
        reason: str = "",
    ) -> Dict[str, Any]:
        """Sends appointment confirmation letter to patient."""
        db = get_db_session()
        try:
            subject = f"✅ Appointment Confirmed — {date} at {time}"
            body_html = self._build_appointment_confirm_html(
                patient_name, appointment_id, doctor_name, specialization,
                department, date, time, reason
            )
            body_plain = self._build_appointment_confirm_plain(
                patient_name, appointment_id, doctor_name, department, date, time
            )
            return self._dispatch_notification(
                db=db,
                recipient_email=patient_email,
                recipient_name=patient_name,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                notification_type=NotificationType.appointment_confirm,
            )
        finally:
            db.close()

    def send_appointment_reschedule(
        self,
        patient_email: str,
        patient_name: str,
        appointment_id: int,
        doctor_name: str,
        department: str,
        new_date: str,
        new_time: str,
    ) -> Dict[str, Any]:
        """Sends reschedule notification."""
        db = get_db_session()
        try:
            subject = f"🔄 Appointment Rescheduled — Now on {new_date}"
            body_html = self._build_reschedule_html(
                patient_name, appointment_id, doctor_name, department, new_date, new_time
            )
            body_plain = f"""
Dear {patient_name},

Your appointment #{appointment_id} has been rescheduled.

NEW DETAILS:
Doctor:     {doctor_name}
Department: {department}
Date:       {new_date}
Time:       {new_time}

Please arrive 15 minutes early with your ID and documents.

— AgentCare Team
"""
            return self._dispatch_notification(
                db=db,
                recipient_email=patient_email,
                recipient_name=patient_name,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                notification_type=NotificationType.appointment_confirm,
            )
        finally:
            db.close()

    def send_appointment_cancellation(
        self,
        patient_email: str,
        patient_name: str,
        appointment_id: int,
        doctor_name: str,
        date: str,
        time: str,
    ) -> Dict[str, Any]:
        """Sends cancellation confirmation."""
        db = get_db_session()
        try:
            subject = f"❌ Appointment Cancelled — {date}"
            body_html = self._build_cancellation_html(
                patient_name, appointment_id, doctor_name, date, time
            )
            body_plain = f"""
Dear {patient_name},

Your appointment #{appointment_id} has been cancelled.

CANCELLED APPOINTMENT:
Doctor: {doctor_name}
Date:   {date}
Time:   {time}

You can book a new appointment anytime through AgentCare.

— AgentCare Team
"""
            return self._dispatch_notification(
                db=db,
                recipient_email=patient_email,
                recipient_name=patient_name,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                notification_type=NotificationType.appointment_confirm,
            )
        finally:
            db.close()

    def send_document_upload_receipt(
        self,
        patient_email: str,
        patient_name: str,
        document_type: str,
        filename: str,
        is_duplicate: bool = False,
        missing_docs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Sends document upload receipt to patient."""
        db = get_db_session()
        try:
            subject = f"📄 Document Received — {filename}"
            body_html = self._build_document_receipt_html(
                patient_name, document_type, filename, is_duplicate, missing_docs or []
            )
            body_plain = f"""
Dear {patient_name},

Your document has been received.

DOCUMENT DETAILS:
Filename: {filename}
Type:     {document_type}
Status:   {'Duplicate detected' if is_duplicate else 'Successfully stored'}

{f"MISSING DOCUMENTS: {', '.join(missing_docs)}" if missing_docs else ""}

— AgentCare Team
"""
            return self._dispatch_notification(
                db=db,
                recipient_email=patient_email,
                recipient_name=patient_name,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                notification_type=NotificationType.document_confirm,
            )
        finally:
            db.close()

    def send_safety_block_notice(
        self,
        patient_email: str,
        patient_name: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Sends notice when request was safety-blocked."""
        db = get_db_session()
        try:
            subject = "⚠️ Notice: Please Consult a Healthcare Provider"
            body_html = self._build_safety_block_html(patient_name, reason)
            body_plain = f"""
Dear {patient_name},

Your recent request could not be processed as it falls outside
our administrative scope.

For medical concerns, please:
- Consult a qualified healthcare provider
- Call emergency services (112) for urgent issues
- Visit the nearest emergency room if needed

— AgentCare Team
"""
            return self._dispatch_notification(
                db=db,
                recipient_email=patient_email,
                recipient_name=patient_name,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                notification_type=NotificationType.escalation_alert,
            )
        finally:
            db.close()


    # ══════════════════════════════════════════════════════
    # INTERNAL — Dispatch based on EMAIL_MODE
    # ══════════════════════════════════════════════════════
    def _dispatch_notification(
        self,
        db: Session,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        body_html: str,
        body_plain: str,
        notification_type: NotificationType,
        escalation_id: Optional[int] = None,
        workflow_run_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Central dispatcher — creates DB record and/or sends SMTP."""

        # Always create the notification record first
        notification = Notification(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=subject,
            body_html=body_html,
            body_plain=body_plain,
            notification_type=notification_type,
            status=NotificationStatus.pending,
            escalation_id=escalation_id,
            workflow_run_id=workflow_run_id,
            created_at=datetime.utcnow(),
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Console mode
        if self.mode == "console":
            self._log_to_console(recipient_email, subject, body_plain)
            notification.status = NotificationStatus.sent
            notification.sent_at = datetime.utcnow()
            db.commit()

        # Database-only mode (great for demo)
        elif self.mode == "database":
            notification.status = NotificationStatus.sent
            notification.sent_at = datetime.utcnow()
            db.commit()
            logger.info(
                f"[EMAIL] Notification saved to DB for {recipient_email} "
                f"(mode=database, no real send)"
            )

        # SMTP mode (real send)
        elif self.mode == "smtp":
            ok, err = self._send_via_smtp(
                recipient_email, subject, body_html, body_plain
            )
            if ok:
                notification.status = NotificationStatus.sent
                notification.sent_at = datetime.utcnow()
            else:
                notification.status = NotificationStatus.failed
                notification.error_message = err
            db.commit()

        # Both modes (save + send)
        elif self.mode == "both":
            ok, err = self._send_via_smtp(
                recipient_email, subject, body_html, body_plain
            )
            if ok:
                notification.status = NotificationStatus.sent
                notification.sent_at = datetime.utcnow()
            else:
                notification.status = NotificationStatus.failed
                notification.error_message = err
                logger.warning(
                    f"[EMAIL] SMTP failed but saved in DB: {err}"
                )
            db.commit()

        return {
            "notification_id": notification.id,
            "recipient":       recipient_email,
            "status":          notification.status.value,
            "sent_at":         notification.sent_at.isoformat() if notification.sent_at else None,
        }

    def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: str,
    ) -> tuple:
        """Sends via Gmail SMTP. Returns (success, error_msg)."""
        if not self.smtp_user or not self.smtp_password:
            return False, "SMTP credentials not configured in .env"

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"{self.from_name} <{self.smtp_user}>"
            msg["To"]      = to_email

            msg.attach(MIMEText(plain_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_email, msg.as_string())

            logger.info(f"[EMAIL] Sent SMTP to {to_email}")
            return True, None

        except Exception as e:
            logger.error(f"[EMAIL] SMTP send failed: {e}")
            return False, str(e)

    def _log_to_console(self, to_email: str, subject: str, body: str):
        print()
        print("=" * 70)
        print(f"📧 EMAIL (console mode)")
        print("=" * 70)
        print(f"To:      {to_email}")
        print(f"Subject: {subject}")
        print("-" * 70)
        print(body)
        print("=" * 70)
        print()

    # ══════════════════════════════════════════════════════
    # HTML TEMPLATE
    # ══════════════════════════════════════════════════════
    def _build_escalation_html(
        self,
        escalation_id: int,
        reason: str,
        details: str,
        patient_name: str,
        workflow_run_id: Optional[int],
    ) -> str:
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Roboto, sans-serif;
            background: #f1f5f9;
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #dc2626 0%, #ea580c 100%);
            padding: 32px;
            text-align: center;
            color: white;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 800;
        }}
        .header p {{
            margin: 8px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
        }}
        .body {{
            padding: 32px;
        }}
        .alert-box {{
            background: #fef2f2;
            border-left: 4px solid #dc2626;
            padding: 16px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .info-row {{
            display: flex;
            padding: 12px 0;
            border-bottom: 1px solid #e5e7eb;
        }}
        .info-label {{
            font-weight: 700;
            color: #4b5563;
            width: 140px;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .info-value {{
            color: #111827;
            flex: 1;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white !important;
            padding: 14px 32px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 700;
            margin: 20px 0;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }}
        .footer {{
            background: #f9fafb;
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 12px;
        }}
        .badge {{
            display: inline-block;
            background: #fee2e2;
            color: #991b1b;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Escalation Alert</h1>
            <p>A patient request requires your immediate review</p>
        </div>

        <div class="body">
            <div class="alert-box">
                <span class="badge">⚠️ URGENT · Escalation #{escalation_id}</span>
                <p style="margin: 12px 0 0 0; color: #111827; font-weight: 600; font-size: 15px;">
                    {reason}
                </p>
            </div>

            <div class="info-row">
                <div class="info-label">Escalation ID</div>
                <div class="info-value">#{escalation_id}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Patient</div>
                <div class="info-value">{patient_name}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Workflow</div>
                <div class="info-value">#{workflow_run_id or 'N/A'}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Time</div>
                <div class="info-value">{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
            </div>

            <h3 style="color: #111827; margin-top: 24px;">📋 Full Details</h3>
            <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; color: #374151; font-family: monospace; font-size: 13px; line-height: 1.6;">
                {details}
            </div>

            <div style="text-align: center; margin-top: 32px;">
                <a href="http://localhost:8501" class="cta-button">
                    🔗 Review in Staff Portal
                </a>
            </div>

            <p style="color: #6b7280; font-size: 13px; text-align: center; margin-top: 16px;">
                Please review and provide a resolution note as soon as possible.
            </p>
        </div>

        <div class="footer">
            <p style="margin: 0;">
                <strong>AgentCare</strong> · Agentic AI Healthcare Administration<br>
                This is an automated alert. Do not reply to this email.
            </p>
        </div>
    </div>
</body>
</html>"""

    def _build_escalation_plain(
        self,
        escalation_id: int,
        reason: str,
        details: str,
        patient_name: str,
    ) -> str:
        return f"""
🚨 ESCALATION ALERT — Requires Review

Escalation ID: #{escalation_id}
Patient:       {patient_name}
Time:          {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

REASON:
{reason}

FULL DETAILS:
{details}

Please log in to the Staff Portal to review:
http://localhost:8501

---
AgentCare · Automated Alert
"""
    # ══════════════════════════════════════════════════════
    # PATIENT EMAIL TEMPLATES
    # ══════════════════════════════════════════════════════
    
    def _build_appointment_confirm_html(self, name, appt_id, doctor, spec, dept, date, time, reason):
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body{{font-family:'Segoe UI',sans-serif;background:#f1f5f9;padding:20px;margin:0}}
.container{{max-width:600px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,0.1)}}
.header{{background:linear-gradient(135deg,#10b981 0%,#059669 100%);padding:32px;text-align:center;color:white}}
.header h1{{margin:0;font-size:28px;font-weight:800}}
.body{{padding:32px}}
.appt-card{{background:linear-gradient(135deg,#f0fdf4 0%,#dcfce7 100%);border:2px solid #10b981;border-radius:16px;padding:24px;margin:20px 0}}
.appt-id{{background:#10b981;color:white;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:700;display:inline-block;margin-bottom:12px}}
.detail-row{{display:flex;padding:10px 0;border-bottom:1px solid #d1fae5}}
.detail-label{{font-weight:700;color:#065f46;width:120px}}
.detail-value{{color:#111827;flex:1}}
.instructions{{background:#eff6ff;border-left:4px solid #3b82f6;padding:16px;border-radius:8px;margin:20px 0}}
.footer{{background:#f9fafb;padding:20px;text-align:center;color:#6b7280;font-size:12px}}
</style></head><body>
<div class="container">
    <div class="header">
        <h1>✅ Appointment Confirmed</h1>
        <p style="margin:8px 0 0 0;opacity:0.95">Your appointment has been successfully scheduled</p>
    </div>
    <div class="body">
        <p style="font-size:16px;color:#111827">Dear <b>{name}</b>,</p>
        <p style="color:#4b5563">We're pleased to confirm your upcoming appointment. Please find the details below:</p>
        
        <div class="appt-card">
            <span class="appt-id">📋 APPOINTMENT #{appt_id}</span>
            <div class="detail-row"><div class="detail-label">👨‍⚕️ Doctor</div><div class="detail-value"><b>{doctor}</b></div></div>
            <div class="detail-row"><div class="detail-label">🩺 Specialty</div><div class="detail-value">{spec or 'General'}</div></div>
            <div class="detail-row"><div class="detail-label">🏥 Department</div><div class="detail-value">{dept}</div></div>
            <div class="detail-row"><div class="detail-label">📅 Date</div><div class="detail-value"><b>{date}</b></div></div>
            <div class="detail-row"><div class="detail-label">🕐 Time</div><div class="detail-value"><b>{time}</b></div></div>
            {f'<div class="detail-row"><div class="detail-label">📝 Reason</div><div class="detail-value">{reason[:100]}</div></div>' if reason else ''}
        </div>
        
        <div class="instructions">
            <h4 style="margin:0 0 8px 0;color:#1e40af">📌 Important Instructions</h4>
            <ul style="margin:8px 0;color:#374151;padding-left:20px">
                <li>Arrive <b>15 minutes early</b> for check-in</li>
                <li>Bring a <b>valid photo ID</b> (Aadhar/Passport/DL)</li>
                <li>Bring any <b>previous medical records</b> and reports</li>
                <li>Bring your <b>insurance card</b> if applicable</li>
                <li>Reminder will be sent 24h and 2h before the appointment</li>
            </ul>
        </div>
        
        <p style="color:#4b5563;font-size:14px;margin-top:24px">
            Need to reschedule or cancel? Log in to your AgentCare portal anytime.
        </p>
    </div>
    <div class="footer">
        <p style="margin:0"><strong>AgentCare</strong> · Agentic AI Healthcare Administration<br>
        This is an automated confirmation. Please do not reply to this email.</p>
    </div>
</div></body></html>"""

    def _build_appointment_confirm_plain(self, name, appt_id, doctor, dept, date, time):
        return f"""
✅ APPOINTMENT CONFIRMED

Dear {name},

Your appointment has been successfully scheduled.

APPOINTMENT #{appt_id}
Doctor:     {doctor}
Department: {dept}
Date:       {date}
Time:       {time}

IMPORTANT:
- Arrive 15 minutes early
- Bring valid photo ID
- Bring previous medical records
- Reminders will be sent 24h and 2h before

— AgentCare Team
"""

    def _build_reschedule_html(self, name, appt_id, doctor, dept, new_date, new_time):
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body{{font-family:'Segoe UI',sans-serif;background:#f1f5f9;padding:20px;margin:0}}
.container{{max-width:600px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,0.1)}}
.header{{background:linear-gradient(135deg,#3b82f6 0%,#2563eb 100%);padding:32px;text-align:center;color:white}}
.header h1{{margin:0;font-size:28px}}
.body{{padding:32px}}
.appt-card{{background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);border:2px solid #3b82f6;border-radius:16px;padding:24px;margin:20px 0}}
.detail-row{{display:flex;padding:10px 0;border-bottom:1px solid #bfdbfe}}
.detail-label{{font-weight:700;color:#1e40af;width:120px}}
.detail-value{{color:#111827;flex:1}}
.footer{{background:#f9fafb;padding:20px;text-align:center;color:#6b7280;font-size:12px}}
</style></head><body>
<div class="container">
    <div class="header">
        <h1>🔄 Appointment Rescheduled</h1>
        <p style="margin:8px 0 0 0;opacity:0.95">Your appointment has been moved to a new date</p>
    </div>
    <div class="body">
        <p>Dear <b>{name}</b>,</p>
        <p>Your appointment #{appt_id} has been successfully rescheduled to the new date shown below:</p>
        
        <div class="appt-card">
            <div class="detail-row"><div class="detail-label">👨‍⚕️ Doctor</div><div class="detail-value"><b>{doctor}</b></div></div>
            <div class="detail-row"><div class="detail-label">🏥 Department</div><div class="detail-value">{dept}</div></div>
            <div class="detail-row"><div class="detail-label">📅 New Date</div><div class="detail-value"><b style="color:#2563eb">{new_date}</b></div></div>
            <div class="detail-row"><div class="detail-label">🕐 New Time</div><div class="detail-value"><b style="color:#2563eb">{new_time}</b></div></div>
        </div>
        
        <p style="color:#4b5563">Please make note of the new date and time. Reminders will be sent automatically.</p>
    </div>
    <div class="footer">
        <p style="margin:0"><strong>AgentCare</strong> · Automated Notification</p>
    </div>
</div></body></html>"""

    def _build_cancellation_html(self, name, appt_id, doctor, date, time):
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body{{font-family:'Segoe UI',sans-serif;background:#f1f5f9;padding:20px;margin:0}}
.container{{max-width:600px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,0.1)}}
.header{{background:linear-gradient(135deg,#ef4444 0%,#dc2626 100%);padding:32px;text-align:center;color:white}}
.header h1{{margin:0;font-size:28px}}
.body{{padding:32px}}
.appt-card{{background:linear-gradient(135deg,#fef2f2 0%,#fee2e2 100%);border:2px solid #ef4444;border-radius:16px;padding:24px;margin:20px 0;opacity:0.85;text-decoration:line-through}}
.detail-row{{display:flex;padding:10px 0;border-bottom:1px solid #fecaca}}
.detail-label{{font-weight:700;color:#991b1b;width:120px}}
.detail-value{{color:#111827;flex:1}}
.footer{{background:#f9fafb;padding:20px;text-align:center;color:#6b7280;font-size:12px}}
</style></head><body>
<div class="container">
    <div class="header">
        <h1>❌ Appointment Cancelled</h1>
    </div>
    <div class="body">
        <p>Dear <b>{name}</b>,</p>
        <p>This confirms the cancellation of your appointment:</p>
        
        <div class="appt-card">
            <div class="detail-row"><div class="detail-label">📋 ID</div><div class="detail-value">#{appt_id}</div></div>
            <div class="detail-row"><div class="detail-label">👨‍⚕️ Doctor</div><div class="detail-value">{doctor}</div></div>
            <div class="detail-row"><div class="detail-label">📅 Date</div><div class="detail-value">{date}</div></div>
            <div class="detail-row"><div class="detail-label">🕐 Time</div><div class="detail-value">{time}</div></div>
        </div>
        
        <p style="color:#4b5563">You can book a new appointment anytime through the AgentCare portal.</p>
    </div>
    <div class="footer">
        <p style="margin:0"><strong>AgentCare</strong> · Automated Notification</p>
    </div>
</div></body></html>"""

    def _build_document_receipt_html(self, name, doc_type, filename, is_dup, missing):
        dup_notice = ""
        if is_dup:
            dup_notice = '<div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:12px;border-radius:8px;margin:16px 0;color:#78350f"><b>⚠️ Duplicate Detected:</b> This document appears to already be in our system.</div>'
        
        missing_notice = ""
        if missing:
            missing_list = ''.join(f'<li>{m}</li>' for m in missing)
            missing_notice = f'<div style="background:#fef2f2;border-left:4px solid #ef4444;padding:12px;border-radius:8px;margin:16px 0"><b style="color:#991b1b">📋 Still Needed:</b><ul style="margin:8px 0 0 20px;color:#374151">{missing_list}</ul></div>'
        
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body{{font-family:'Segoe UI',sans-serif;background:#f1f5f9;padding:20px;margin:0}}
.container{{max-width:600px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,0.1)}}
.header{{background:linear-gradient(135deg,#8b5cf6 0%,#6d28d9 100%);padding:32px;text-align:center;color:white}}
.header h1{{margin:0;font-size:28px}}
.body{{padding:32px}}
.doc-card{{background:#f5f3ff;border:2px solid #8b5cf6;border-radius:16px;padding:24px;margin:20px 0}}
.detail-row{{display:flex;padding:10px 0;border-bottom:1px solid #ddd6fe}}
.detail-label{{font-weight:700;color:#5b21b6;width:120px}}
.detail-value{{color:#111827;flex:1}}
.footer{{background:#f9fafb;padding:20px;text-align:center;color:#6b7280;font-size:12px}}
</style></head><body>
<div class="container">
    <div class="header">
        <h1>📄 Document Received</h1>
    </div>
    <div class="body">
        <p>Dear <b>{name}</b>,</p>
        <p>Your document has been successfully received and processed:</p>
        
        <div class="doc-card">
            <div class="detail-row"><div class="detail-label">📎 Filename</div><div class="detail-value"><b>{filename}</b></div></div>
            <div class="detail-row"><div class="detail-label">🏷️ Type</div><div class="detail-value">{doc_type}</div></div>
            <div class="detail-row"><div class="detail-label">✅ Status</div><div class="detail-value">{'Stored (Duplicate)' if is_dup else 'Successfully Stored'}</div></div>
        </div>
        
        {dup_notice}
        {missing_notice}
    </div>
    <div class="footer">
        <p style="margin:0"><strong>AgentCare</strong> · Automated Notification</p>
    </div>
</div></body></html>"""

    def _build_safety_block_html(self, name, reason):
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body{{font-family:'Segoe UI',sans-serif;background:#f1f5f9;padding:20px;margin:0}}
.container{{max-width:600px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,0.1)}}
.header{{background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%);padding:32px;text-align:center;color:white}}
.header h1{{margin:0;font-size:28px}}
.body{{padding:32px}}
.notice-box{{background:#fef3c7;border-left:4px solid #f59e0b;padding:20px;border-radius:8px;margin:20px 0}}
.emergency-box{{background:#fef2f2;border:2px solid #ef4444;padding:20px;border-radius:12px;margin:20px 0;text-align:center}}
.footer{{background:#f9fafb;padding:20px;text-align:center;color:#6b7280;font-size:12px}}
</style></head><body>
<div class="container">
    <div class="header">
        <h1>⚠️ Please Consult a Doctor</h1>
    </div>
    <div class="body">
        <p>Dear <b>{name}</b>,</p>
        
        <div class="notice-box">
            <p style="margin:0;color:#78350f"><b>Your recent request falls outside our administrative scope.</b></p>
            <p style="margin:8px 0 0 0;color:#92400e;font-size:14px">Reason: {reason[:200]}</p>
        </div>
        
        <p>AgentCare handles administrative tasks (booking, documents, reminders) but cannot provide medical advice, diagnoses, or prescriptions.</p>
        
        <p><b>For medical concerns, please:</b></p>
        <ul>
            <li>Book an appointment with a qualified doctor via AgentCare</li>
            <li>Consult your primary care physician</li>
            <li>Visit the nearest clinic or hospital</li>
        </ul>
        
        <div class="emergency-box">
            <h3 style="margin:0 0 8px 0;color:#991b1b">🚨 For Emergencies</h3>
            <p style="margin:0;font-size:18px;color:#dc2626"><b>Call 112 immediately</b></p>
            <p style="margin:4px 0 0 0;color:#7f1d1d;font-size:13px">Or visit the nearest emergency room</p>
        </div>
    </div>
    <div class="footer">
        <p style="margin:0"><strong>AgentCare</strong> · Administrative System Only</p>
    </div>
</div></body></html>"""

# ── Singleton instance ─────────────────────────────────────────
email_service = EmailService()