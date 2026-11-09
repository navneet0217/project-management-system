from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import Forbidden, NotFound
from app.models import (
    AuditAction,
    Project,
    ProjectActivity,
    ProjectMember,
    ProjectStatus,
    Role,
    Task,
    User,
)
from app.schemas.audit import ProjectActivityOut
from app.schemas.profile import ProfileProject, UserProfileOut
from app.schemas.task import TaskOut
from app.schemas.user import UserOption, UserOut

TASK_LIMIT = 50
ACTIVITY_LIMIT = 20


def get_profile(db: Session, viewer: User, user_id: int) -> UserProfileOut:
    target = db.get(User, user_id)
    if not target:
        raise NotFound("User not found")
    # Managers use profiles to pick developers for their projects; admins can see everyone.
    if not viewer.has_role(Role.ADMIN) and not target.has_role(Role.DEVELOPER):
        raise Forbidden("Managers can only view developer profiles")

    member_of = db.scalars(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == target.id)
        .options(joinedload(Project.manager))
    ).unique().all()
    managed = db.scalars(select(Project).where(Project.manager_id == target.id)).all()

    current: list[ProfileProject] = []
    past: list[ProfileProject] = []
    seen_ids: set[int] = set()
    for relation, projects in (("Manager", managed), ("Member", member_of)):
        for p in projects:
            if p.id in seen_ids:
                continue
            seen_ids.add(p.id)
            item = ProfileProject(id=p.id, name=p.name, status=p.status, relation=relation)
            (past if p.status == ProjectStatus.COMPLETED else current).append(item)

    # Projects the user was removed from also count as past involvement.
    active_ids = {p.id for p in member_of} | {p.id for p in managed}
    removed = db.scalars(
        select(Project)
        .join(ProjectActivity, ProjectActivity.project_id == Project.id)
        .where(ProjectActivity.action == AuditAction.MEMBER_REMOVED, ProjectActivity.target_user_id == target.id)
        .distinct()
    ).all()
    past += [
        ProfileProject(id=p.id, name=p.name, status=p.status, relation="Removed")
        for p in removed
        if p.id not in active_ids
    ]

    managers: dict[int, UserOption] = {}
    for p in member_of:
        if p.manager and p.manager.id != target.id and p.status != ProjectStatus.COMPLETED:
            managers[p.manager.id] = UserOption.model_validate(p.manager)

    tasks = db.scalars(
        select(Task)
        .where(Task.assignee_id == target.id)
        .options(joinedload(Task.assignee), joinedload(Task.project))
        .order_by(Task.created_at.desc(), Task.id.desc())
        .limit(TASK_LIMIT)
    ).unique().all()
    activity = db.scalars(
        select(ProjectActivity)
        .where(or_(ProjectActivity.actor_id == target.id, ProjectActivity.target_user_id == target.id))
        .options(
            joinedload(ProjectActivity.actor),
            joinedload(ProjectActivity.target_user),
            joinedload(ProjectActivity.project),
        )
        .order_by(ProjectActivity.created_at.desc(), ProjectActivity.id.desc())
        .limit(ACTIVITY_LIMIT)
    ).unique().all()

    return UserProfileOut(
        user=UserOut.model_validate(target),
        managers=list(managers.values()),
        current_projects=current,
        past_projects=past,
        tasks=[TaskOut.model_validate(t) for t in tasks],
        activity=[ProjectActivityOut.model_validate(a) for a in activity],
    )
