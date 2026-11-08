"""Reusable audit logging for project activity.

Every service that changes a project, task or member calls record(). The row is added to the SAME
database session as the change, so the action and its log entry are committed (or rolled back) together.
"""

from datetime import date, datetime
from enum import Enum

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import AuditAction, AuditEntity, Project, ProjectActivity, User
from app.services import notification_service

# The filter groups shown in the Activity tab
CATEGORY_ENTITIES: dict[str, list[AuditEntity]] = {
    "tasks": [AuditEntity.TASK],
    "members": [AuditEntity.MEMBER],
    "project": [AuditEntity.PROJECT],
    "comments": [AuditEntity.COMMENT],
}

_MAX_VALUE_LEN = 500


def _text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        value = value.value
    elif isinstance(value, (date, datetime)):
        value = value.isoformat()
    text = str(value)
    return text if len(text) <= _MAX_VALUE_LEN else text[: _MAX_VALUE_LEN - 1] + "…"


def record(
    db: Session,
    *,
    project_id: int,
    actor: User | None,
    action: AuditAction,
    entity_type: AuditEntity,
    entity_id: int | None = None,
    entity_label: str | None = None,
    target_user_id: int | None = None,
    field: str | None = None,
    old: object = None,
    new: object = None,
    comment: str | None = None,
) -> None:
    db.add(
        ProjectActivity(
            project_id=project_id,
            actor_id=actor.id if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_label=(entity_label or "")[:200] or None,
            target_user_id=target_user_id,
            field=field,
            old_value=_text(old),
            new_value=_text(new),
            comment=comment,
        )
    )
    notification_service.queue(
        db, project_id=project_id, actor=actor, action=action, entity_type=entity_type, entity_id=entity_id,
        entity_label=entity_label, target_user_id=target_user_id, field=field, old=_text(old), new=_text(new),
        comment=comment,
    )


def list_for_project(
    db: Session, project: Project, *, category: str | None, page: int, size: int
) -> tuple[list[ProjectActivity], int]:
    """Newest first. The caller must already have checked that the user may view the project."""
    stmt = select(ProjectActivity).where(ProjectActivity.project_id == project.id)
    if category:
        stmt = stmt.where(ProjectActivity.entity_type.in_(CATEGORY_ENTITIES[category]))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        db.scalars(
            stmt.options(
                joinedload(ProjectActivity.actor),
                joinedload(ProjectActivity.target_user),
                joinedload(ProjectActivity.project),
            )
            .order_by(ProjectActivity.created_at.desc(), ProjectActivity.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        .unique()
        .all()
    )
    return list(rows), total
