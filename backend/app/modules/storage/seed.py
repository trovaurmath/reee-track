from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.equipment.models import Equipment, EquipmentEvent
from app.modules.identity.models import User
from app.modules.storage.models import StorageAssignment, StorageLocation, StorageMovement

DEMO_LOCATIONS = (
    ("DEP-A-E01-P01", "Depósito Central", "A", "E01", "P01", "01", 4),
    ("DEP-A-E01-P02", "Depósito Central", "A", "E01", "P02", "01", 4),
    ("DEP-B-E02-P01", "Depósito Técnico", "B", "E02", "P01", "01", 2),
)


def seed_storage(session: Session) -> int:
    locations: list[StorageLocation] = []
    for code, warehouse, aisle, rack, shelf, position, capacity in DEMO_LOCATIONS:
        location = session.scalar(
            select(StorageLocation).where(StorageLocation.code == code)
        )
        if location is None:
            location = StorageLocation(
                code=code,
                warehouse=warehouse,
                aisle=aisle,
                rack=rack,
                shelf=shelf,
                position=position,
                capacity=capacity,
                notes="Posição demonstrativa da V0.5.",
            )
            session.add(location)
        locations.append(location)
    session.commit()

    if not settings.seed_demo_data:
        return 0
    admin = session.scalar(
        select(User).where(User.username == settings.initial_admin_username.lower())
    )
    if admin is None:
        return 0
    candidates = list(
        session.scalars(
            select(Equipment)
            .where(Equipment.current_status == "ARMAZENADO")
            .where(Equipment.archived_at.is_(None))
            .order_by(Equipment.tracking_code)
            .limit(3)
        )
    )
    created = 0
    now = datetime.now(UTC)
    for index, equipment in enumerate(candidates):
        existing = session.scalar(
            select(StorageAssignment).where(
                StorageAssignment.equipment_id == equipment.id
            )
        )
        if existing:
            continue
        location = locations[index % len(locations)]
        occurred_at = now - timedelta(days=35 - index * 12)
        session.add(
            StorageAssignment(
                equipment_id=equipment.id,
                location_id=location.id,
                entered_at=occurred_at,
            )
        )
        session.add(
            StorageMovement(
                equipment_id=equipment.id,
                to_location_id=location.id,
                movement_type="ENTRY",
                occurred_at=occurred_at,
                user_id=admin.id,
                notes="Movimentação fictícia para demonstração.",
            )
        )
        session.add(
            EquipmentEvent(
                equipment_id=equipment.id,
                event_type="STORAGE_ENTRY",
                previous_status=equipment.current_status,
                new_status=equipment.current_status,
                occurred_at=occurred_at,
                user_id=admin.id,
                location=location.code,
                description=f"Entrada demonstrativa no armazenamento em {location.code}.",
                metadata_json={"demo": True, "to_location": location.code},
            )
        )
        created += 1
    session.commit()
    return created
