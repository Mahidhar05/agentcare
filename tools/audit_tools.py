# tools/audit_tools.py

import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import AuditEvent

logger = logging.getLogger(__name__)


def log_audit_event(
    db: Session,
    action: str,
    actor_id: int = None,
    entity_type: str = None,
    entity_id: int = None,
    metadata: dict = None,
    ip_address: str = None,
) -> AuditEvent:
    """
    Writes a single audit event to the database.
    Called by every agent and tool after any meaningful action.

    Args:
        db          : active SQLAlchemy session
        action      : short action name e.g. 'appointment_booked'
        actor_id    : user_id who triggered the action (None = system)
        entity_type : e.g. 'Appointment', 'Document', 'WorkflowRun'
        entity_id   : primary key of the affected entity
        metadata    : any extra context as a dict (will be JSON-serialized)
        ip_address  : optional IP of the request

    Returns:
        The saved AuditEvent ORM object
    """
    try:
        meta_str = json.dumps(metadata) if metadata else None

        event = AuditEvent(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            meta_data=meta_str,
            ip_address=ip_address,
            created_at=datetime.utcnow(),
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info(
            f"[AUDIT] action={action} | actor={actor_id} | "
            f"entity={entity_type}#{entity_id}"
        )
        return event

    except Exception as e:
        logger.error(f"[AUDIT] Failed to write audit event: {e}")
        db.rollback()
        raise


def get_audit_trail(
    db: Session,
    entity_type: str = None,
    entity_id: int = None,
    actor_id: int = None,
    limit: int = 100,
) -> list:
    """
    Retrieves audit events filtered by entity or actor.

    Returns:
        List of AuditEvent dicts
    """
    try:
        query = db.query(AuditEvent)

        if entity_type:
            query = query.filter(AuditEvent.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditEvent.entity_id == entity_id)
        if actor_id:
            query = query.filter(AuditEvent.actor_id == actor_id)

        events = query.order_by(
            AuditEvent.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "id": e.id,
                "action": e.action,
                "actor_id": e.actor_id,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "metadata": json.loads(e.meta_data) if e.meta_data else {},
                "ip_address": e.ip_address,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]

    except Exception as e:
        logger.error(f"[AUDIT] Failed to retrieve audit trail: {e}")
        return []


def get_full_audit_log(db: Session, limit: int = 200) -> list:
    """
    Returns the full audit log for staff/admin view.
    """
    try:
        events = db.query(AuditEvent).order_by(
            AuditEvent.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "id": e.id,
                "action": e.action,
                "actor_id": e.actor_id,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "metadata": json.loads(e.meta_data) if e.meta_data else {},
                "ip_address": e.ip_address,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    except Exception as e:
        logger.error(f"[AUDIT] Failed to fetch full log: {e}")
        return []