import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError, ConflictError, NotFoundError
from app.modules.audit.service import record_audit
from app.modules.equipment.models import EquipmentEvent
from app.modules.equipment.service import (
    _validated_event_time,
    get_equipment_or_raise,
    normalize_optional,
)
from app.modules.identity.models import User
from app.modules.storage import repository
from app.modules.storage.models import StorageAssignment, StorageLocation, StorageMovement
from app.modules.storage.schemas import (
    StorageDashboardRead,
    StorageLocationCreate,
    StorageLocationRead,
    StorageLocationUpdate,
    StorageMovementCreate,
    StorageMovementRead,
    StorageOccupancyRead,
)


def to_location_read(location: StorageLocation, occupied: int) -> StorageLocationRead:
    return StorageLocationRead(
        id=location.id,
        code=location.code,
        warehouse=location.warehouse,
        aisle=location.aisle,
        rack=location.rack,
        shelf=location.shelf,
        position=location.position,
        capacity=location.capacity,
        occupied=occupied,
        available=max(location.capacity - occupied, 0),
        notes=location.notes,
        is_active=location.is_active,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )


def create_location(
    session: Session,
    data: StorageLocationCreate,
    *,
    actor: User,
    request_id: str | None = None,
) -> StorageLocationRead:
    if repository.get_location_by_code(session, data.code):
        raise ConflictError("Código de posição já cadastrado")
    location = StorageLocation(
        code=data.code,
        warehouse=data.warehouse.strip(),
        aisle=normalize_optional(data.aisle),
        rack=normalize_optional(data.rack),
        shelf=normalize_optional(data.shelf),
        position=normalize_optional(data.position),
        capacity=data.capacity,
        notes=normalize_optional(data.notes),
    )
    session.add(location)
    session.flush()
    record_audit(
        session,
        actor_user_id=actor.id,
        action="storage.location_created",
        resource_type="storage_location",
        resource_id=str(location.id),
        details={"code": location.code, "capacity": location.capacity},
        request_id=request_id,
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("Código de posição já cadastrado") from exc
    session.refresh(location)
    return to_location_read(location, 0)


def update_location(
    session: Session,
    location_id: uuid.UUID,
    data: StorageLocationUpdate,
    *,
    actor: User,
    request_id: str | None = None,
) -> StorageLocationRead:
    location = repository.get_location(session, location_id)
    if location is None:
        raise NotFoundError("Posição de armazenamento não encontrada")
    occupied = repository.count_occupancy(session, location.id)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("capacity") is not None and changes["capacity"] < occupied:
        raise ConflictError("A capacidade não pode ser menor que a ocupação atual")
    before = {field: getattr(location, field) for field in changes}
    for field, value in changes.items():
        if field in {"warehouse", "aisle", "rack", "shelf", "position", "notes"}:
            value = normalize_optional(value)
        setattr(location, field, value)
    record_audit(
        session,
        actor_user_id=actor.id,
        action="storage.location_updated",
        resource_type="storage_location",
        resource_id=str(location.id),
        details={"before": before, "after": changes},
        request_id=request_id,
    )
    session.commit()
    session.refresh(location)
    return to_location_read(location, occupied)


def deactivate_location(
    session: Session,
    location_id: uuid.UUID,
    *,
    actor: User,
    request_id: str | None = None,
) -> None:
    location = repository.get_location(session, location_id)
    if location is None:
        raise NotFoundError("Posição de armazenamento não encontrada")
    if repository.count_occupancy(session, location.id):
        raise ConflictError("Não é possível excluir uma posição ocupada")
    location.is_active = False
    record_audit(
        session,
        actor_user_id=actor.id,
        action="storage.location_deactivated",
        resource_type="storage_location",
        resource_id=str(location.id),
        details={"code": location.code},
        request_id=request_id,
    )
    session.commit()


def move_equipment(
    session: Session,
    data: StorageMovementCreate,
    *,
    actor: User,
    request_id: str | None = None,
) -> StorageMovementRead:
    equipment = get_equipment_or_raise(session, data.equipment_id)
    if equipment.archived_at is not None:
        raise ConflictError("Equipamento arquivado não pode ser movimentado")
    assignment = repository.get_assignment_for_equipment(session, equipment.id)
    from_location = (
        repository.get_location(session, assignment.location_id) if assignment else None
    )
    to_location = (
        repository.get_location(session, data.to_location_id) if data.to_location_id else None
    )
    if data.to_location_id and to_location is None:
        raise NotFoundError("Posição de destino não encontrada")
    if to_location and not to_location.is_active:
        raise ConflictError("Posição de destino está inativa")
    if assignment is None and to_location is None:
        raise ApplicationError("Informe uma posição para a entrada no armazenamento")
    if assignment and to_location and assignment.location_id == to_location.id:
        raise ConflictError("O equipamento já está nessa posição")
    if to_location and repository.count_occupancy(session, to_location.id) >= to_location.capacity:
        raise ConflictError("Posição de destino sem capacidade disponível")

    occurred_at = _validated_event_time(data.occurred_at)
    if assignment is None:
        movement_type = "ENTRY"
        assignment = StorageAssignment(
            equipment_id=equipment.id,
            location_id=to_location.id,
            entered_at=occurred_at,
        )
        session.add(assignment)
    elif to_location is None:
        movement_type = "EXIT"
        session.delete(assignment)
    else:
        movement_type = "TRANSFER"
        assignment.location_id = to_location.id
        assignment.entered_at = occurred_at

    movement = StorageMovement(
        equipment_id=equipment.id,
        from_location_id=from_location.id if from_location else None,
        to_location_id=to_location.id if to_location else None,
        movement_type=movement_type,
        occurred_at=occurred_at,
        user_id=actor.id,
        notes=normalize_optional(data.notes),
    )
    session.add(movement)
    if movement_type == "ENTRY":
        description = f"Entrada no armazenamento em {to_location.code}."
    elif movement_type == "TRANSFER":
        description = f"Transferência de {from_location.code} para {to_location.code}."
    else:
        description = f"Saída do armazenamento de {from_location.code}."
    session.add(
        EquipmentEvent(
            equipment_id=equipment.id,
            event_type=f"STORAGE_{movement_type}",
            previous_status=equipment.current_status,
            new_status=equipment.current_status,
            occurred_at=occurred_at,
            user_id=actor.id,
            location=to_location.code if to_location else from_location.code,
            description=description,
            metadata_json={
                "from_location": from_location.code if from_location else None,
                "to_location": to_location.code if to_location else None,
            },
        )
    )
    record_audit(
        session,
        actor_user_id=actor.id,
        action=f"storage.{movement_type.lower()}",
        resource_type="equipment",
        resource_id=str(equipment.id),
        details={
            "tracking_code": equipment.tracking_code,
            "from": from_location.code if from_location else "",
            "to": to_location.code if to_location else "",
        },
        request_id=request_id,
    )
    session.commit()
    session.refresh(movement)
    return StorageMovementRead(
        id=movement.id,
        equipment_id=equipment.id,
        tracking_code=equipment.tracking_code,
        movement_type=movement.movement_type,
        from_location_code=from_location.code if from_location else None,
        to_location_code=to_location.code if to_location else None,
        occurred_at=movement.occurred_at,
        user_id=movement.user_id,
        notes=movement.notes,
    )


def list_occupancy_reads(
    session: Session, *, query: str | None, alert_days: int
) -> list[StorageOccupancyRead]:
    now = datetime.now(UTC)
    items = []
    for assignment, equipment, location in repository.list_occupancies(session, query=query):
        entered_at = assignment.entered_at
        if entered_at.tzinfo is None:
            entered_at = entered_at.replace(tzinfo=UTC)
        dwell_days = max((now - entered_at).days, 0)
        occupied = repository.count_occupancy(session, location.id)
        items.append(
            StorageOccupancyRead(
                assignment_id=assignment.id,
                equipment_id=equipment.id,
                tracking_code=equipment.tracking_code,
                equipment_description=(
                    f"{equipment.equipment_type.name} {equipment.brand} {equipment.model}"
                ),
                current_status=equipment.current_status,
                location=to_location_read(location, occupied),
                entered_at=assignment.entered_at,
                dwell_days=dwell_days,
                alert=dwell_days >= alert_days,
            )
        )
    return items


def dashboard(session: Session, *, alert_days: int) -> StorageDashboardRead:
    rows = repository.list_locations(session, include_inactive=True)
    occupied_total = sum(occupied for _, occupied in rows)
    capacity_total = sum(location.capacity for location, _ in rows if location.is_active)
    alerts = sum(
        item.alert for item in list_occupancy_reads(session, query=None, alert_days=alert_days)
    )
    return StorageDashboardRead(
        locations_total=len(rows),
        locations_active=sum(location.is_active for location, _ in rows),
        capacity_total=capacity_total,
        occupied_total=occupied_total,
        available_total=max(capacity_total - occupied_total, 0),
        dwell_alerts=alerts,
    )
