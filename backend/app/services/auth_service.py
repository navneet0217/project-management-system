from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import Forbidden, Unauthorized
from app.core.security import (
    create_access_token,
    hash_token,
    new_refresh_token,
    verify_password,
)
from app.db.base import utcnow
from app.models import RefreshToken, User
from app.schemas.user import TokenPair


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    # Same message for "no such user" and "wrong password" so attackers can't probe for accounts.
    if not user or not verify_password(password, user.hashed_password):
        raise Unauthorized("Invalid email or password")
    if not user.is_active:
        raise Forbidden("This account has been deactivated")
    return user


def issue_tokens(db: Session, user: User) -> TokenPair:
    raw = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=utcnow() + timedelta(days=settings.REFRESH_TOKEN_DAYS),
        )
    )
    db.commit()
    return TokenPair(access_token=create_access_token(user.id, user.role), refresh_token=raw)


def rotate_refresh_token(db: Session, raw_token: str) -> TokenPair:
    """Each refresh token works once. Presenting an already-used one revokes the whole session."""
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    if not record:
        raise Unauthorized("Invalid refresh token")
    if record.revoked:
        db.execute(update(RefreshToken).where(RefreshToken.user_id == record.user_id).values(revoked=True))
        db.commit()
        raise Unauthorized("Refresh token already used. Please log in again.")
    if record.expires_at < utcnow():
        raise Unauthorized("Refresh token expired. Please log in again.")
    user = db.get(User, record.user_id)
    if not user or not user.is_active:
        raise Unauthorized("Account is not active")
    record.revoked = True
    return issue_tokens(db, user)  # commits both the revoke and the new token


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    if record and not record.revoked:
        record.revoked = True
        db.commit()
