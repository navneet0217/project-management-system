from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequest, Forbidden, Unauthorized
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    new_refresh_token,
    verify_password,
)
from app.db.base import utcnow
from app.models import AuthToken, RefreshToken, TokenPurpose, User
from app.schemas.user import TokenPair
from app.services import email_service


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    # Same message for "no such user" and "wrong password" so attackers can't probe for accounts.
    if not user or not verify_password(password, user.hashed_password):
        raise Unauthorized("Invalid email or password")
    if not user.is_active:
        raise Forbidden("This account has been deactivated")
    # Checked after the password so the message cannot be used to discover which emails are registered.
    if not user.email_verified_at:
        raise Forbidden("Please verify your email address first. Check your inbox for the link.")
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

# ---------- emailed one-time tokens: verify email, reset password ----------


def _issue_token(db: Session, user: User, purpose: TokenPurpose, ttl: timedelta) -> str:
    """Create a fresh token and cancel older unused ones of the same kind. Returns the raw token (emailed, never stored)."""
    now = utcnow()
    db.execute(
        update(AuthToken)
        .where(AuthToken.user_id == user.id, AuthToken.purpose == purpose, AuthToken.used_at.is_(None))
        .values(used_at=now)
    )
    raw = new_refresh_token()  # 256-bit random, URL safe
    db.add(AuthToken(user_id=user.id, purpose=purpose, token_hash=hash_token(raw), expires_at=now + ttl))
    return raw


def _consume_token(db: Session, raw: str, purpose: TokenPurpose) -> User:
    record = db.scalar(select(AuthToken).where(AuthToken.token_hash == hash_token(raw), AuthToken.purpose == purpose))
    # One generic message for unknown / used / expired, so a guesser learns nothing.
    if not record or record.used_at or record.expires_at < utcnow():
        raise BadRequest("This link is invalid or has expired. Please request a new one.")
    user = db.get(User, record.user_id)
    if not user or user.deleted_at:
        raise BadRequest("This link is invalid or has expired. Please request a new one.")
    record.used_at = utcnow()
    return user


def send_verification(db: Session, user: User) -> None:
    raw = _issue_token(db, user, TokenPurpose.VERIFY_EMAIL, timedelta(hours=settings.VERIFY_TOKEN_HOURS))
    db.commit()
    email_service.send(email_service.verification_email(user.email, user.full_name, raw))


def resend_verification(db: Session, email: str) -> None:
    """Always looks the same from outside (no account enumeration)."""
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user and user.is_active and not user.deleted_at and not user.email_verified_at:
        send_verification(db, user)


def verify_email(db: Session, raw_token: str) -> None:
    user = _consume_token(db, raw_token, TokenPurpose.VERIFY_EMAIL)
    if not user.email_verified_at:
        user.email_verified_at = utcnow()
    db.commit()


def forgot_password(db: Session, email: str) -> None:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or not user.is_active or user.deleted_at:
        return  # same response either way
    raw = _issue_token(db, user, TokenPurpose.RESET_PASSWORD, timedelta(minutes=settings.RESET_TOKEN_MINUTES))
    db.commit()
    email_service.send(email_service.password_reset_email(user.email, user.full_name, raw))


def reset_password(db: Session, raw_token: str, new_password: str) -> None:
    user = _consume_token(db, raw_token, TokenPurpose.RESET_PASSWORD)
    user.hashed_password = hash_password(new_password)
    if not user.email_verified_at:
        user.email_verified_at = utcnow()  # they just proved they control this inbox
    # End every existing session (refresh tokens). Access tokens expire on their own within minutes.
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(revoked=True))
    db.commit()