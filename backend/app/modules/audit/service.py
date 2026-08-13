import uuid

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog


def record_audit(
    session: Session,
    *,
    action: str,
    resource_type: str,
    actor_user_id: uuid.UUID | None = None,
    resource_id: str | None = None,
    details: dict[str, object] | None = None,
    request_id: str | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        request_id=request_id,
    )
    session.add(log)
    return log

