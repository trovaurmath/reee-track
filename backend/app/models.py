"""Central model registry used by Alembic and tests."""

from app.core.models import Base
from app.modules.audit.models import AuditLog
from app.modules.equipment.models import (
    Collection,
    Equipment,
    EquipmentCategory,
    EquipmentEvent,
    EquipmentType,
    NumberSequence,
    Sector,
)
from app.modules.identity.models import Permission, RefreshSession, Role, User
from app.modules.storage.models import StorageAssignment, StorageLocation, StorageMovement
from app.modules.triage.models import (
    Triage,
    TriageAnswer,
    TriageClassification,
    TriageCriterion,
)

__all__ = [
    "AuditLog",
    "Base",
    "Collection",
    "Equipment",
    "EquipmentCategory",
    "EquipmentEvent",
    "EquipmentType",
    "NumberSequence",
    "Permission",
    "RefreshSession",
    "Role",
    "Sector",
    "StorageAssignment",
    "StorageLocation",
    "StorageMovement",
    "Triage",
    "TriageAnswer",
    "TriageClassification",
    "TriageCriterion",
    "User",
]
