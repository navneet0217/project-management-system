from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequest, Forbidden, NotFound
from app.models import (
    ActivityType,
    AuditAction,
    AuditEntity,
    Priority,
    Project,
    ProjectMember,
    Role,
    Task,
    TaskActivity,
    TaskComment,
    TaskStatus,
    User,
)
from app.schemas.task import (
    ActivityOut,
    CommentOut,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)
from app.services import audit_service, project_service

SORT_FIELDS = {"created_at", "deadline", "priority", "status", "title"}
_PRIORITY_RANK = case(
    (Task.priority == Priority.LOW, 1),
    (Task.priority == Priority.MEDIUM, 2),
    (Task.priority == Priority.HIGH, 3),
    else_=4,
)
_STATUS_RANK = case(
    (Task.status == TaskStatus.TODO, 1),
    (Task.status == TaskStatus.IN_PROGRESS, 2),
    (Task.status == TaskStatus.IN_REVIEW, 3),
    else_=4,
)


def _log(db: Session, task: Task, actor: User, kind: ActivityType, old: str | None, new: str | None) -> None:
    db.add(TaskActivity(task_id=task.id, user_id=actor.id, type=kind, old_value=old, new_value=new))


def _validate_assignee(db: Session, project: Project, assignee_id: int | None) -> User | None:
    if assignee_id is None:
        return None
    assignee = db.get(User, assignee_id)
    if not assignee or not assignee.is_active or assignee.role != Role.DEVELOPER:
        raise BadRequest("Assignee must be an active developer")
    if not db.get(ProjectMember, (project.id, assignee.id)):
        raise BadRequest("Assignee must be a member of this project")
    return assignee


def _load(db: Session, task_id: int) -> Task:
    # populate_existing: always show fresh data, even if this Task object was already loaded
    # earlier in the same request (otherwise a just-changed assignee would still look old).
    stmt = (
        select(Task)
        .where(Task.id == task_id)
        .options(joinedload(Task.assignee), joinedload(Task.project))
        .execution_options(populate_existing=True)
    )
    task = db.scalars(stmt).unique().one_or_none()
    if not task:
        raise NotFound("Task not found")
    return task


def get_task_for_view(db: Session, user: User, task_id: int) -> tuple[Task, Project]:
    task = _load(db, task_id)
    project = project_service.get_viewable(db, user, task.project_id)  # 404 if no access
    return task, project


def list_tasks(
    db: Session,
    user: User,
    project_id: int,
    *,
    status: TaskStatus | None,
    priority: Priority | None,
    assignee_id: int | None,
    search: str | None,
    sort_by: str,
    order: str,
    page: int,
    size: int,
) -> tuple[list[TaskOut], int]:
    project_service.get_viewable(db, user, project_id)
    return _query_tasks(db, [Task.project_id == project_id], status, priority, assignee_id, search, sort_by, order, page, size)


def my_tasks(
    db: Session,
    user: User,
    status: TaskStatus | None,
    priority: Priority | None,
    search: str | None,
    sort_by: str,
    order: str,
    page: int,
    size: int,
) -> tuple[list[TaskOut], int]:
    return _query_tasks(db, [Task.assignee_id == user.id], status, priority, None, search, sort_by, order, page, size)


def task_scope(user: User) -> list:
    """Which tasks a user can see across all projects (the dashboard uses the same rule)."""
    if user.role == Role.ADMIN:
        return []
    if user.role == Role.MANAGER:
        return [Task.project_id.in_(select(Project.id).where(Project.manager_id == user.id))]
    return [Task.assignee_id == user.id]


def visible_tasks(
    db: Session,
    user: User,
    *,
    status: TaskStatus | None,
    priority: Priority | None,
    search: str | None,
    sort_by: str,
    order: str,
    page: int,
    size: int,
) -> tuple[list[TaskOut], int]:
    return _query_tasks(db, task_scope(user), status, priority, None, search, sort_by, order, page, size)


