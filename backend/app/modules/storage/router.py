import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.authorization import require_permissions
from app.core.database import get_db
from app.modules.identity.models import User
from app.modules.storage import repository, service
from app.modules.storage.schemas import (
    StorageDashboardRead,
    StorageLocationCreate,
    StorageLocationRead,
    StorageLocationUpdate,
    StorageMovementCreate,
    StorageMovementRead,
    StorageOccupancyRead,
)

router = APIRouter(prefix="/storage", tags=["Armazenamento"])


@router.get("/dashboard", response_model=StorageDashboardRead)
def get_dashboard(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
    alert_days: Annotated[int, Query(ge=1, le=3650)] = 30,
) -> StorageDashboardRead:
    del current_user
    return service.dashboard(session, alert_days=alert_days)


@router.get("/locations", response_model=list[StorageLocationRead])
def get_locations(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
    query: str | None = None,
    include_inactive: bool = False,
) -> list[StorageLocationRead]:
    del current_user
    return [
        service.to_location_read(location, occupied)
        for location, occupied in repository.list_locations(
            session, query=query, include_inactive=include_inactive
        )
    ]


@router.post("/locations", response_model=StorageLocationRead, status_code=201)
def post_location(
    data: StorageLocationCreate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("storage:manage"))],
) -> StorageLocationRead:
    return service.create_location(
        session, data, actor=current_user, request_id=request.state.request_id
    )


@router.patch("/locations/{location_id}", response_model=StorageLocationRead)
def patch_location(
    location_id: uuid.UUID,
    data: StorageLocationUpdate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("storage:manage"))],
) -> StorageLocationRead:
    return service.update_location(
        session,
        location_id,
        data,
        actor=current_user,
        request_id=request.state.request_id,
    )


@router.delete("/locations/{location_id}", status_code=204)
def delete_location(
    location_id: uuid.UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("storage:manage"))],
) -> Response:
    service.deactivate_location(
        session,
        location_id,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return Response(status_code=204)


@router.get("/occupancies", response_model=list[StorageOccupancyRead])
def get_occupancies(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
    query: str | None = None,
    alert_days: Annotated[int, Query(ge=1, le=3650)] = 30,
) -> list[StorageOccupancyRead]:
    del current_user
    return service.list_occupancy_reads(session, query=query, alert_days=alert_days)


@router.get("/movements", response_model=list[StorageMovementRead])
def get_movements(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[StorageMovementRead]:
    del current_user
    return [
        StorageMovementRead(
            id=movement.id,
            equipment_id=movement.equipment_id,
            tracking_code=equipment.tracking_code,
            movement_type=movement.movement_type,
            from_location_code=from_code,
            to_location_code=to_code,
            occurred_at=movement.occurred_at,
            user_id=movement.user_id,
            notes=movement.notes,
        )
        for movement, equipment, from_code, to_code in repository.list_movements(
            session, limit=limit
        )
    ]


@router.post("/movements", response_model=StorageMovementRead, status_code=201)
def post_movement(
    data: StorageMovementCreate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("storage:manage"))],
) -> StorageMovementRead:
    return service.move_equipment(
        session, data, actor=current_user, request_id=request.state.request_id
    )
