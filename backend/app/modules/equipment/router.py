import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.authorization import require_permissions
from app.core.config import settings
from app.core.database import get_db
from app.modules.equipment import repository, service
from app.modules.equipment.documents import (
    equipment_public_url,
    generate_equipment_label,
    generate_qr_png,
)
from app.modules.equipment.schemas import (
    CatalogCreate,
    CatalogRead,
    EquipmentArchiveRequest,
    EquipmentCreate,
    EquipmentEventRead,
    EquipmentListResponse,
    EquipmentRead,
    EquipmentUpdate,
    TimelineNoteCreate,
    TraceabilityEventRead,
    TraceabilityFeedResponse,
    WorkflowStatusRead,
    WorkflowTransitionRequest,
)
from app.modules.equipment.workflow import STATUS_BY_CODE, manual_transition_options
from app.modules.identity.models import User

catalog_router = APIRouter(prefix="/catalogs", tags=["Catálogos"])
router = APIRouter(prefix="/equipments", tags=["Equipamentos"])
traceability_router = APIRouter(prefix="/traceability", tags=["Rastreabilidade"])


@catalog_router.get("/equipment-categories", response_model=list[CatalogRead])
def get_categories(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
) -> list[CatalogRead]:
    del current_user
    return [service.to_catalog_read(item) for item in repository.list_categories(session)]


@catalog_router.post("/equipment-categories", response_model=CatalogRead, status_code=201)
def post_category(
    data: CatalogCreate,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("configuration:manage"))],
) -> CatalogRead:
    del current_user
    return service.to_catalog_read(service.create_category(session, data))


@catalog_router.get("/equipment-types", response_model=list[CatalogRead])
def get_equipment_types(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
) -> list[CatalogRead]:
    del current_user
    return [service.to_catalog_read(item) for item in repository.list_equipment_types(session)]


@catalog_router.post("/equipment-types", response_model=CatalogRead, status_code=201)
def post_equipment_type(
    data: CatalogCreate,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("configuration:manage"))],
) -> CatalogRead:
    del current_user
    return service.to_catalog_read(service.create_equipment_type(session, data))


@catalog_router.get("/sectors", response_model=list[CatalogRead])
def get_sectors(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
) -> list[CatalogRead]:
    del current_user
    return [service.to_catalog_read(item) for item in repository.list_sectors(session)]


@catalog_router.post("/sectors", response_model=CatalogRead, status_code=201)
def post_sector(
    data: CatalogCreate,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("configuration:manage"))],
) -> CatalogRead:
    del current_user
    return service.to_catalog_read(service.create_sector(session, data))


