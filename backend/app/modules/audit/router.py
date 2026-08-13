from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.authorization import require_permissions
from app.core.database import get_db
from app.modules.audit.models import AuditLog
from app.modules.audit.schemas import AuditLogRead
from app.modules.identity.models import User

router = APIRouter(prefix="/audit-logs", tags=["Auditoria"])


@router.get("", response_model=list[AuditLogRead])
def get_audit_logs(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("audit:read"))],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditLog]:
    del current_user
    statement = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    return list(session.scalars(statement))

