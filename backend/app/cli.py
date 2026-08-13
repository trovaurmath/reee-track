import argparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.equipment.seed import seed_demo_data
from app.modules.identity.models import Permission, Role, User
from app.modules.identity.permissions import PERMISSIONS, ROLE_DEFINITIONS
from app.modules.identity.security import hash_password
from app.modules.storage.seed import seed_storage


def seed_rbac(session: Session) -> None:
    permissions_by_code: dict[str, Permission] = {}
    for definition in PERMISSIONS:
        permission = session.scalar(select(Permission).where(Permission.code == definition.code))
        if permission is None:
            permission = Permission(code=definition.code, name=definition.name)
            session.add(permission)
        else:
            permission.name = definition.name
        permissions_by_code[definition.code] = permission

    session.flush()

    roles_by_code: dict[str, Role] = {}
    for code, definition in ROLE_DEFINITIONS.items():
        role = session.scalar(select(Role).where(Role.code == code))
        if role is None:
            role = Role(code=code, name=str(definition["name"]), is_system=True)
            session.add(role)
        role.name = str(definition["name"])
        role.description = str(definition["description"])
        role.permissions = [
            permissions_by_code[permission_code]
            for permission_code in sorted(definition["permissions"])
        ]
        roles_by_code[code] = role

    session.flush()

    admin_username = settings.initial_admin_username.strip().lower()
    admin = session.scalar(select(User).where(User.username == admin_username))
    if admin is None:
        admin = User(
            username=admin_username,
            email=settings.initial_admin_email.strip().lower(),
            full_name=settings.initial_admin_full_name.strip(),
            password_hash=hash_password(settings.initial_admin_password),
            is_active=True,
            is_superuser=True,
        )
        session.add(admin)

    admin.is_superuser = True
    if roles_by_code["ADMINISTRADOR"] not in admin.roles:
        admin.roles.append(roles_by_code["ADMINISTRADOR"])

    session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="REEE-Track administration commands")
    parser.add_argument("command", choices=["seed-rbac", "seed-demo"])
    args = parser.parse_args()

    with SessionLocal() as session:
        if args.command == "seed-rbac":
            seed_rbac(session)
            print("RBAC e administrador inicial verificados com sucesso.")
        elif args.command == "seed-demo":
            created = seed_demo_data(session)
            storage_created = seed_storage(session)
            print(f"Armazenamento verificado; {storage_created} ocupações demonstrativas criadas.")
            print(f"Catálogos verificados; {created} equipamentos demonstrativos criados.")


if __name__ == "__main__":
    main()
