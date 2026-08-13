from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.authorization import require_permissions
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.modules.identity import repository, service
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.identity.schemas import RoleRead, TokenResponse, UserCreate, UserRead

router = APIRouter(tags=["Identidade"])


def set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key="reee_refresh_token",
        value=raw_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        path=f"{settings.api_v1_prefix}/auth",
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user = service.authenticate(session, form_data.username, form_data.password)
    token_response, refresh_token = service.create_session_tokens(
        session,
        user,
        request_id=request.state.request_id,
    )
    set_refresh_cookie(response, refresh_token)
    return token_response


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, session: Annotated[Session, Depends(get_db)]):
    raw_token = request.cookies.get("reee_refresh_token")
    if not raw_token:
        raise AuthenticationError("Refresh token não informado")
    token_response, new_refresh_token = service.rotate_refresh_token(
        session,
        raw_token,
        request_id=request.state.request_id,
    )
    set_refresh_cookie(response, new_refresh_token)
    return token_response


@router.post("/auth/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
) -> None:
    raw_token = request.cookies.get("reee_refresh_token")
    if raw_token:
        service.revoke_refresh_token(
            session,
            raw_token,
            request_id=request.state.request_id,
        )
    response.delete_cookie(key="reee_refresh_token", path=f"{settings.api_v1_prefix}/auth")


@router.get("/auth/me", response_model=UserRead)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return service.to_user_read(current_user)


@router.get("/users", response_model=list[UserRead])
def get_users(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("user:read"))],
) -> list[UserRead]:
    del current_user
    return [service.to_user_read(user) for user in repository.list_users(session)]


@router.post("/users", response_model=UserRead, status_code=201)
def post_user(
    data: UserCreate,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("user:create"))],
) -> UserRead:
    user = service.create_user(
        session,
        data,
        actor=current_user,
        request_id=request.state.request_id,
    )
    return service.to_user_read(user)


@router.get("/roles", response_model=list[RoleRead])
def get_roles(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("user:read"))],
) -> list[RoleRead]:
    del current_user
    return [
        RoleRead(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
            permissions=sorted(permission.code for permission in role.permissions),
        )
        for role in repository.list_roles(session)
    ]
