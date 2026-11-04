from datetime import date

from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from app.models import Priority, Project, ProjectMember, ProjectStatus, Role, Task, TaskStatus, User
from app.schemas.dashboard import DashboardOut, DeadlineItem, ProjectProgress
from app.services import task_service


def build_dashboard(db: Session, user: User) -> DashboardOut:
    today = date.today()

    # What counts as "my tasks" depends on the role (shared rule with the task list endpoint).
    scope = task_service.task_scope(user)

    def count(*conditions) -> int:
        return db.scalar(select(func.count(Task.id)).where(*scope, *conditions)) or 0

    by_status = {s.value: 0 for s in TaskStatus}
    for status, n in db.execute(select(Task.status, func.count(Task.id)).where(*scope).group_by(Task.status)):
        by_status[status.value] = n
    by_priority = {p.value: 0 for p in Priority}
    for prio, n in db.execute(select(Task.priority, func.count(Task.id)).where(*scope).group_by(Task.priority)):
        by_priority[prio.value] = n

    overdue = count(Task.deadline < today, Task.status != TaskStatus.DONE)
    common = {
        "total_tasks": sum(by_status.values()),
        "pending_tasks": by_status["TODO"],
        "in_progress_tasks": by_status["IN_PROGRESS"] + by_status["IN_REVIEW"],
        "completed_tasks": by_status["DONE"],
        "overdue_tasks": overdue,
    }

    if user.role == Role.ADMIN:
        summary = {
            "total_users": db.scalar(select(func.count(User.id))) or 0,
            "total_projects": db.scalar(select(func.count(Project.id))) or 0,
            "active_projects": db.scalar(select(func.count(Project.id)).where(Project.status == ProjectStatus.ACTIVE)) or 0,
            "completed_projects": db.scalar(select(func.count(Project.id)).where(Project.status == ProjectStatus.COMPLETED)) or 0,
            **common,
        }
    elif user.role == Role.MANAGER:
        mine = select(Project.id).where(Project.manager_id == user.id)
        summary = {
            "managed_projects": db.scalar(select(func.count(Project.id)).where(Project.manager_id == user.id)) or 0,
            "team_members": db.scalar(
                select(func.count(distinct(ProjectMember.user_id))).where(ProjectMember.project_id.in_(mine))
            ) or 0,
            **common,
        }
    else:
        summary = {"assigned_tasks": common["total_tasks"], **common}

    done_expr = func.sum(case((Task.status == TaskStatus.DONE, 1), else_=0))
    base = select(Project.id, Project.name, func.count(Task.id), done_expr).select_from(Project)
    if user.role == Role.ADMIN:
        base = base.outerjoin(Task, Task.project_id == Project.id)
    elif user.role == Role.MANAGER:
        base = base.outerjoin(Task, Task.project_id == Project.id).where(Project.manager_id == user.id)
    else:
        base = base.join(Task, Task.project_id == Project.id).where(Task.assignee_id == user.id)
    progress = []
    for pid, name, total, done in db.execute(base.group_by(Project.id, Project.name).order_by(Project.id.desc()).limit(10)):
        done = int(done or 0)
        progress.append(
            ProjectProgress(
                id=pid, name=name, total_tasks=total, done_tasks=done,
                completion_percentage=round(done * 100 / total, 1) if total else 0.0,
            )
        )

    upcoming = db.execute(
        select(Task, Project.name)
        .join(Project, Project.id == Task.project_id)
        .where(*scope, Task.status != TaskStatus.DONE, Task.deadline >= today)
        .order_by(Task.deadline, Task.id)
        .limit(5)
    ).all()

    return DashboardOut(
        role=user.role,
        summary=summary,
        tasks_by_status=by_status,
        tasks_by_priority=by_priority,
        projects=progress,
        upcoming_deadlines=[
            DeadlineItem(
                id=t.id, title=t.title, project_id=t.project_id, project_name=pname,
                deadline=t.deadline, priority=t.priority, status=t.status,
            )
            for t, pname in upcoming
        ],
    )
