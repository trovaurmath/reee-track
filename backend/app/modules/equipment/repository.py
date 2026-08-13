import uuid
from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, selectinload

from app.modules.equipment.models import (
    Equipment,
    EquipmentCategory,
    EquipmentEvent,
    EquipmentType,
    NumberSequence,
    Sector,
)


def next_sequence_value(session: Session, namespace: str, year: int) -> int:
    values = {"namespace": namespace, "year": year, "current_value": 1}
    dialect_name = session.get_bind().dialect.name

    if dialect_name == "postgresql":
        insert_statement = postgresql_insert(NumberSequence).values(**values)
    elif dialect_name == "sqlite":
        insert_statement = sqlite_insert(NumberSequence).values(**values)
    else:
        sequence = session.get(NumberSequence, {"namespace": namespace, "year": year})
        if sequence is None:
            sequence = NumberSequence(**values)
            session.add(sequence)
            session.flush()
            return 1
        sequence.current_value += 1
        session.flush()
        return sequence.current_value

    statement = insert_statement.on_conflict_do_update(
        index_elements=[NumberSequence.namespace, NumberSequence.year],
        set_={"current_value": NumberSequence.current_value + 1},
    ).returning(NumberSequence.current_value)
    return session.execute(statement).scalar_one()


def get_category(session: Session, category_id: uuid.UUID) -> EquipmentCategory | None:
    return session.get(EquipmentCategory, category_id)


def get_equipment_type(session: Session, type_id: uuid.UUID) -> EquipmentType | None:
    return session.get(EquipmentType, type_id)


def get_sector(session: Session, sector_id: uuid.UUID) -> Sector | None:
    return session.get(Sector, sector_id)


def get_equipment(session: Session, equipment_id: uuid.UUID) -> Equipment | None:
    statement = (
        select(Equipment)
        .where(Equipment.id == equipment_id)
        .options(selectinload(Equipment.collection))
    )
    return session.scalar(statement)


def get_equipment_for_update(session: Session, equipment_id: uuid.UUID) -> Equipment | None:
    statement = (
        select(Equipment)
        .where(Equipment.id == equipment_id)
        .options(selectinload(Equipment.collection))
        .with_for_update(of=Equipment)
    )
    return session.scalar(statement)


def get_equipment_by_tracking_code(session: Session, tracking_code: str) -> Equipment | None:
    statement = (
        select(Equipment)
        .where(Equipment.tracking_code == tracking_code.strip().upper())
        .options(selectinload(Equipment.collection))
    )
    return session.scalar(statement)


def get_equipment_by_asset_number(session: Session, asset_number: str) -> Equipment | None:
    return session.scalar(select(Equipment).where(Equipment.asset_number == asset_number))


def _apply_filters(
    statement: Select,
    *,
    query: str | None,
    category_id: uuid.UUID | None,
    equipment_type_id: uuid.UUID | None,
    origin_sector_id: uuid.UUID | None,
    status: str | None,
    collected_from: datetime | None,
    collected_to: datetime | None,
    include_archived: bool,
) -> Select:
    if not include_archived:
        statement = statement.where(Equipment.archived_at.is_(None))
    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                Equipment.tracking_code.ilike(pattern),
                Equipment.asset_number.ilike(pattern),
                Equipment.serial_number.ilike(pattern),
                Equipment.brand.ilike(pattern),
                Equipment.model.ilike(pattern),
            )
        )
    if category_id:
        statement = statement.where(Equipment.category_id == category_id)
    if equipment_type_id:
        statement = statement.where(Equipment.equipment_type_id == equipment_type_id)
    if origin_sector_id:
        statement = statement.where(Equipment.origin_sector_id == origin_sector_id)
    if status:
        statement = statement.where(Equipment.current_status == status.strip().upper())
    if collected_from:
        statement = statement.where(Equipment.collection_date >= collected_from)
    if collected_to:
        statement = statement.where(Equipment.collection_date <= collected_to)
    return statement


def list_equipments(
    session: Session,
    *,
    query: str | None = None,
    category_id: uuid.UUID | None = None,
    equipment_type_id: uuid.UUID | None = None,
    origin_sector_id: uuid.UUID | None = None,
    status: str | None = None,
    collected_from: datetime | None = None,
    collected_to: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
    include_archived: bool = False,
) -> tuple[list[Equipment], int]:
    filters = {
        "query": query,
        "category_id": category_id,
        "equipment_type_id": equipment_type_id,
        "origin_sector_id": origin_sector_id,
        "status": status,
        "collected_from": collected_from,
        "collected_to": collected_to,
        "include_archived": include_archived,
    }
    item_statement = _apply_filters(
        select(Equipment).options(selectinload(Equipment.collection)),
        **filters,
    )
    item_statement = (
        item_statement.order_by(Equipment.created_at.desc()).limit(limit).offset(offset)
    )
    count_statement = _apply_filters(select(func.count()).select_from(Equipment), **filters)
    return list(session.scalars(item_statement).unique()), session.scalar(count_statement) or 0


def list_events(session: Session, equipment_id: uuid.UUID) -> list[EquipmentEvent]:
    statement = (
        select(EquipmentEvent)
        .where(EquipmentEvent.equipment_id == equipment_id)
        .order_by(EquipmentEvent.occurred_at, EquipmentEvent.id)
    )
    return list(session.scalars(statement))


def list_traceability_events(
    session: Session,
    *,
    event_type: str | None = None,
    status: str | None = None,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[tuple[EquipmentEvent, Equipment]], int]:
    statement = select(EquipmentEvent, Equipment).join(
        Equipment, Equipment.id == EquipmentEvent.equipment_id
    )
    count_statement = select(func.count()).select_from(EquipmentEvent).join(
        Equipment, Equipment.id == EquipmentEvent.equipment_id
    )
    conditions = []
    if event_type:
        conditions.append(EquipmentEvent.event_type == event_type.strip().upper())
    if status:
        conditions.append(EquipmentEvent.new_status == status.strip().upper())
    if query:
        pattern = f"%{query.strip()}%"
        conditions.append(
            or_(
                Equipment.tracking_code.ilike(pattern),
                Equipment.asset_number.ilike(pattern),
                Equipment.brand.ilike(pattern),
                Equipment.model.ilike(pattern),
                EquipmentEvent.description.ilike(pattern),
            )
        )
    if conditions:
        statement = statement.where(*conditions)
        count_statement = count_statement.where(*conditions)
    statement = statement.order_by(
        EquipmentEvent.occurred_at.desc(), EquipmentEvent.id.desc()
    ).limit(limit).offset(offset)
    return list(session.execute(statement).tuples()), session.scalar(count_statement) or 0


def list_categories(session: Session, active_only: bool = True) -> list[EquipmentCategory]:
    statement = select(EquipmentCategory).order_by(EquipmentCategory.name)
    if active_only:
        statement = statement.where(EquipmentCategory.is_active.is_(True))
    return list(session.scalars(statement))


def list_equipment_types(session: Session, active_only: bool = True) -> list[EquipmentType]:
    statement = select(EquipmentType).order_by(EquipmentType.name)
    if active_only:
        statement = statement.where(EquipmentType.is_active.is_(True))
    return list(session.scalars(statement))


def list_sectors(session: Session, active_only: bool = True) -> list[Sector]:
    statement = select(Sector).order_by(Sector.name)
    if active_only:
        statement = statement.where(Sector.is_active.is_(True))
    return list(session.scalars(statement))
