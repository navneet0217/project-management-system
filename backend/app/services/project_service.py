
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequest, Conflict, Forbidden, NotFound
from app.models import (
    ActivityType,
    AuditAction,
    AuditEntity,
    Project,
    ProjectMember,
    ProjectStatus,
    Role,
    Task,
    TaskActivity,
    TaskStatus,
    User,
)
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.schemas.user import UserOption
from app.services import audit_service


def _scope(user: User):
    """One place that decides which projects a user can see (used by lists AND single lookups)."""
    stmt = select(Project)
    if user.role == Role.ADMIN:
        return stmt
    if user.role == Role.MANAGER:
        return stmt.where(Project.manager_id == user.id)
    return stmt.join(ProjectMember, ProjectMember.project_id == Project.id).where(
        ProjectMember.user_id == user.id
    )


def can_manage(user: User, project: Project) -> bool:
    return user.role == Role.ADMIN or (user.role == Role.MANAGER and project.manager_id == user.id)


def get_viewable(db: Session, user: User, project_id: int) -> Project:
    # 404 (not 403) when you can't see it, so people can't discover which project IDs exist.
    stmt = _scope(user).where(Project.id == project_id).options(joinedload(Project.manager))
    project = db.scalars(stmt).unique().one_or_none()
    if not project:
        raise NotFound("Project not found")
    return project


def get_manageable(db: Session, user: User, project_id: int) -> Project:
    project = get_viewable(db, user, project_id)
    if not can_manage(user, project):
        raise Forbidden("Only the project manager or an admin can do this")
    return project


def serialize(db: Session, projects: list[Project]) -> list[ProjectOut]:
    ids = [p.id for p in projects]
    totals: dict[int, int] = {}
    done: dict[int, int] = {}
    members: dict[int, int] = {}
    if ids:
        totals = dict(
            db.execute(
                select(Task.project_id, func.count(Task.id)).where(Task.project_id.in_(ids)).group_by(Task.project_id)
            ).all()
        )
        done = dict(
            db.execute(
                select(Task.project_id, func.count(Task.id))
                .where(Task.project_id.in_(ids), Task.status == TaskStatus.DONE)
                .group_by(Task.project_id)
            ).all()
        )
        members = dict(
            db.execute(
                select(ProjectMember.project_id, func.count(ProjectMember.user_id))
                .where(ProjectMember.project_id.in_(ids))
                .group_by(ProjectMember.project_id)
            ).all()
        )
    result = []
    for p in projects:
        total, finished = totals.get(p.id, 0), done.get(p.id, 0)
        result.append(
            ProjectOut(
                id=p.id,
                name=p.name,
                description=p.description,
                status=p.status,
                start_date=p.start_date,
                end_date=p.end_date,
                manager=UserOption.model_validate(p.manager) if p.manager else None,
                member_count=members.get(p.id, 0),
                total_tasks=total,
                done_tasks=finished,
                completion_percentage=round(finished * 100 / total, 1) if total else 0.0,
                created_at=p.created_at,
            )
        )
    return result


