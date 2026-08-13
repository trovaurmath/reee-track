import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.equipment.models import Equipment
from app.modules.triage.models import (
    Triage,
    TriageAnswer,
    TriageClassification,
    TriageCriterion,
)


def get_classification(
    session: Session,
    classification_id: uuid.UUID,
) -> TriageClassification | None:
    return session.get(TriageClassification, classification_id)


def get_classification_by_code(
    session: Session,
    code: str,
) -> TriageClassification | None:
    return session.scalar(
        select(TriageClassification).where(TriageClassification.code == code.strip().upper())
    )


def list_classifications(
    session: Session,
    *,
    active_only: bool = True,
) -> list[TriageClassification]:
    statement = select(TriageClassification).order_by(
        TriageClassification.display_order,
        TriageClassification.name,
    )
    if active_only:
        statement = statement.where(TriageClassification.is_active.is_(True))
    return list(session.scalars(statement))


def get_criterion(session: Session, criterion_id: uuid.UUID) -> TriageCriterion | None:
    return session.get(TriageCriterion, criterion_id)


def get_criterion_by_code(session: Session, code: str) -> TriageCriterion | None:
    return session.scalar(
        select(TriageCriterion).where(TriageCriterion.code == code.strip().upper())
    )


def list_criteria(session: Session, *, active_only: bool = True) -> list[TriageCriterion]:
    statement = select(TriageCriterion).order_by(
        TriageCriterion.display_order,
        TriageCriterion.question,
    )
    if active_only:
        statement = statement.where(TriageCriterion.is_active.is_(True))
    return list(session.scalars(statement))


def get_equipment_for_update_by_code(
    session: Session,
    tracking_code: str,
) -> Equipment | None:
    statement = (
        select(Equipment)
        .where(Equipment.tracking_code == tracking_code.strip().upper())
        .with_for_update(of=Equipment)
    )
    return session.scalar(statement)


def get_equipment_by_code(session: Session, tracking_code: str) -> Equipment | None:
    return session.scalar(
        select(Equipment).where(Equipment.tracking_code == tracking_code.strip().upper())
    )


def get_equipment_for_update(session: Session, equipment_id: uuid.UUID) -> Equipment | None:
    return session.scalar(
        select(Equipment).where(Equipment.id == equipment_id).with_for_update(of=Equipment)
    )


def _triage_options():
    return (
        joinedload(Triage.equipment),
        joinedload(Triage.evaluator),
        joinedload(Triage.classification),
        selectinload(Triage.answers).joinedload(TriageAnswer.criterion),
    )


def get_triage(
    session: Session,
    triage_id: uuid.UUID,
    *,
    for_update: bool = False,
) -> Triage | None:
    statement = select(Triage).where(Triage.id == triage_id).options(*_triage_options())
    if for_update:
        statement = statement.with_for_update(of=Triage)
    return session.scalar(statement)


def get_active_triage(session: Session, equipment_id: uuid.UUID) -> Triage | None:
    statement = (
        select(Triage)
        .where(Triage.equipment_id == equipment_id, Triage.status == "IN_PROGRESS")
        .options(*_triage_options())
    )
    return session.scalar(statement)


def list_equipment_triages(session: Session, equipment_id: uuid.UUID) -> list[Triage]:
    statement = (
        select(Triage)
        .where(Triage.equipment_id == equipment_id)
        .options(*_triage_options())
        .order_by(Triage.started_at.desc())
    )
    return list(session.scalars(statement).unique())


def list_queue(
    session: Session,
    *,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[tuple[Equipment, Triage | None]], int]:
    queue_statuses = ("AGUARDANDO_TRIAGEM", "AGUARDANDO_AVALIACAO", "EM_TRIAGEM")
    # The MVP queue is intentionally loaded in two queries to remain portable to
    # SQLite tests while keeping the production query bounded by pagination.
    equipments = list(
        session.scalars(
            select(Equipment)
            .where(Equipment.current_status.in_(queue_statuses))
            .order_by(Equipment.collection_date, Equipment.tracking_code)
            .limit(limit)
            .offset(offset)
        ).unique()
    )
    triages_by_equipment = (
        {
            triage.equipment_id: triage
            for triage in session.scalars(
                select(Triage)
                .where(
                    Triage.equipment_id.in_([equipment.id for equipment in equipments]),
                    Triage.status == "IN_PROGRESS",
                )
                .options(joinedload(Triage.evaluator))
            )
        }
        if equipments
        else {}
    )
    total = session.scalar(
        select(func.count())
        .select_from(Equipment)
        .where(Equipment.current_status.in_(queue_statuses))
    ) or 0
    return [(equipment, triages_by_equipment.get(equipment.id)) for equipment in equipments], total