@router.get("", response_model=EquipmentListResponse)
def get_equipments(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
    query: str | None = None,
    category_id: uuid.UUID | None = None,
    equipment_type_id: uuid.UUID | None = None,
    origin_sector_id: uuid.UUID | None = None,
    status: str | None = None,
    collected_from: datetime | None = None,
    collected_to: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    include_archived: bool = False,
) -> EquipmentListResponse:
    del current_user
    items, total = repository.list_equipments(
        session,
        query=query,
        category_id=category_id,
        equipment_type_id=equipment_type_id,
        origin_sector_id=origin_sector_id,
        status=status,
        collected_from=collected_from,
        collected_to=collected_to,
        limit=limit,
        offset=offset,
        include_archived=include_archived,
    )
    return EquipmentListResponse(
        items=[service.to_equipment_read(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=EquipmentRead, status_code=201)
def post_equipment(
    data: EquipmentCreate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:create"))],
) -> EquipmentRead:
    equipment = service.create_equipment(
        session,
        data,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return service.to_equipment_read(equipment)


@router.get("/by-code/{tracking_code}", response_model=EquipmentRead)
def get_equipment_by_code(
    tracking_code: str,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
) -> EquipmentRead:
    del current_user
    return service.to_equipment_read(
        service.get_equipment_by_code_or_raise(session, tracking_code)
    )


@router.get("/{equipment_id}", response_model=EquipmentRead)
def get_equipment(
    equipment_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
) -> EquipmentRead:
    del current_user
    return service.to_equipment_read(service.get_equipment_or_raise(session, equipment_id))


@router.patch("/{equipment_id}", response_model=EquipmentRead)
def patch_equipment(
    equipment_id: uuid.UUID,
    data: EquipmentUpdate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:update"))],
) -> EquipmentRead:
    equipment = service.update_equipment(
        session,
        equipment_id,
        data,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return service.to_equipment_read(equipment)


@router.delete("/{equipment_id}", response_model=EquipmentRead)
def delete_equipment(
    equipment_id: uuid.UUID,
    data: EquipmentArchiveRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:delete"))],
) -> EquipmentRead:
    return service.to_equipment_read(
        service.archive_equipment(
            session,
            equipment_id,
            data,
            actor=current_user,
            request_id=request.state.request_id,
        )
    )


@router.get("/{equipment_id}/workflow-options", response_model=list[WorkflowStatusRead])
def get_workflow_options(
    equipment_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
) -> list[WorkflowStatusRead]:
    del current_user
    equipment = service.get_equipment_or_raise(session, equipment_id)
    return [
        WorkflowStatusRead(
            code=definition.code,
            label=definition.label,
            stage=definition.stage,
            terminal=definition.terminal,
        )
        for definition in manual_transition_options(equipment.current_status)
    ]


@router.post("/{equipment_id}/transitions", response_model=EquipmentRead)
def post_workflow_transition(
    equipment_id: uuid.UUID,
    data: WorkflowTransitionRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("workflow:transition"))],
) -> EquipmentRead:
    return service.to_equipment_read(
        service.transition_equipment(
            session,
            equipment_id,
            data,
            actor=current_user,
            request_id=request.state.request_id,
        )
    )


@router.post("/{equipment_id}/timeline-notes", response_model=EquipmentEventRead, status_code=201)
def post_timeline_note(
    equipment_id: uuid.UUID,
    data: TimelineNoteCreate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("workflow:transition"))],
) -> EquipmentEventRead:
    event = service.add_timeline_note(
        session,
        equipment_id,
        data,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return EquipmentEventRead(
        id=event.id,
        equipment_id=event.equipment_id,
        event_type=event.event_type,
        previous_status=event.previous_status,
        new_status=event.new_status,
        timestamp=event.occurred_at,
        user_id=event.user_id,
        location=event.location,
        description=event.description,
        metadata=event.metadata_json,
    )


@router.get("/{equipment_id}/timeline", response_model=list[EquipmentEventRead])
def get_timeline(
    equipment_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
) -> list[EquipmentEventRead]:
    del current_user
    service.get_equipment_or_raise(session, equipment_id)
    return [
        EquipmentEventRead(
            id=event.id,
            equipment_id=event.equipment_id,
            event_type=event.event_type,
            previous_status=event.previous_status,
            new_status=event.new_status,
            timestamp=event.occurred_at,
            user_id=event.user_id,
            location=event.location,
            description=event.description,
            metadata=event.metadata_json,
        )
        for event in repository.list_events(session, equipment_id)
    ]


@router.get("/{equipment_id}/qr-code")
def get_qr_code(
    equipment_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
) -> Response:
    del current_user
    equipment = service.get_equipment_or_raise(session, equipment_id)
    content = equipment_public_url(settings.public_frontend_url, equipment.tracking_code)
    return Response(
        content=generate_qr_png(content),
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.get("/{equipment_id}/label")
def get_label(
    equipment_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
) -> Response:
    del current_user
    equipment = service.get_equipment_or_raise(session, equipment_id)
    filename = f"etiqueta-{equipment.tracking_code}.pdf"
    return Response(
        content=generate_equipment_label(equipment, settings.public_frontend_url),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@traceability_router.get("/events", response_model=TraceabilityFeedResponse)
def get_traceability_feed(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
    event_type: str | None = None,
    status: str | None = None,
    query: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TraceabilityFeedResponse:
    del current_user
    rows, total = repository.list_traceability_events(
        session,
        event_type=event_type,
        status=status,
        query=query,
        limit=limit,
        offset=offset,
    )
    items = [
        TraceabilityEventRead(
            id=event.id,
            equipment_id=event.equipment_id,
            event_type=event.event_type,
            previous_status=event.previous_status,
            new_status=event.new_status,
            timestamp=event.occurred_at,
            user_id=event.user_id,
            location=event.location,
            description=event.description,
            metadata=event.metadata_json,
            tracking_code=equipment.tracking_code,
            equipment_description=(
                f"{equipment.equipment_type.name} {equipment.brand} {equipment.model}"
            ),
            status_label=(
                STATUS_BY_CODE[event.new_status].label
                if event.new_status in STATUS_BY_CODE
                else None
            ),
        )
        for event, equipment in rows
    ]
    return TraceabilityFeedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
