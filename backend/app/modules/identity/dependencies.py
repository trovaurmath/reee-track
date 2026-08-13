from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.modules.identity.models import User
from app.modules.identity.repository import get_user_by_id
from app.modules.identity.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    user_id = decode_access_token(token)
    user = get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Usuário não encontrado ou inativo")
    return user