def _query_tasks(db, conditions, status, priority, assignee_id, search, sort_by, order, page, size):
    stmt = select(Task).where(*conditions)
    if status:
        stmt = stmt.where(Task.status == status)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    if assignee_id:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if search:
        stmt = stmt.where(Task.title.ilike(f"%{search}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    if sort_by not in SORT_FIELDS:
        raise BadRequest(f"sort_by must be one of: {', '.join(sorted(SORT_FIELDS))}")
    column = {
        "priority": _PRIORITY_RANK,
        "status": _STATUS_RANK,
        "created_at": Task.created_at,
        "deadline": Task.deadline,
        "title": Task.title,
    }[sort_by]
    ordering = column.desc() if order == "desc" else column.asc()
    rows = (
        db.scalars(
            stmt.options(joinedload(Task.assignee), joinedload(Task.project))
            .order_by(ordering, Task.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        .unique()
        .all()
    )
    return [TaskOut.model_validate(t) for t in rows], total


def _is_owner(user: User, task: Task) -> bool:
    """A developer 'owns' the tasks assigned to them."""
    return user.role == Role.DEVELOPER and task.assignee_id == user.id


def create_task(db: Session, user: User, project_id: int, data: TaskCreate) -> TaskOut:
    if user.role == Role.DEVELOPER:
        # Developers create tasks for themselves, in projects they are a member of (404 otherwise).
        project = project_service.get_viewable(db, user, project_id)
        if data.assignee_id not in (None, user.id):
            raise Forbidden("You can only create tasks assigned to yourself")
        assignee_id = user.id
    else:
        project = project_service.get_manageable(db, user, project_id)
        _validate_assignee(db, project, data.assignee_id)
        assignee_id = data.assignee_id
    task = Task(
        project_id=project.id,
        title=data.title.strip(),
        description=data.description,
        priority=data.priority,
        deadline=data.deadline,
        assignee_id=assignee_id,
        created_by=user.id,
    )
    db.add(task)
    db.flush()
    _log(db, task, user, ActivityType.CREATED, None, task.title)
    audit_service.record(
        db, project_id=project.id, actor=user, action=AuditAction.TASK_CREATED, entity_type=AuditEntity.TASK,
        entity_id=task.id, entity_label=task.title, new=task.title,
    )
    if assignee_id:
        assignee = db.get(User, assignee_id)
        audit_service.record(
            db, project_id=project.id, actor=user, action=AuditAction.TASK_ASSIGNED, entity_type=AuditEntity.TASK,
            entity_id=task.id, entity_label=task.title, field="assignee", new=assignee.full_name if assignee else None,
            target_user_id=assignee_id,
        )
    db.commit()
    return TaskOut.model_validate(_load(db, task.id))


def update_task(db: Session, user: User, task_id: int, data: TaskUpdate) -> TaskOut:
    task, project = get_task_for_view(db, user, task_id)
    manager = project_service.can_manage(user, project)
    if not (manager or _is_owner(user, task)):
        raise Forbidden("Only the project manager, an admin or the task's assignee can edit task details")
    changes = data.model_dump(exclude_unset=True)
    if not manager and "assignee_id" in changes and changes["assignee_id"] != task.assignee_id:
        raise Forbidden("Only the project manager or an admin can change the assignee")

    def audit(action: AuditAction, **kw) -> None:
        audit_service.record(
            db, project_id=project.id, actor=user, action=action, entity_type=AuditEntity.TASK,
            entity_id=task.id, entity_label=task.title, **kw,
        )

    if "assignee_id" in changes and changes["assignee_id"] != task.assignee_id:
        new_assignee = _validate_assignee(db, project, changes["assignee_id"])
        old_name = task.assignee.full_name if task.assignee else None
        new_name = new_assignee.full_name if new_assignee else None
        _log(db, task, user, ActivityType.ASSIGNEE_CHANGED, old_name, new_name)
        audit(
            AuditAction.TASK_ASSIGNED if old_name is None else AuditAction.TASK_REASSIGNED,
            field="assignee", old=old_name, new=new_name, target_user_id=changes["assignee_id"],
        )
        task.assignee_id = changes["assignee_id"]
    for field in ("title", "description", "priority", "deadline"):
        if field not in changes or (field in ("title", "priority") and changes[field] is None):
            continue
        old, new = getattr(task, field), changes[field]
        if old == new:
            continue
        if field == "priority":
            audit(AuditAction.TASK_PRIORITY_CHANGED, field=field, old=old, new=new)
        else:
            audit(AuditAction.TASK_UPDATED, field=field, old=old, new=new)
        setattr(task, field, new)
    db.commit()
    return TaskOut.model_validate(_load(db, task.id))


def change_status(db: Session, user: User, task_id: int, status: TaskStatus) -> TaskOut:
    task, project = get_task_for_view(db, user, task_id)
    is_assignee = task.assignee_id == user.id
    if not (project_service.can_manage(user, project) or is_assignee):
        raise Forbidden("You can only change the status of tasks assigned to you")
    if task.status != status:
        _log(db, task, user, ActivityType.STATUS_CHANGED, task.status.value, status.value)
        audit_service.record(
            db, project_id=project.id, actor=user, action=AuditAction.TASK_STATUS_CHANGED,
            entity_type=AuditEntity.TASK, entity_id=task.id, entity_label=task.title,
            field="status", old=task.status, new=status,
        )
        task.status = status
        db.commit()
    return TaskOut.model_validate(_load(db, task.id))


def delete_task(db: Session, user: User, task_id: int, reason: str) -> None:
    task, project = get_task_for_view(db, user, task_id)
    # Managers/admins can delete any task in their project. A developer may only delete a task
    # that is assigned to them AND that they created themselves (not work handed to them by a manager).
    allowed = project_service.can_manage(user, project) or (_is_owner(user, task) and task.created_by == user.id)
    if not allowed:
        raise Forbidden("You are not allowed to delete this task")
    audit_service.record(
        db, project_id=project.id, actor=user, action=AuditAction.TASK_DELETED, entity_type=AuditEntity.TASK,
        entity_id=task.id, entity_label=task.title, comment=reason.strip(),
    )
    db.delete(task)
    db.commit()


def add_comment(db: Session, user: User, task_id: int, body: str) -> CommentOut:
    task, project = get_task_for_view(db, user, task_id)
    comment = TaskComment(task_id=task.id, user_id=user.id, body=body.strip())
    db.add(comment)
    db.flush()
    audit_service.record(
        db, project_id=project.id, actor=user, action=AuditAction.COMMENT_ADDED, entity_type=AuditEntity.COMMENT,
        entity_id=comment.id, entity_label=task.title, new=comment.body,
    )
    db.commit()
    return CommentOut.model_validate(comment)


def list_comments(db: Session, user: User, task_id: int) -> list[CommentOut]:
    task, _ = get_task_for_view(db, user, task_id)
    rows = db.scalars(
        select(TaskComment)
        .where(TaskComment.task_id == task.id)
        .options(joinedload(TaskComment.user))
        .order_by(TaskComment.created_at, TaskComment.id)
    ).unique().all()
    return [CommentOut.model_validate(c) for c in rows]


def list_activities(db: Session, user: User, task_id: int) -> list[ActivityOut]:
    task, _ = get_task_for_view(db, user, task_id)
    rows = db.scalars(
        select(TaskActivity)
        .where(TaskActivity.task_id == task.id)
        .options(joinedload(TaskActivity.user))
        .order_by(TaskActivity.created_at.desc(), TaskActivity.id.desc())
    ).unique().all()
    return [ActivityOut.model_validate(a) for a in rows]
