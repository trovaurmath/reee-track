import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.identity.models import Permission, RefreshSession, Role, User


def user_load_options():  # type: ignore[no-untyped-def]
    return (selectinload(User.roles).selectinload(Role.permissions),)


def get_user_by_id(session: Session, user_id: uuid.UUID) -> User | None:
    statement = select(User).where(User.id == user_id).options(*user_load_options())
    return session.scalar(statement)


def get_user_by_username(session: Session, username: str) -> User | None:
    statement = (
        select(User)
        .where(User.username == username.strip().lower())
        .options(*user_load_options())
    )
    return session.scalar(statement)


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email.strip().lower()))


def list_users(session: Session) -> list[User]:
    statement = select(User).options(*user_load_options()).order_by(User.username)
    return list(session.scalars(statement).unique())


def get_roles_by_codes(session: Session, codes: list[str]) -> list[Role]:
    normalized = {code.strip().upper() for code in codes}
    if not normalized:
        return []
    statement = (
        select(Role).where(Role.code.in_(normalized)).options(selectinload(Role.permissions))
    )
    return list(session.scalars(statement).unique())


def list_roles(session: Session) -> list[Role]:
    statement = select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
    return list(session.scalars(statement).unique())


def get_refresh_session(session: Session, token_hash: str) -> RefreshSession | None:
    statement = (
        select(RefreshSession)
        .where(RefreshSession.token_hash == token_hash)
        .options(selectinload(RefreshSession.user).selectinload(User.roles).selectinload(Role.permissions))
    )
    return session.scalar(statement)


def get_permission_by_code(session: Session, code: str) -> Permission | None:
    return session.scalar(select(Permission).where(Permission.code == code))
