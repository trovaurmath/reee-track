import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.equipment.models import Equipment
from app.modules.storage.models import StorageAssignment, StorageLocation, StorageMovement


def get_location(session: Session, location_id: uuid.UUID) -> StorageLocation | None:
    return session.get(StorageLocation, location_id)


def get_location_by_code(session: Session, code: str) -> StorageLocation | None:
    return session.scalar(select(StorageLocation).where(StorageLocation.code == code))


def list_locations(
    session: Session, *, query: str | None = None, include_inactive: bool = False
) -> list[tuple[StorageLocation, int]]:
    statement = (
        select(StorageLocation, func.count(StorageAssignment.id))
        .outerjoin(StorageAssignment, StorageAssignment.location_id == StorageLocation.id)
        .group_by(StorageLocation.id)
    )
    if not include_inactive:
        statement = statement.where(StorageLocation.is_active.is_(True))
    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                StorageLocation.code.ilike(pattern),
                StorageLocation.warehouse.ilike(pattern),
                StorageLocation.aisle.ilike(pattern),
                StorageLocation.rack.ilike(pattern),
                StorageLocation.shelf.ilike(pattern),
                StorageLocation.position.ilike(pattern),
            )
        )
    return list(session.execute(statement.order_by(StorageLocation.code)).tuples())


def count_occupancy(session: Session, location_id: uuid.UUID) -> int:
    statement = select(func.count()).select_from(StorageAssignment).where(
        StorageAssignment.location_id == location_id
    )
    return session.scalar(statement) or 0


def get_assignment_for_equipment(
    session: Session, equipment_id: uuid.UUID
) -> StorageAssignment | None:
    return session.scalar(
        select(StorageAssignment).where(StorageAssignment.equipment_id == equipment_id)
    )


def list_occupancies(
    session: Session, *, query: str | None = None
) -> list[tuple[StorageAssignment, Equipment, StorageLocation]]:
    statement = (
        select(StorageAssignment, Equipment, StorageLocation)
        .join(Equipment, Equipment.id == StorageAssignment.equipment_id)
        .join(StorageLocation, StorageLocation.id == StorageAssignment.location_id)
    )
    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                Equipment.tracking_code.ilike(pattern),
                Equipment.asset_number.ilike(pattern),
                Equipment.brand.ilike(pattern),
                Equipment.model.ilike(pattern),
                StorageLocation.code.ilike(pattern),
            )
        )
    return list(
        session.execute(
            statement.order_by(StorageAssignment.entered_at.desc())
        ).tuples()
    )


def list_movements(
    session: Session, *, limit: int = 100
) -> list[tuple[StorageMovement, Equipment, str | None, str | None]]:
    from_location = StorageLocation.__table__.alias("from_location")
    to_location = StorageLocation.__table__.alias("to_location")
    statement = (
        select(
            StorageMovement,
            Equipment,
            from_location.c.code,
            to_location.c.code,
        )
        .join(Equipment, Equipment.id == StorageMovement.equipment_id)
        .outerjoin(from_location, from_location.c.id == StorageMovement.from_location_id)
        .outerjoin(to_location, to_location.c.id == StorageMovement.to_location_id)
        .order_by(StorageMovement.occurred_at.desc(), StorageMovement.id.desc())
        .limit(limit)
    )
    return list(session.execute(statement).tuples())
