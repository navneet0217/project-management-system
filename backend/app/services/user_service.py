from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequest, Conflict, NotFound
from app.core.security import hash_password
from app.db.base import utcnow
from app.models import Project, ProjectMember, ProjectStatus, RefreshToken, Role, User
from app.schemas.user import ProjectRef, UserCreate, UserListItem, UserOption, UserUpdate

SORT_COLUMNS = {
    "full_name": User.full_name,
    "email": User.email,
    "role": User.role,
    "is_active": User.is_active,
    "created_at": User.created_at,
}


def project_allocations(
    db: Session, user_ids: list[int]
) -> tuple[dict[int, list[ProjectRef]], dict[int, list[UserOption]]]:
    """Current (not completed) projects per user (member or manager) and, for members, who manages them."""
    result: dict[int, list[ProjectRef]] = {uid: [] for uid in user_ids}
    managers: dict[int, dict[int, UserOption]] = {uid: {} for uid in user_ids}
    if not user_ids:
        return result, {}
    as_member = db.execute(
        select(ProjectMember.user_id, Project)
        .join(Project, Project.id == ProjectMember.project_id)
        .where(ProjectMember.user_id.in_(user_ids), Project.status != ProjectStatus.COMPLETED)
        .options(joinedload(Project.manager))
        .order_by(Project.name)
    ).unique().all()
    for uid, project in as_member:
        result[uid].append(ProjectRef.model_validate(project))
        if project.manager:
            managers[uid][project.manager.id] = UserOption.model_validate(project.manager)
    managed = db.scalars(
        select(Project)
        .where(Project.manager_id.in_(user_ids), Project.status != ProjectStatus.COMPLETED)
        .order_by(Project.name)
    ).all()
    for project in managed:
        result[project.manager_id].append(ProjectRef.model_validate(project))
    return result, {uid: list(m.values()) for uid, m in managers.items()}


def list_users(
    db: Session,
    search: str | None,
    role: Role | None,
    is_active: bool | None,
    removed: bool,
    sort_by: str,
    order: str,
    page: int,
    size: int,
) -> tuple[list[UserListItem], int]:
    if sort_by not in SORT_COLUMNS:
        raise BadRequest(f"sort_by must be one of: {', '.join(sorted(SORT_COLUMNS))}")
    # removed (soft-deleted) users are hidden unless the admin explicitly opens the "Removed" view
    stmt = select(User).where(User.deleted_at.is_not(None) if removed else User.deleted_at.is_(None))
    if search:
        like = f"%{search}%"
        stmt = stmt.where(User.full_name.ilike(like) | User.email.ilike(like))
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    column = SORT_COLUMNS[sort_by]
    ordering = column.desc() if order == "desc" else column.asc()
    rows = db.scalars(stmt.order_by(ordering, User.id.desc()).offset((page - 1) * size).limit(size)).all()
    allocations, managers = project_allocations(db, [u.id for u in rows])
    items = [
        UserListItem.model_validate(u).model_copy(
            update={"projects": allocations[u.id], "managers": managers.get(u.id, [])}
        )
        for u in rows
    ]
    return items, total


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFound("User not found")
    return user


def create_user(db: Session, data: UserCreate, verified: bool = True) -> User:
    email = data.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise Conflict("A user with this email already exists")
    user = User(
        email=email,
        full_name=data.full_name.strip(),
        hashed_password=hash_password(data.password),
        role=data.role,
        email_verified_at=utcnow() if verified else None,  # admin-created accounts are trusted
    )
    db.add(user)
    db.commit()
    return user


def update_user(db: Session, actor: User, user_id: int, data: UserUpdate) -> User:
    user = get_user(db, user_id)
    changes = data.model_dump(exclude_unset=True)
    if user.deleted_at and changes.get("is_active"):
        raise BadRequest("This user was removed. Restore them first.")
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

def remove_user(db: Session, actor: User, user_id: int) -> None:
    """Soft remove: deactivate, hide from lists and end all sessions. History (tasks, activity) is kept."""
    user = get_user(db, user_id)
    if user.id == actor.id:
        raise BadRequest("You cannot remove your own account")
    if user.deleted_at:
        return  # already removed
    open_projects = db.scalar(
        select(func.count(Project.id)).where(Project.manager_id == user.id, Project.status != ProjectStatus.COMPLETED)
    )
    if open_projects:
        raise Conflict(f"This user manages {open_projects} active project(s). Reassign them first.")
    user.is_active = False
    user.deleted_at = utcnow()
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(revoked=True))
    db.commit()


def restore_user(db: Session, user_id: int) -> User:
    """Bring a removed user back. They stay inactive until an admin activates them."""
    user = get_user(db, user_id)
    if user.deleted_at:
        user.deleted_at = None
        db.commit()
    return user