import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import Forbidden, Unauthorized
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Role, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise Unauthorized("Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise Unauthorized("Invalid or expired token") from None
    user = db.get(User, user_id)
    # Re-checked on every request, so deactivating a user takes effect immediately.
    if not user or not user.is_active or user.deleted_at:
        raise Unauthorized("Account not found or deactivated")
    return user


def require_roles(*roles: Role):
    """Dependency factory: `Depends(require_roles(Role.ADMIN))` blocks everyone else with 403."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if not any(user.has_role(role) for role in roles):
            raise Forbidden()
        return user

    return checker
