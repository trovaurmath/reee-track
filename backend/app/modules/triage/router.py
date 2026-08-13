import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.authorization import require_permissions
from app.core.database import get_db
from app.modules.identity.models import User
from app.modules.triage import repository, service
from app.modules.triage.schemas import (
    ClassificationCreate,
    ClassificationRead,
    ClassificationUpdate,
    CriterionCreate,
    CriterionRead,
    CriterionUpdate,
    TriageAnswersUpdate,
    TriageComplete,
    TriageQueueResponse,
    TriageRead,
)

configuration_router = APIRouter(prefix="/triage-config", tags=["Configuração da triagem"])
router = APIRouter(prefix="/triages", tags=["Triagem"])
equipment_router = APIRouter(prefix="/equipments", tags=["Triagem"])


@configuration_router.get("/classifications", response_model=list[ClassificationRead])
def get_classifications(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
    include_inactive: bool = False,
) -> list[ClassificationRead]:
    del current_user
    return [
        service.to_classification_read(item)
        for item in repository.list_classifications(session, active_only=not include_inactive)
    ]


@configuration_router.post("/classifications", response_model=ClassificationRead, status_code=201)
def post_classification(
    data: ClassificationCreate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("configuration:manage"))],
) -> ClassificationRead:
    item = service.create_classification(
        session,
        data,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return service.to_classification_read(item)


@configuration_router.patch(
    "/classifications/{classification_id}",
    response_model=ClassificationRead,
)
def patch_classification(
    classification_id: uuid.UUID,
    data: ClassificationUpdate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("configuration:manage"))],
) -> ClassificationRead:
    item = service.update_classification(
        session,
        classification_id,
        data,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return service.to_classification_read(item)


@configuration_router.get("/criteria", response_model=list[CriterionRead])
def get_criteria(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
    include_inactive: bool = False,
) -> list[CriterionRead]:
    del current_user
    return [
        service.to_criterion_read(item)
        for item in repository.list_criteria(session, active_only=not include_inactive)
    ]


@configuration_router.post("/criteria", response_model=CriterionRead, status_code=201)
def post_criterion(
    data: CriterionCreate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("configuration:manage"))],
) -> CriterionRead:
    item = service.create_criterion(
        session,
        data,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return service.to_criterion_read(item)


@configuration_router.patch("/criteria/{criterion_id}", response_model=CriterionRead)
def patch_criterion(
    criterion_id: uuid.UUID,
    data: CriterionUpdate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("configuration:manage"))],
) -> CriterionRead:
    item = service.update_criterion(
        session,
        criterion_id,
        data,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return service.to_criterion_read(item)


@router.get("/queue", response_model=TriageQueueResponse)
def get_queue(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("triage:execute"))],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TriageQueueResponse:
    del current_user
    return service.get_queue(session, limit=limit, offset=offset)


@router.get("/{triage_id}", response_model=TriageRead)
def get_triage(
    triage_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
) -> TriageRead:
    del current_user
    return service.to_triage_read(service.get_triage_or_raise(session, triage_id))


@router.put("/{triage_id}/answers", response_model=TriageRead)
def put_answers(
    triage_id: uuid.UUID,
    data: TriageAnswersUpdate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("triage:execute"))],
) -> TriageRead:
    triage = service.save_answers(
        session,
        triage_id,
        data,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return service.to_triage_read(triage)


@router.post("/{triage_id}/complete", response_model=TriageRead)
def post_complete_triage(
    triage_id: uuid.UUID,
    data: TriageComplete,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(
            require_permissions(
                "triage:execute",
                "triage:classify",
                "workflow:transition",
            )
        ),
    ],
) -> TriageRead:
    triage = service.complete_triage(
        session,
        triage_id,
        data,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return service.to_triage_read(triage)


@router.post("/{triage_id}/cancel", response_model=TriageRead)
def post_cancel_triage(
    triage_id: uuid.UUID,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permissions("triage:execute", "workflow:transition")),
    ],
) -> TriageRead:
    triage = service.cancel_triage(
        session,
        triage_id,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return service.to_triage_read(triage)


@equipment_router.get("/{tracking_code}/triages", response_model=list[TriageRead])
def get_equipment_triages(
    tracking_code: str,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("equipment:read"))],
) -> list[TriageRead]:
    del current_user
    return [
        service.to_triage_read(item)
        for item in service.get_equipment_triages(session, tracking_code)
    ]


@equipment_router.post("/{tracking_code}/triages", response_model=TriageRead, status_code=201)
def post_equipment_triage(
    tracking_code: str,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permissions("triage:execute", "workflow:transition")),
    ],
) -> TriageRead:
    triage = service.start_triage(
        session,
        tracking_code,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return service.to_triage_read(triage)
