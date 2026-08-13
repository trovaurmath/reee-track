import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError, ConflictError, NotFoundError
from app.modules.audit.service import record_audit
from app.modules.equipment.models import EquipmentEvent
from app.modules.equipment.workflow import (
    TRIAGE_STARTABLE_STATUSES,
    ensure_transition,
    ensure_triage_result_status,
)
from app.modules.identity.models import User
from app.modules.triage import repository
from app.modules.triage.models import (
    Triage,
    TriageAnswer,
    TriageClassification,
    TriageCriterion,
)
from app.modules.triage.schemas import (
    ClassificationCreate,
    ClassificationRead,
    ClassificationUpdate,
    CriterionCreate,
    CriterionRead,
    CriterionUpdate,
    TriageAnswerRead,
    TriageAnswersUpdate,
    TriageComplete,
    TriageQueueItem,
    TriageQueueResponse,
    TriageRead,
)

CHOICE_TYPES = {"SINGLE_CHOICE", "MULTIPLE_CHOICE"}
ANSWER_TYPES = {"BOOLEAN", "TEXT", "NUMBER", *CHOICE_TYPES}


def normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_options(options: list[str]) -> list[str]:
    normalized = [option.strip() for option in options if option.strip()]
    if len(normalized) != len(set(normalized)):
        raise ApplicationError("As opções do critério não podem se repetir")
    return normalized


def _validate_criterion_definition(answer_type: str, options: list[str]) -> tuple[str, list[str]]:
    normalized_type = answer_type.strip().upper()
    if normalized_type not in ANSWER_TYPES:
        raise ApplicationError("Tipo de resposta inválido")
    normalized_options = _normalize_options(options)
    if normalized_type in CHOICE_TYPES and len(normalized_options) < 2:
        raise ApplicationError("Critérios de escolha precisam de pelo menos duas opções")
    if normalized_type not in CHOICE_TYPES and normalized_options:
        raise ApplicationError("Este tipo de resposta não aceita opções")
    return normalized_type, normalized_options


def to_classification_read(item: TriageClassification) -> ClassificationRead:
    return ClassificationRead.model_validate(item)


def to_criterion_read(item: TriageCriterion) -> CriterionRead:
    return CriterionRead(
        id=item.id,
        code=item.code,
        question=item.question,
        help_text=item.help_text,
        answer_type=item.answer_type,
        options=item.options_json,
        is_required=item.is_required,
        display_order=item.display_order,
        is_active=item.is_active,
    )


def to_triage_read(triage: Triage) -> TriageRead:
    return TriageRead(
        id=triage.id,
        equipment_id=triage.equipment_id,
        tracking_code=triage.equipment.tracking_code,
        equipment_description=f"{triage.equipment.brand} {triage.equipment.model}",
        evaluator_user_id=triage.evaluator_user_id,
        evaluator_name=triage.evaluator.full_name,
        status=triage.status,
        classification=(
            to_classification_read(triage.classification) if triage.classification else None
        ),
        technical_opinion=triage.technical_opinion,
        observations=triage.observations,
        defects=triage.defects,
        reusable_components=triage.reusable_components,
        started_at=triage.started_at,
        completed_at=triage.completed_at,
        answers=[
            TriageAnswerRead(
                id=answer.id,
                criterion_id=answer.criterion_id,
                criterion_code=answer.criterion.code,
                question=answer.criterion.question,
                answer_type=answer.criterion.answer_type,
                value=answer.value_json,  # type: ignore[arg-type]
                notes=answer.notes,
            )
            for answer in triage.answers
        ],
    )


