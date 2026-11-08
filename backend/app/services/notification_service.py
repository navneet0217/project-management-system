"""Email notifications for project/task activity.

audit_service.record() calls queue() for every audited action. Emails wait in the session's outbox and are
only sent after the transaction commits (a rolled-back change must never produce an email).
"""

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models import AuditAction, AuditEntity, Project, Task, User
from app.services import email_service


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
    outbox = db.info.setdefault("outbox", [])
    for user in _recipients(db, project, task, target_user_id, actor):
        if any(m.to == user.email for m in outbox):
            continue  # one email per person per change (creating an assigned task logs two events)
        headline, detail = text
        outbox.append(
            email_service.notification_email(user.email, user.full_name, f"{headline}: {entity_label or ''}".strip(": "), detail, project.id)
        )


def flush(db: Session) -> None:
    for email in db.info.pop("outbox", []):
        email_service.send(email)


def discard(db: Session) -> None:
    db.info.pop("outbox", None)

@event.listens_for(Session, "after_commit")
def _send_after_commit(session: Session) -> None:
    flush(session)


@event.listens_for(Session, "after_rollback")
def _drop_on_rollback(session: Session) -> None:
    discard(session)