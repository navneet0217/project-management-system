from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequest, Conflict, NotFound
from app.core.security import hash_password
from app.models import RefreshToken, Role, User
from app.schemas.user import UserCreate, UserOut, UserUpdate


def list_users(
    db: Session, search: str | None, role: Role | None, is_active: bool | None, page: int, size: int
) -> tuple[list[UserOut], int]:
    stmt = select(User)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(User.full_name.ilike(like) | User.email.ilike(like))
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(User.id.desc()).offset((page - 1) * size).limit(size)).all()
    return [UserOut.model_validate(u) for u in rows], total


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFound("User not found")
    return user


def create_user(db: Session, data: UserCreate) -> User:
    email = data.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise Conflict("A user with this email already exists")
    user = User(
        email=email,
        full_name=data.full_name.strip(),
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    return user


def update_user(db: Session, actor: User, user_id: int, data: UserUpdate) -> User:
    user = get_user(db, user_id)
    changes = data.model_dump(exclude_unset=True)
    if user.id == actor.id:
        # Stops an admin from locking themselves out of the system.
        if changes.get("is_active") is False:
            raise BadRequest("You cannot deactivate your own account")
        if "role" in changes and changes["role"] != Role.ADMIN:
            raise BadRequest("You cannot remove your own admin role")
    if "password" in changes:
        user.hashed_password = hash_password(changes.pop("password"))
    for field, value in changes.items():
        if value is not None:
            setattr(user, field, value)
    if changes.get("is_active") is False:
        db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(revoked=True))
    db.commit()
    return user