def create_classification(
    session: Session,
    data: ClassificationCreate,
    *,
    actor: User,
    request_id: str | None = None,
) -> TriageClassification:
    if repository.get_classification_by_code(session, data.code):
        raise ConflictError("Código de classificação já cadastrado")
    item = TriageClassification(
        code=data.code,
        name=data.name.strip(),
        description=normalize_optional(data.description),
        target_status=ensure_triage_result_status(data.target_status),
        display_order=data.display_order,
    )
    session.add(item)
    session.flush()
    record_audit(
        session,
        actor_user_id=actor.id,
        action="triage.classification_created",
        resource_type="triage_classification",
        resource_id=str(item.id),
        details={"code": item.code, "target_status": item.target_status},
        request_id=request_id,
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("Nome ou código de classificação já cadastrado") from exc
    session.refresh(item)
    return item


def update_classification(
    session: Session,
    classification_id: uuid.UUID,
    data: ClassificationUpdate,
    *,
    actor: User,
    request_id: str | None = None,
) -> TriageClassification:
    item = repository.get_classification(session, classification_id)
    if item is None:
        raise NotFoundError("Classificação não encontrada")
    changes = data.model_dump(exclude_unset=True)
    before: dict[str, object] = {}
    after: dict[str, object] = {}
    for field, value in changes.items():
        if field == "target_status" and value is not None:
            value = ensure_triage_result_status(value)
        if field in {"name", "description"}:
            value = normalize_optional(value)
        before[field] = getattr(item, field)
        setattr(item, field, value)
        after[field] = value
    if before:
        record_audit(
            session,
            actor_user_id=actor.id,
            action="triage.classification_updated",
            resource_type="triage_classification",
            resource_id=str(item.id),
            details={"before": before, "after": after},
            request_id=request_id,
        )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("Nome de classificação já cadastrado") from exc
    session.refresh(item)
    return item


def create_criterion(
    session: Session,
    data: CriterionCreate,
    *,
    actor: User,
    request_id: str | None = None,
) -> TriageCriterion:
    if repository.get_criterion_by_code(session, data.code):
        raise ConflictError("Código de critério já cadastrado")
    answer_type, options = _validate_criterion_definition(data.answer_type, data.options)
    item = TriageCriterion(
        code=data.code,
        question=data.question.strip(),
        help_text=normalize_optional(data.help_text),
        answer_type=answer_type,
        options_json=options,
        is_required=data.is_required,
        display_order=data.display_order,
    )
    session.add(item)
    session.flush()
    record_audit(
        session,
        actor_user_id=actor.id,
        action="triage.criterion_created",
        resource_type="triage_criterion",
        resource_id=str(item.id),
        details={"code": item.code, "answer_type": item.answer_type},
        request_id=request_id,
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("Critério de triagem já cadastrado") from exc
    session.refresh(item)
    return item


def update_criterion(
    session: Session,
    criterion_id: uuid.UUID,
    data: CriterionUpdate,
    *,
    actor: User,
    request_id: str | None = None,
) -> TriageCriterion:
    item = repository.get_criterion(session, criterion_id)
    if item is None:
        raise NotFoundError("Critério de triagem não encontrado")
    changes = data.model_dump(exclude_unset=True)
    answer_type = changes.get("answer_type", item.answer_type)
    options = changes.get("options", item.options_json)
    answer_type, options = _validate_criterion_definition(answer_type, options)
    before = {
        field: (item.options_json if field == "options" else getattr(item, field))
        for field in changes
    }
    if "question" in changes:
        item.question = changes["question"].strip()
    if "help_text" in changes:
        item.help_text = normalize_optional(changes["help_text"])
    if "answer_type" in changes or "options" in changes:
        item.answer_type = answer_type
        item.options_json = options
    for field in ("is_required", "display_order", "is_active"):
        if field in changes:
            setattr(item, field, changes[field])
    after = {
        field: (item.options_json if field == "options" else getattr(item, field))
        for field in changes
    }
    if before:
        record_audit(
            session,
            actor_user_id=actor.id,
            action="triage.criterion_updated",
            resource_type="triage_criterion",
            resource_id=str(item.id),
            details={"before": before, "after": after},
            request_id=request_id,
        )
    session.commit()
    session.refresh(item)
    return item


def get_triage_or_raise(session: Session, triage_id: uuid.UUID) -> Triage:
    session.expire_all()
    triage = repository.get_triage(session, triage_id)
    if triage is None:
        raise NotFoundError("Triagem não encontrada")
    return triage


def start_triage(
    session: Session,
    tracking_code: str,
    *,
    actor: User,
    request_id: str | None = None,
) -> Triage:
    equipment = repository.get_equipment_for_update_by_code(session, tracking_code)
    if equipment is None:
        raise NotFoundError("Equipamento não encontrado")
    active = repository.get_active_triage(session, equipment.id)
    if active:
        return active
    if equipment.current_status not in TRIAGE_STARTABLE_STATUSES:
        raise ApplicationError(
            f"O equipamento não pode iniciar triagem no estado {equipment.current_status}"
        )
    previous, new = ensure_transition(equipment.current_status, "EM_TRIAGEM")
    now = datetime.now(UTC)
    triage = Triage(
        equipment_id=equipment.id,
        evaluator_user_id=actor.id,
        status="IN_PROGRESS",
        started_at=now,
    )
    session.add(triage)
    equipment.current_status = new
    session.flush()
    session.add(
        EquipmentEvent(
            equipment_id=equipment.id,
            event_type="TRIAGE_STARTED",
            previous_status=previous,
            new_status=new,
            occurred_at=now,
            user_id=actor.id,
            location=equipment.origin_sector.name,
            description="Triagem técnica iniciada.",
            metadata_json={"triage_id": str(triage.id)},
        )
    )
    record_audit(
        session,
        actor_user_id=actor.id,
        action="triage.started",
        resource_type="triage",
        resource_id=str(triage.id),
        details={"tracking_code": equipment.tracking_code, "status": new},
        request_id=request_id,
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("Já existe uma triagem em andamento para o equipamento") from exc
    return get_triage_or_raise(session, triage.id)


def _validate_answer(criterion: TriageCriterion, value: object) -> object:
    if criterion.answer_type == "BOOLEAN":
        if type(value) is not bool:
            raise ApplicationError(f"'{criterion.question}' exige resposta Sim ou Não")
    elif criterion.answer_type == "TEXT":
        if not isinstance(value, str) or not value.strip():
            raise ApplicationError(f"'{criterion.question}' exige uma resposta textual")
        value = value.strip()
    elif criterion.answer_type == "NUMBER":
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ApplicationError(f"'{criterion.question}' exige uma resposta numérica")
    elif criterion.answer_type == "SINGLE_CHOICE":
        if not isinstance(value, str) or value not in criterion.options_json:
            raise ApplicationError(f"Resposta inválida para '{criterion.question}'")
    elif criterion.answer_type == "MULTIPLE_CHOICE":
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) and item in criterion.options_json for item in value)
        ):
            raise ApplicationError(f"Resposta inválida para '{criterion.question}'")
        value = list(dict.fromkeys(value))
    else:
        raise ApplicationError("O critério possui um tipo de resposta desconhecido")
    return value