def list_projects(
    db: Session, user: User, search: str | None, status: ProjectStatus | None, page: int, size: int
) -> tuple[list[ProjectOut], int]:
    stmt = _scope(user)
    if search:
        # Matches project name, description or the manager's name (scoping above still applies).
        like = f"%{search.strip()}%"
        manager_ids = select(User.id).where(User.full_name.ilike(like))
        stmt = stmt.where(
            Project.name.ilike(like) | Project.description.ilike(like) | Project.manager_id.in_(manager_ids)
        )
    if status:
        stmt = stmt.where(Project.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        db.scalars(
            stmt.options(joinedload(Project.manager))
            .order_by(Project.created_at.desc(), Project.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        .unique()
        .all()
    )
    return serialize(db, list(rows)), total


def _validate_manager(db: Session, manager_id: int) -> None:
    manager = db.get(User, manager_id)
    if not manager or not manager.is_active or manager.role != Role.MANAGER:
        raise BadRequest("manager_id must be an active user with the MANAGER role")


def create_project(db: Session, user: User, data: ProjectCreate) -> Project:
    if user.role == Role.MANAGER:
        if data.manager_id not in (None, user.id):
            raise Forbidden("Managers can only create projects that they manage themselves")
        manager_id = user.id
    else:
        manager_id = data.manager_id
        if manager_id is not None:
            _validate_manager(db, manager_id)
    project = Project(
        name=data.name.strip(),
        description=data.description,
        status=data.status,
        start_date=data.start_date,
        end_date=data.end_date,
        manager_id=manager_id,
    )
    db.add(project)
    db.commit()
    return get_viewable(db, user, project.id)


def update_project(db: Session, user: User, project_id: int, data: ProjectUpdate) -> Project:
    project = get_manageable(db, user, project_id)
    changes = data.model_dump(exclude_unset=True)
    if "manager_id" in changes:
        if user.role != Role.ADMIN:
            raise Forbidden("Only an admin can change the project manager")
        if changes["manager_id"] is not None:
            _validate_manager(db, changes["manager_id"])
    start = changes.get("start_date", project.start_date)
    end = changes.get("end_date", project.end_date)
    if start and end and end < start:
        raise BadRequest("end_date cannot be before start_date")
    for field, value in changes.items():
        if field in ("name", "status") and value is None:
            continue
        old = getattr(project, field)
        if old == value:
            continue
        if field == "manager_id":  # log the manager's name, not the raw id
            old_user = db.get(User, old) if old else None
            new_user = db.get(User, value) if value else None
            old, new = (old_user.full_name if old_user else None), (new_user.full_name if new_user else None)
            audit_service.record(
                db, project_id=project.id, actor=user, action=AuditAction.PROJECT_UPDATED,
                entity_type=AuditEntity.PROJECT, entity_id=project.id, entity_label=project.name,
                field="manager", old=old, new=new,
            )
        else:
            audit_service.record(
                db, project_id=project.id, actor=user, action=AuditAction.PROJECT_UPDATED,
                entity_type=AuditEntity.PROJECT, entity_id=project.id, entity_label=project.name,
                field=field, old=old, new=value,
            )
        setattr(project, field, value)
    db.commit()
    return get_viewable(db, user, project_id)


def delete_project(db: Session, user: User, project_id: int) -> None:
    project = get_manageable(db, user, project_id)
    open_tasks = db.scalar(
        select(func.count(Task.id)).where(Task.project_id == project.id, Task.status != TaskStatus.DONE)
    )
    if open_tasks:
        # Safeguard: you cannot delete a project that still has unfinished work.
        raise Conflict(f"Project still has {open_tasks} open task(s). Finish or delete them first.")
    db.delete(project)
    db.commit()


def list_members(db: Session, user: User, project_id: int) -> list[UserOption]:
    get_viewable(db, user, project_id)
    users = db.scalars(
        select(User)
        .join(ProjectMember, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
        .order_by(User.full_name)
    ).all()
    return [UserOption.model_validate(u) for u in users]


def add_member(db: Session, user: User, project_id: int, member_id: int) -> list[UserOption]:
    project = get_manageable(db, user, project_id)
    member = db.get(User, member_id)
    if not member:
        raise NotFound("User not found")
    if not member.is_active:
        raise BadRequest("Inactive users cannot be added to a project")
    if member.role != Role.DEVELOPER:
        raise BadRequest("Only developers can be added as project members")
    if db.get(ProjectMember, (project.id, member.id)):
        raise Conflict("User is already a member of this project")
    db.add(ProjectMember(project_id=project.id, user_id=member.id))
    audit_service.record(
        db, project_id=project.id, actor=user, action=AuditAction.MEMBER_ADDED, entity_type=AuditEntity.MEMBER,
        entity_id=member.id, entity_label=member.full_name, target_user_id=member.id,
    )
    db.commit()
    return list_members(db, user, project_id)


def remove_member(db: Session, user: User, project_id: int, member_id: int) -> None:
    project = get_manageable(db, user, project_id)
    link = db.get(ProjectMember, (project.id, member_id))
    if not link:
        raise NotFound("User is not a member of this project")
    # Their tasks in this project become unassigned (and the change is recorded in the timeline).
    tasks = db.scalars(select(Task).where(Task.project_id == project.id, Task.assignee_id == member_id)).all()
    removed = db.get(User, member_id)
    removed_name = removed.full_name if removed else str(member_id)
    for task in tasks:
        task.assignee_id = None
        db.add(
            TaskActivity(
                task_id=task.id,
                user_id=user.id,
                type=ActivityType.ASSIGNEE_CHANGED,
                old_value=removed_name,
                new_value=None,
            )
        )
        audit_service.record(
            db, project_id=project.id, actor=user, action=AuditAction.TASK_REASSIGNED, entity_type=AuditEntity.TASK,
            entity_id=task.id, entity_label=task.title, field="assignee", old=removed_name, new=None,
            comment="Unassigned because the member was removed from the project",
        )
    audit_service.record(
        db, project_id=project.id, actor=user, action=AuditAction.MEMBER_REMOVED, entity_type=AuditEntity.MEMBER,
        entity_id=member_id, entity_label=removed_name, target_user_id=member_id,
    )
    db.delete(link)
    db.commit()


