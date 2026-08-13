from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.modules.audit.service import record_audit
from app.modules.identity import repository
from app.modules.identity.models import RefreshSession, User
from app.modules.identity.schemas import TokenResponse, UserCreate, UserRead
from app.modules.identity.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def user_permissions(user: User) -> set[str]:
    return {
        permission.code
        for role in user.roles
        for permission in role.permissions
    }


def to_user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=sorted(role.code for role in user.roles),
        permissions=sorted(user_permissions(user)),
        created_at=user.created_at,
    )


def authenticate(session: Session, username: str, password: str) -> User:
    user = repository.get_user_by_username(session, username)
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("Usuário ou senha inválidos")
    if not user.is_active:
        raise AuthenticationError("Usuário inativo")
    return user


def create_session_tokens(
    session: Session,
    user: User,
    *,
    request_id: str | None = None,
) -> tuple[TokenResponse, str]:
    refresh = create_refresh_token()
    refresh_session = RefreshSession(
        user_id=user.id,
        token_hash=refresh.token_hash,
        expires_at=refresh.expires_at,
        created_at=datetime.now(UTC),
    )
    session.add(refresh_session)
    session.flush()
    record_audit(
        session,
        actor_user_id=user.id,
        action="auth.login",
        resource_type="session",
        resource_id=str(refresh_session.id),
        request_id=request_id,
    )
    session.commit()
    response = TokenResponse(
        access_token=create_access_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
        user=to_user_read(user),
    )
    return response, refresh.raw_token


def rotate_refresh_token(
    session: Session,
    raw_token: str,
    *,
    request_id: str | None = None,
) -> tuple[TokenResponse, str]:
    refresh_session = repository.get_refresh_session(session, hash_refresh_token(raw_token))
    now = datetime.now(UTC)
    if refresh_session is None or refresh_session.revoked_at is not None:
        raise AuthenticationError("Sessão inválida")

    expires_at = refresh_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now or not refresh_session.user.is_active:
        raise AuthenticationError("Sessão expirada")

    refresh_session.revoked_at = now
    new_refresh = create_refresh_token()
    session.add(
        RefreshSession(
            user_id=refresh_session.user_id,
            token_hash=new_refresh.token_hash,
            expires_at=new_refresh.expires_at,
            created_at=now,
        )
    )
    record_audit(
        session,
        actor_user_id=refresh_session.user_id,
        action="auth.refresh",
        resource_type="session",
        resource_id=str(refresh_session.id),
        request_id=request_id,
    )
    session.commit()
    response = TokenResponse(
        access_token=create_access_token(refresh_session.user_id),
        expires_in=settings.access_token_expire_minutes * 60,
        user=to_user_read(refresh_session.user),
    )
    return response, new_refresh.raw_token


def revoke_refresh_token(
    session: Session,
    raw_token: str,
    *,
    request_id: str | None = None,
) -> None:
    refresh_session = repository.get_refresh_session(session, hash_refresh_token(raw_token))
    if refresh_session is None or refresh_session.revoked_at is not None:
        return
    refresh_session.revoked_at = datetime.now(UTC)
    record_audit(
        session,
        actor_user_id=refresh_session.user_id,
        action="auth.logout",
        resource_type="session",
        resource_id=str(refresh_session.id),
        request_id=request_id,
    )
    session.commit()


def create_user(
    session: Session,
    data: UserCreate,
    *,
    actor: User,
    request_id: str | None = None,
) -> User:
    if repository.get_user_by_username(session, data.username):
        raise ConflictError("Nome de usuário já cadastrado")
    if repository.get_user_by_email(session, str(data.email)):
        raise ConflictError("E-mail já cadastrado")

    roles = repository.get_roles_by_codes(session, data.role_codes)
    found_codes = {role.code for role in roles}
    missing_codes = {code.upper() for code in data.role_codes} - found_codes
    if missing_codes:
        raise NotFoundError(f"Papéis não encontrados: {', '.join(sorted(missing_codes))}")

    user = User(
        username=data.username,
        email=str(data.email),
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password),
        roles=roles,
    )
    session.add(user)
    session.flush()
    record_audit(
        session,
        actor_user_id=actor.id,
        action="user.created",
        resource_type="user",
        resource_id=str(user.id),
        details={"username": user.username, "roles": sorted(found_codes)},
        request_id=request_id,
    )
    session.commit()
    return repository.get_user_by_id(session, user.id) or user
