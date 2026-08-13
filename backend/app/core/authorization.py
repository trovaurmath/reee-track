from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from app.core.exceptions import AuthorizationError
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.identity.service import user_permissions


def require_permissions(*required_permissions: str) -> Callable[..., User]:
    def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.is_superuser:
            return current_user
        missing = set(required_permissions) - user_permissions(current_user)
        if missing:
            raise AuthorizationError(
                f"Permissões necessárias: {', '.join(sorted(missing))}"
            )
        return current_user

    return dependency