def save_answers(
    session: Session,
    triage_id: uuid.UUID,
    data: TriageAnswersUpdate,
    *,
    actor: User,
    request_id: str | None = None,
) -> Triage:
    triage = repository.get_triage(session, triage_id, for_update=True)
    if triage is None:
        raise NotFoundError("Triagem não encontrada")
    if triage.status != "IN_PROGRESS":
        raise ApplicationError("Somente triagens em andamento podem receber respostas")
    criteria = {
        criterion.id: criterion
        for criterion in repository.list_criteria(session, active_only=False)
    }
    existing = {answer.criterion_id: answer for answer in triage.answers}
    for answer_data in data.answers:
        criterion = criteria.get(answer_data.criterion_id)
        if criterion is None or not criterion.is_active:
            raise NotFoundError("Critério de triagem não encontrado ou inativo")
        value = _validate_answer(criterion, answer_data.value)
        answer = existing.get(criterion.id)
        if answer is None:
            answer = TriageAnswer(
                triage_id=triage.id,
                criterion_id=criterion.id,
                value_json=value,
            )
            session.add(answer)
        else:
            answer.value_json = value
        answer.notes = normalize_optional(answer_data.notes)
    record_audit(
        session,
        actor_user_id=actor.id,
        action="triage.answers_saved",
        resource_type="triage",
        resource_id=str(triage.id),
        details={"answer_count": len(data.answers)},
        request_id=request_id,
    )
    session.commit()
    return get_triage_or_raise(session, triage.id)


