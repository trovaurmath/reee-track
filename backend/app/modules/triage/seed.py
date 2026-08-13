from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.triage.models import TriageClassification, TriageCriterion

CLASSIFICATIONS = (
    (
        "REUTILIZAVEL",
        "Reutilizável",
        "Equipamento ou conjunto funcional apto a novo uso.",
        "SEPARADO_REUTILIZACAO",
        10,
    ),
    (
        "RECICLAVEL",
        "Reciclável",
        "Equipamento recomendado para desmontagem ou reciclagem.",
        "AGUARDANDO_RECICLAGEM",
        20,
    ),
    (
        "INUTILIZAVEL",
        "Inutilizável",
        "Equipamento sem viabilidade técnica de uso ou recuperação.",
        "AGUARDANDO_DESTINACAO",
        30,
    ),
    (
        "AGUARDANDO_AVALIACAO",
        "Aguardando avaliação",
        "A análise atual não foi suficiente para uma decisão conclusiva.",
        "AGUARDANDO_AVALIACAO",
        40,
    ),
)

CRITERIA = (
    ("POWERS_ON", "O equipamento liga?", "BOOLEAN", 10),
    ("IS_FUNCTIONAL", "O equipamento está funcional?", "BOOLEAN", 20),
    ("HAS_DEFECT", "O equipamento possui defeito?", "BOOLEAN", 30),
    ("DEFECT_REPAIRABLE", "O defeito é reparável?", "BOOLEAN", 40),
    ("CAN_BE_REUSED", "O equipamento pode ser reutilizado?", "BOOLEAN", 50),
    (
        "HAS_REUSABLE_COMPONENTS",
        "Possui componentes reaproveitáveis?",
        "BOOLEAN",
        60,
    ),
    ("AUCTION_ELIGIBLE", "Pode ser encaminhado para leilão?", "BOOLEAN", 70),
    (
        "RECYCLE_RECOMMENDED",
        "Deve ser encaminhado para reciclagem?",
        "BOOLEAN",
        80,
    ),
)


def seed_triage_catalogs(session: Session) -> tuple[int, int]:
    classifications_created = 0
    for code, name, description, target_status, display_order in CLASSIFICATIONS:
        item = session.scalar(
            select(TriageClassification).where(TriageClassification.code == code)
        )
        if item is None:
            session.add(
                TriageClassification(
                    code=code,
                    name=name,
                    description=description,
                    target_status=target_status,
                    display_order=display_order,
                )
            )
            classifications_created += 1

    criteria_created = 0
    for code, question, answer_type, display_order in CRITERIA:
        item = session.scalar(select(TriageCriterion).where(TriageCriterion.code == code))
        if item is None:
            session.add(
                TriageCriterion(
                    code=code,
                    question=question,
                    answer_type=answer_type,
                    options_json=[],
                    is_required=True,
                    display_order=display_order,
                )
            )
            criteria_created += 1

    session.commit()
    return classifications_created, criteria_created
