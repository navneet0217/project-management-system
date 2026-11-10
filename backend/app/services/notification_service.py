"""In-app notifications (bell icon) for project/task activity.

audit_service.record() calls queue() for every audited action. The row is added to the caller's session, so it is
committed or rolled back together with the change itself.
"""

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import AuditAction, AuditEntity, Notification, Project, Task, User


def _recipients(db: Session, project: Project, task: Task | None, target_user_id: int | None, actor: User | None) -> list[User]:
    ids = {project.manager_id, target_user_id}
    if task is not None:
        ids.add(task.assignee_id)
    ids.discard(None)
    if actor:
        ids.discard(actor.id)  # nobody needs an email about their own action
    users = [db.get(User, i) for i in ids]
    return [u for u in users if u and u.is_active and not u.deleted_at and u.email_verified_at]


def _describe(action: AuditAction, who: str, label: str, field: str | None, old: str | None, new: str | None, comment: str | None):
    task = f'"{label}"'
    match action:
        case AuditAction.TASK_CREATED:
            return "New task", f"{who} created the task {task}."
        case AuditAction.TASK_ASSIGNED:
            return "Task assigned", f"{who} assigned {task} to {new or 'someone'}."
        case AuditAction.TASK_REASSIGNED:
            return "Task reassigned", f"{who} changed the assignee of {task} from {old or 'nobody'} to {new or 'nobody'}."
        case AuditAction.TASK_STATUS_CHANGED:
            return "Task status changed", f"{who} moved {task} from {old} to {new}."
        case AuditAction.TASK_PRIORITY_CHANGED:
            return "Task priority changed", f"{who} changed the priority of {task} from {old} to {new}."
        case AuditAction.TASK_UPDATED:
            return "Task updated", f"{who} changed the {field} of {task}" + (f" from {old} to {new}." if old or new else ".")
        case AuditAction.TASK_DELETED:
            return "Task deleted", f"{who} deleted {task}. Reason: {comment}"
        case AuditAction.COMMENT_ADDED:
            return "New comment", f"{who} commented on {task}: {new}"
        case AuditAction.MEMBER_ADDED:
            return "Added to a project", f"{who} added {label} to the project."
        case AuditAction.MEMBER_REMOVED:
            return "Removed from a project", f"{who} removed {label} from the project."
    return None


def queue(
    db: Session,
    *,
    project_id: int,
    actor: User | None,
    action: AuditAction,
    entity_type: AuditEntity,
    entity_id: int | None,
    entity_label: str | None,
    target_user_id: int | None,
    field: str | None,
    old: str | None,
    new: str | None,
    comment: str | None,
) -> None:
    if entity_type == AuditEntity.PROJECT:
        return  # project-level edits are not emailed
    text = _describe(action, actor.full_name if actor else "Someone", entity_label or "a task", field, old, new, comment)
    project = db.get(Project, project_id)
    if not text or not project:
        return
    # comment events carry the comment id, so the task assignee is passed in as target_user_id instead
    task = db.get(Task, entity_id) if entity_type == AuditEntity.TASK and entity_id else None
    if action == AuditAction.TASK_CREATED:
        task = None  # the assignee is told by the TASK_ASSIGNED event that follows, so they get one clear email
    # in the same transaction as the change: a rolled-back change leaves no notification behind
    seen: set[int] = set()
    headline, detail = text
    for user in _recipients(db, project, task, target_user_id, actor):
        if user.id in seen:
            continue  # one notification per person per change (creating an assigned task logs two events)
        seen.add(user.id)
        title = f"{headline}: {entity_label}" if entity_label else headline
        db.add(Notification(user_id=user.id, project_id=project.id, title=title[:200], body=detail[:500]))


def list_for(db: Session, user: User, limit: int = 30) -> tuple[list[Notification], int]:
    rows = db.scalars(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.id.desc()).limit(limit)
    ).all()
    unread = db.scalar(
        select(func.count()).select_from(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))
    )
    return list(rows), unread or 0


def mark_read(db: Session, user: User, notification_id: int | None = None) -> None:
    stmt = update(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))
    if notification_id is not None:
        stmt = stmt.where(Notification.id == notification_id)
    db.execute(stmt.values(is_read=True))
    db.commit()