def complete_triage(
    session: Session,
    triage_id: uuid.UUID,
    data: TriageComplete,
    *,
    actor: User,
    request_id: str | None = None,
) -> Triage:
    triage = repository.get_triage(session, triage_id, for_update=True)
    if triage is None:
        raise NotFoundError("Triagem não encontrada")
    if triage.status != "IN_PROGRESS":
        raise ApplicationError("A triagem já foi finalizada")
    equipment = repository.get_equipment_for_update(session, triage.equipment_id)
    if equipment is None:
        raise NotFoundError("Equipamento não encontrado")
    classification = repository.get_classification(session, data.classification_id)
    if classification is None or not classification.is_active:
        raise NotFoundError("Classificação não encontrada ou inativa")

    required_ids = {
        criterion.id
        for criterion in repository.list_criteria(session)
        if criterion.is_required
    }
    answered_ids = {answer.criterion_id for answer in triage.answers}
    missing_ids = required_ids - answered_ids
    if missing_ids:
        missing_questions = [
            criterion.question
            for criterion in repository.list_criteria(session)
            if criterion.id in missing_ids
        ]
        raise ApplicationError(
            "Responda aos critérios obrigatórios: " + "; ".join(missing_questions)
        )

    previous, target = ensure_transition(equipment.current_status, classification.target_status)
    now = datetime.now(UTC)
    triage.status = "COMPLETED"
    triage.classification = classification
    triage.technical_opinion = data.technical_opinion.strip()
    triage.observations = normalize_optional(data.observations)
    triage.defects = normalize_optional(data.defects)
    triage.reusable_components = normalize_optional(data.reusable_components)
    triage.completed_at = now
    equipment.current_status = target
    session.add_all(
        (
            EquipmentEvent(
                equipment_id=equipment.id,
                event_type="TRIAGE_COMPLETED",
                previous_status=previous,
                new_status=previous,
                occurred_at=now,
                user_id=actor.id,
                location=equipment.origin_sector.name,
                description="Triagem técnica concluída.",
                metadata_json={
                    "triage_id": str(triage.id),
                    "answer_count": len(triage.answers),
                },
            ),
            EquipmentEvent(
                equipment_id=equipment.id,
                event_type="CLASSIFIED",
                previous_status=previous,
                new_status=target,
                occurred_at=now + timedelta(microseconds=1),
                user_id=actor.id,
                location=equipment.origin_sector.name,
                description=f"Equipamento classificado como {classification.name}.",
                metadata_json={
                    "triage_id": str(triage.id),
                    "classification_code": classification.code,
                },
            ),
        )
    )
    record_audit(
        session,
        actor_user_id=actor.id,
        action="triage.completed",
        resource_type="triage",
        resource_id=str(triage.id),
        details={
            "tracking_code": equipment.tracking_code,
            "classification": classification.code,
            "previous_status": previous,
            "new_status": target,
        },
        request_id=request_id,
    )
    session.commit()
    return get_triage_or_raise(session, triage.id)


def cancel_triage(
    session: Session,
    triage_id: uuid.UUID,
    *,
    actor: User,
    request_id: str | None = None,
) -> Triage:
    triage = repository.get_triage(session, triage_id, for_update=True)
    if triage is None:
        raise NotFoundError("Triagem não encontrada")
    if triage.status != "IN_PROGRESS":
        raise ApplicationError("Somente triagens em andamento podem ser canceladas")
    equipment = repository.get_equipment_for_update(session, triage.equipment_id)
    if equipment is None:
        raise NotFoundError("Equipamento não encontrado")
    previous, target = ensure_transition(equipment.current_status, "AGUARDANDO_TRIAGEM")
    now = datetime.now(UTC)
    triage.status = "CANCELLED"
    triage.completed_at = now
    equipment.current_status = target
    session.add(
        EquipmentEvent(
            equipment_id=equipment.id,
            event_type="TRIAGE_CANCELLED",
            previous_status=previous,
            new_status=target,
            occurred_at=now,
            user_id=actor.id,
            location=equipment.origin_sector.name,
            description="Triagem cancelada; equipamento devolvido à fila.",
            metadata_json={"triage_id": str(triage.id)},
        )
    )
    record_audit(
        session,
        actor_user_id=actor.id,
        action="triage.cancelled",
        resource_type="triage",
        resource_id=str(triage.id),
        details={"tracking_code": equipment.tracking_code},
        request_id=request_id,
    )
    session.commit()
    return get_triage_or_raise(session, triage.id)


def get_equipment_triages(session: Session, tracking_code: str) -> list[Triage]:
    equipment = repository.get_equipment_by_code(session, tracking_code)
    if equipment is None:
        raise NotFoundError("Equipamento não encontrado")
    return repository.list_equipment_triages(session, equipment.id)


def get_queue(session: Session, *, limit: int, offset: int) -> TriageQueueResponse:
    rows, total = repository.list_queue(session, limit=limit, offset=offset)
    return TriageQueueResponse(
        items=[
            TriageQueueItem(
                equipment_id=equipment.id,
                tracking_code=equipment.tracking_code,
                asset_number=equipment.asset_number,
                equipment_description=f"{equipment.brand} {equipment.model}",
                category_name=equipment.category.name,
                origin_sector_name=equipment.origin_sector.name,
                current_status=equipment.current_status,
                collection_date=equipment.collection_date,
                active_triage_id=active.id if active else None,
                evaluator_name=active.evaluator.full_name if active else None,
            )
            for equipment, active in rows
        ],
        total=total,
    )
