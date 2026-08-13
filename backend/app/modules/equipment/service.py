import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError, ConflictError, NotFoundError
from app.modules.audit.service import record_audit
from app.modules.equipment import repository
from app.modules.equipment.models import (
    Collection,
    Equipment,
    EquipmentCategory,
    EquipmentEvent,
    EquipmentType,
    Sector,
)
from app.modules.equipment.schemas import (
    CatalogCreate,
    CatalogRead,
    EquipmentArchiveRequest,
    EquipmentCreate,
    EquipmentRead,
    EquipmentUpdate,
    TimelineNoteCreate,
    WorkflowTransitionRequest,
)
from app.modules.equipment.workflow import STATUS_BY_CODE, ensure_manual_transition
from app.modules.identity.models import User


def normalize_optional(value: str | None, *, uppercase: bool = False) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized.upper() if uppercase else normalized


def ensure_timezone(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def to_catalog_read(catalog: EquipmentCategory | EquipmentType | Sector) -> CatalogRead:
    return CatalogRead.model_validate(catalog)


def to_equipment_read(equipment: Equipment) -> EquipmentRead:
    return EquipmentRead(
        id=equipment.id,
        tracking_code=equipment.tracking_code,
        asset_number=equipment.asset_number,
        serial_number=equipment.serial_number,
        equipment_type=to_catalog_read(equipment.equipment_type),
        category=to_catalog_read(equipment.category),
        origin_sector=to_catalog_read(equipment.origin_sector),
        brand=equipment.brand,
        model=equipment.model,
        description=equipment.description,
        initial_condition=equipment.initial_condition,
        current_status=equipment.current_status,
        collection_date=equipment.collection_date,
        collection_notes=equipment.collection.notes if equipment.collection else None,
        is_archived=equipment.archived_at is not None,
        archived_at=equipment.archived_at,
        archive_reason=equipment.archive_reason,
        created_at=equipment.created_at,
        updated_at=equipment.updated_at,
    )


def _validate_catalogs(
    session: Session,
    category_id: uuid.UUID,
    equipment_type_id: uuid.UUID,
    origin_sector_id: uuid.UUID,
) -> tuple[EquipmentCategory, EquipmentType, Sector]:
    category = repository.get_category(session, category_id)
    equipment_type = repository.get_equipment_type(session, equipment_type_id)
    sector = repository.get_sector(session, origin_sector_id)
    if category is None or not category.is_active:
        raise NotFoundError("Categoria não encontrada ou inativa")
    if equipment_type is None or not equipment_type.is_active:
        raise NotFoundError("Tipo de equipamento não encontrado ou inativo")
    if sector is None or not sector.is_active:
        raise NotFoundError("Setor de origem não encontrado ou inativo")
    return category, equipment_type, sector


def create_equipment(
    session: Session,
    data: EquipmentCreate,
    *,
    actor: User,
    request_id: str | None = None,
) -> Equipment:
    collection_date = ensure_timezone(data.collection_date)
    now = datetime.now(UTC)
    if collection_date > now + timedelta(minutes=5):
        raise ApplicationError("A data de recolhimento não pode estar no futuro")

    category, equipment_type, sector = _validate_catalogs(
        session,
        data.category_id,
        data.equipment_type_id,
        data.origin_sector_id,
    )
    asset_number = normalize_optional(data.asset_number, uppercase=True)
    if asset_number and repository.get_equipment_by_asset_number(session, asset_number):
        raise ConflictError("Número patrimonial já cadastrado")

    sequence = repository.next_sequence_value(session, "EQUIPMENT", collection_date.year)
    tracking_code = f"REEE-{collection_date.year}-{sequence:06d}"
    equipment = Equipment(
        tracking_code=tracking_code,
        asset_number=asset_number,
        serial_number=normalize_optional(data.serial_number),
        equipment_type=equipment_type,
        category=category,
        origin_sector=sector,
        brand=data.brand.strip(),
        model=data.model.strip(),
        description=normalize_optional(data.description),
        initial_condition=data.initial_condition.strip(),
        current_status="AGUARDANDO_TRIAGEM",
        collection_date=collection_date,
    )
    equipment.collection = Collection(
        collector_user_id=actor.id,
        notes=normalize_optional(data.collection_notes),
    )
    session.add(equipment)
    session.flush()

    registration_time = max(now, collection_date)
    events = (
        EquipmentEvent(
            equipment_id=equipment.id,
            event_type="COLLECTED",
            previous_status=None,
            new_status="RECOLHIDO",
            occurred_at=collection_date,
            user_id=actor.id,
            location=sector.name,
            description="Equipamento recolhido e incorporado ao processo de descarte.",
            metadata_json={"origin_sector_code": sector.code},
        ),
        EquipmentEvent(
            equipment_id=equipment.id,
            event_type="EQUIPMENT_REGISTERED",
            previous_status="RECOLHIDO",
            new_status="CADASTRADO",
            occurred_at=registration_time,
            user_id=actor.id,
            location=sector.name,
            description=f"Equipamento cadastrado com o código {tracking_code}.",
            metadata_json={},
        ),
        EquipmentEvent(
            equipment_id=equipment.id,
            event_type="QUEUED_FOR_TRIAGE",
            previous_status="CADASTRADO",
            new_status="AGUARDANDO_TRIAGEM",
            occurred_at=registration_time + timedelta(microseconds=1),
            user_id=actor.id,
            location=sector.name,
            description="Equipamento encaminhado para a fila de triagem.",
            metadata_json={},
        ),
    )
    session.add_all(events)
    record_audit(
        session,
        actor_user_id=actor.id,
        action="equipment.created",
        resource_type="equipment",
        resource_id=str(equipment.id),
        details={"tracking_code": tracking_code, "status": equipment.current_status},
        request_id=request_id,
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("Conflito ao cadastrar equipamento") from exc
    return get_equipment_or_raise(session, equipment.id)


def get_equipment_or_raise(session: Session, equipment_id: uuid.UUID) -> Equipment:
    equipment = repository.get_equipment(session, equipment_id)
    if equipment is None:
        raise NotFoundError("Equipamento não encontrado")
    return equipment


def get_equipment_by_code_or_raise(session: Session, tracking_code: str) -> Equipment:
    equipment = repository.get_equipment_by_tracking_code(session, tracking_code)
    if equipment is None:
        raise NotFoundError("Equipamento não encontrado")
    return equipment


def _validated_event_time(value: datetime | None) -> datetime:
    occurred_at = ensure_timezone(value) if value else datetime.now(UTC)
    if occurred_at > datetime.now(UTC) + timedelta(minutes=5):
        raise ApplicationError("A data do evento não pode estar no futuro")
    return occurred_at


def transition_equipment(
    session: Session,
    equipment_id: uuid.UUID,
    data: WorkflowTransitionRequest,
    *,
    actor: User,
    request_id: str | None = None,
) -> Equipment:
    equipment = repository.get_equipment_for_update(session, equipment_id)
    if equipment is None:
        raise NotFoundError("Equipamento não encontrado")
    previous, new = ensure_manual_transition(equipment.current_status, data.new_status)
    occurred_at = _validated_event_time(data.occurred_at)
    equipment.current_status = new
    session.add(
        EquipmentEvent(
            equipment_id=equipment.id,
            event_type="STATUS_CHANGED",
            previous_status=previous,
            new_status=new,
            occurred_at=occurred_at,
            user_id=actor.id,
            location=normalize_optional(data.location),
            description=data.description.strip(),
            metadata_json={
                "source": "manual_workflow",
                "status_label": STATUS_BY_CODE[new].label,
            },
        )
    )
    record_audit(
        session,
        actor_user_id=actor.id,
        action="equipment.status_changed",
        resource_type="equipment",
        resource_id=str(equipment.id),
        details={
            "tracking_code": equipment.tracking_code,
            "previous_status": previous,
            "new_status": new,
            "location": normalize_optional(data.location) or "",
        },
        request_id=request_id,
    )
    session.commit()
    return get_equipment_or_raise(session, equipment.id)


def add_timeline_note(
    session: Session,
    equipment_id: uuid.UUID,
    data: TimelineNoteCreate,
    *,
    actor: User,
    request_id: str | None = None,
) -> EquipmentEvent:
    equipment = get_equipment_or_raise(session, equipment_id)
    event = EquipmentEvent(
        equipment_id=equipment.id,
        event_type="OPERATIONAL_NOTE",
        previous_status=equipment.current_status,
        new_status=equipment.current_status,
        occurred_at=_validated_event_time(data.occurred_at),
        user_id=actor.id,
        location=normalize_optional(data.location),
        description=data.description.strip(),
        metadata_json={"source": "manual_note"},
    )
    session.add(event)
    record_audit(
        session,
        actor_user_id=actor.id,
        action="equipment.timeline_note_added",
        resource_type="equipment",
        resource_id=str(equipment.id),
        details={"tracking_code": equipment.tracking_code},
        request_id=request_id,
    )
    session.commit()
    session.refresh(event)
    return event


def update_equipment(
    session: Session,
    equipment_id: uuid.UUID,
    data: EquipmentUpdate,
    *,
    actor: User,
    request_id: str | None = None,
) -> Equipment:
    equipment = get_equipment_or_raise(session, equipment_id)
    if equipment.archived_at is not None:
        raise ConflictError("Equipamento arquivado não pode ser alterado")
    changes = data.model_dump(exclude_unset=True)
    before: dict[str, object] = {}
    after: dict[str, object] = {}

    catalog_keys = {"category_id", "equipment_type_id", "origin_sector_id"}
    if any(key in changes and changes[key] is None for key in catalog_keys):
        raise ApplicationError("Categoria, tipo e setor não podem ser nulos")
    if any(key in changes for key in catalog_keys):
        category_id = changes.get("category_id", equipment.category_id)
        equipment_type_id = changes.get("equipment_type_id", equipment.equipment_type_id)
        origin_sector_id = changes.get("origin_sector_id", equipment.origin_sector_id)
        category, equipment_type, sector = _validate_catalogs(
            session,
            category_id,
            equipment_type_id,
            origin_sector_id,
        )
        catalog_updates = {
            "category_id": ("category", category),
            "equipment_type_id": ("equipment_type", equipment_type),
            "origin_sector_id": ("origin_sector", sector),
        }
        for input_field, (relationship_name, catalog) in catalog_updates.items():
            if input_field not in changes:
                continue
            before[input_field] = str(getattr(equipment, input_field))
            setattr(equipment, relationship_name, catalog)
            after[input_field] = str(catalog.id)

    field_map = {
        "brand": "brand",
        "model": "model",
        "description": "description",
        "initial_condition": "initial_condition",
        "serial_number": "serial_number",
    }
    for input_field, model_field in field_map.items():
        if input_field not in changes:
            continue
        value = changes[input_field]
        if isinstance(value, str):
            value = normalize_optional(value)
        before[input_field] = str(getattr(equipment, model_field))
        setattr(equipment, model_field, value)
        after[input_field] = str(value)

    if "asset_number" in changes:
        asset_number = normalize_optional(changes["asset_number"], uppercase=True)
        duplicate = (
            repository.get_equipment_by_asset_number(session, asset_number)
            if asset_number
            else None
        )
        if duplicate and duplicate.id != equipment.id:
            raise ConflictError("Número patrimonial já cadastrado")
        before["asset_number"] = equipment.asset_number or ""
        equipment.asset_number = asset_number
        after["asset_number"] = asset_number or ""

    if "collection_notes" in changes and equipment.collection:
        before["collection_notes"] = equipment.collection.notes or ""
        equipment.collection.notes = normalize_optional(changes["collection_notes"])
        after["collection_notes"] = equipment.collection.notes or ""

    if before:
        record_audit(
            session,
            actor_user_id=actor.id,
            action="equipment.updated",
            resource_type="equipment",
            resource_id=str(equipment.id),
            details={"before": before, "after": after},
            request_id=request_id,
        )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("Conflito ao atualizar equipamento") from exc
    return get_equipment_or_raise(session, equipment.id)


def archive_equipment(
    session: Session,
    equipment_id: uuid.UUID,
    data: EquipmentArchiveRequest,
    *,
    actor: User,
    request_id: str | None = None,
) -> Equipment:
    equipment = repository.get_equipment_for_update(session, equipment_id)
    if equipment is None:
        raise NotFoundError("Equipamento não encontrado")
    if equipment.archived_at is not None:
        raise ConflictError("Equipamento já está arquivado")

    from app.modules.storage.repository import get_assignment_for_equipment

    if get_assignment_for_equipment(session, equipment.id) is not None:
        raise ConflictError("Retire o equipamento do armazenamento antes de excluí-lo")

    archived_at = datetime.now(UTC)
    reason = data.reason.strip()
    equipment.archived_at = archived_at
    equipment.archived_by_user_id = actor.id
    equipment.archive_reason = reason
    session.add(
        EquipmentEvent(
            equipment_id=equipment.id,
            event_type="EQUIPMENT_ARCHIVED",
            previous_status=equipment.current_status,
            new_status=equipment.current_status,
            occurred_at=archived_at,
            user_id=actor.id,
            description=f"Equipamento excluído do inventário ativo. Motivo: {reason}",
            metadata_json={"source": "safe_delete"},
        )
    )
    record_audit(
        session,
        actor_user_id=actor.id,
        action="equipment.archived",
        resource_type="equipment",
        resource_id=str(equipment.id),
        details={"tracking_code": equipment.tracking_code, "reason": reason},
        request_id=request_id,
    )
    session.commit()
    return get_equipment_or_raise(session, equipment.id)


def _create_catalog(
    session: Session,
    model: type[EquipmentCategory] | type[EquipmentType] | type[Sector],
    data: CatalogCreate,
) -> EquipmentCategory | EquipmentType | Sector:
    existing = session.query(model).filter(model.code == data.code).first()
    if existing:
        raise ConflictError("Código de catálogo já cadastrado")
    item = model(
        code=data.code,
        name=data.name.strip(),
        description=normalize_optional(data.description),
    )
    session.add(item)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("Nome ou código de catálogo já cadastrado") from exc
    session.refresh(item)
    return item


def create_category(session: Session, data: CatalogCreate) -> EquipmentCategory:
    item = _create_catalog(session, EquipmentCategory, data)
    assert isinstance(item, EquipmentCategory)
    return item


def create_equipment_type(session: Session, data: CatalogCreate) -> EquipmentType:
    item = _create_catalog(session, EquipmentType, data)
    assert isinstance(item, EquipmentType)
    return item


def create_sector(session: Session, data: CatalogCreate) -> Sector:
    item = _create_catalog(session, Sector, data)
    assert isinstance(item, Sector)
    return item
