from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.audit.service import record_audit
from app.modules.equipment.models import (
    Equipment,
    EquipmentCategory,
    EquipmentEvent,
    EquipmentType,
    Sector,
)
from app.modules.equipment.schemas import EquipmentCreate
from app.modules.equipment.service import create_equipment
from app.modules.identity.models import User
from app.modules.triage.seed import seed_triage_catalogs

CATEGORIES = (
    ("COMPUTADORES", "Computadores", "Desktops, notebooks e estações de trabalho."),
    ("PERIFERICOS", "Periféricos", "Monitores, teclados, mouses e acessórios."),
    ("IMPRESSAO", "Impressão", "Impressoras, multifuncionais e scanners."),
    ("ENERGIA", "Energia", "Estabilizadores, nobreaks e fontes."),
    ("OUTROS", "Outros", "Equipamentos não contemplados nas categorias principais."),
)

EQUIPMENT_TYPES = (
    ("DESKTOP", "Desktop"),
    ("NOTEBOOK", "Notebook"),
    ("MONITOR", "Monitor"),
    ("MOUSE", "Mouse"),
    ("TECLADO", "Teclado"),
    ("IMPRESSORA", "Impressora"),
    ("ESTABILIZADOR", "Estabilizador"),
    ("NOBREAK", "Nobreak"),
    ("SCANNER", "Scanner"),
)

SECTORS = (
    ("LAB_INFO", "Laboratório de Informática"),
    ("ADMIN", "Setor Administrativo"),
    ("BIBLIOTECA", "Biblioteca"),
    ("PATRIMONIO", "Setor de Patrimônio"),
    ("MANUTENCAO", "Setor de Manutenção"),
)

DEMO_EQUIPMENTS = (
    ("DESKTOP", "COMPUTADORES", "Dell", "Vostro 200", "AGUARDANDO_TRIAGEM"),
    ("DESKTOP", "COMPUTADORES", "NTC", "Corporate", "SEPARADO_REUTILIZACAO"),
    ("ESTABILIZADOR", "ENERGIA", "SMS", "Revolution Speedy", "ARMAZENADO"),
    ("IMPRESSORA", "IMPRESSAO", "Xerox", "Phaser 3020", "AGUARDANDO_RECICLAGEM"),
    ("IMPRESSORA", "IMPRESSAO", "HP", "LaserJet P1102", "SEPARADO_LEILAO"),
    ("NOTEBOOK", "COMPUTADORES", "Lenovo", "ThinkPad E14", "FINALIZADO"),
    ("MONITOR", "PERIFERICOS", "LG", "Flatron 19M38A", "AGUARDANDO_TRIAGEM"),
    ("MOUSE", "PERIFERICOS", "Logitech", "M90", "FINALIZADO"),
    ("TECLADO", "PERIFERICOS", "Dell", "KB216", "ARMAZENADO"),
    ("NOBREAK", "ENERGIA", "Intelbras", "XNB 1200", "AGUARDANDO_RECICLAGEM"),
    ("DESKTOP", "COMPUTADORES", "HP", "ProDesk 400", "SEPARADO_REUTILIZACAO"),
    ("NOTEBOOK", "COMPUTADORES", "Acer", "Aspire 5", "SEPARADO_LEILAO"),
    ("MONITOR", "PERIFERICOS", "Samsung", "S22F350", "FINALIZADO"),
    ("IMPRESSORA", "IMPRESSAO", "Epson", "L395", "ARMAZENADO"),
    ("SCANNER", "IMPRESSAO", "Canon", "LiDE 300", "AGUARDANDO_TRIAGEM"),
    ("TECLADO", "PERIFERICOS", "Multilaser", "TC193", "AGUARDANDO_RECICLAGEM"),
    ("MOUSE", "PERIFERICOS", "Microsoft", "Basic Optical", "SEPARADO_REUTILIZACAO"),
    ("ESTABILIZADOR", "ENERGIA", "Ragtech", "Side Way", "FINALIZADO"),
    ("DESKTOP", "COMPUTADORES", "Lenovo", "ThinkCentre M70", "SEPARADO_LEILAO"),
    ("MONITOR", "PERIFERICOS", "AOC", "E970SWHNL", "ARMAZENADO"),
)


def seed_catalogs(
    session: Session,
) -> tuple[dict[str, EquipmentCategory], dict[str, EquipmentType], list[Sector]]:
    categories: dict[str, EquipmentCategory] = {}
    for code, name, description in CATEGORIES:
        item = session.scalar(select(EquipmentCategory).where(EquipmentCategory.code == code))
        if item is None:
            item = EquipmentCategory(code=code, name=name, description=description)
            session.add(item)
        categories[code] = item

    equipment_types: dict[str, EquipmentType] = {}
    for code, name in EQUIPMENT_TYPES:
        item = session.scalar(select(EquipmentType).where(EquipmentType.code == code))
        if item is None:
            item = EquipmentType(code=code, name=name)
            session.add(item)
        equipment_types[code] = item

    sectors: list[Sector] = []
    for code, name in SECTORS:
        item = session.scalar(select(Sector).where(Sector.code == code))
        if item is None:
            item = Sector(code=code, name=name)
            session.add(item)
        sectors.append(item)

    session.commit()
    return categories, equipment_types, sectors


def seed_demo_data(session: Session) -> int:
    categories, equipment_types, sectors = seed_catalogs(session)
    seed_triage_catalogs(session)
    if not settings.seed_demo_data:
        return 0

    admin = session.scalar(
        select(User).where(User.username == settings.initial_admin_username.lower())
    )
    if admin is None:
        raise RuntimeError("Execute seed-rbac antes de seed-demo")

    created_count = 0
    now = datetime.now(UTC)
    for index, (type_code, category_code, brand, model, status) in enumerate(DEMO_EQUIPMENTS, 1):
        asset_number = f"DEMO-{index:04d}"
        if session.scalar(select(Equipment).where(Equipment.asset_number == asset_number)):
            continue
        sector = sectors[(index - 1) % len(sectors)]
        equipment = create_equipment(
            session,
            EquipmentCreate(
                asset_number=asset_number,
                serial_number=f"SN-DEMO-{index:06d}",
                equipment_type_id=equipment_types[type_code].id,
                category_id=categories[category_code].id,
                origin_sector_id=sector.id,
                brand=brand,
                model=model,
                description="Registro fictício criado para demonstração.",
                initial_condition="Equipamento usado aguardando avaliação técnica.",
                collection_date=now - timedelta(days=index),
                collection_notes="Dados inteiramente fictícios.",
            ),
            actor=admin,
        )
        if status != "AGUARDANDO_TRIAGEM":
            equipment.current_status = status
            session.add(
                EquipmentEvent(
                    equipment_id=equipment.id,
                    event_type="DEMO_STATUS_ASSIGNED",
                    previous_status="AGUARDANDO_TRIAGEM",
                    new_status=status,
                    occurred_at=now - timedelta(days=max(index - 1, 0)),
                    user_id=admin.id,
                    location=sector.name,
                    description="Estado fictício atribuído pelo seed de demonstração.",
                    metadata_json={"demo": True},
                )
            )
            record_audit(
                session,
                actor_user_id=admin.id,
                action="equipment.demo_status_assigned",
                resource_type="equipment",
                resource_id=str(equipment.id),
                details={"status": status},
            )
            session.commit()
        created_count += 1
    return created_count
