from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Role, User
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserOption, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])
admin_only = require_roles(Role.ADMIN)


@router.get("/options", response_model=list[UserOption])
def user_options(
    role: Role | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
):
    """Small dropdown list (active users). Managers use it to pick developers and managers."""
    stmt = select(User).where(User.is_active.is_(True)).order_by(User.full_name)
    if role:
        stmt = stmt.where(User.role == role)
    return [UserOption.model_validate(u) for u in db.scalars(stmt).all()]


@router.get("", response_model=Page[UserOut])
def list_users(
    search: str | None = Query(None, max_length=100),
    role: Role | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    items, total = user_service.list_users(db, search, role, is_active, page, size)
    return Page[UserOut](items=items, total=total, page=page, size=size)


@router.post("", response_model=UserOut, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return UserOut.model_validate(user_service.create_user(db, data))


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return UserOut.model_validate(user_service.get_user(db, user_id))


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
):
    return UserOut.model_validate(user_service.update_user(db, actor, user_id, data))
