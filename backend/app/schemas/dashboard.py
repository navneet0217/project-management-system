from datetime import date

from pydantic import BaseModel

from app.models import Priority, Role, TaskStatus


class ProjectProgress(BaseModel):
    id: int
    name: str
    total_tasks: int
    done_tasks: int
    completion_percentage: float


class DeadlineItem(BaseModel):
    id: int
    title: str
    project_id: int
    project_name: str
    deadline: date
    priority: Priority
    status: TaskStatus


class DashboardOut(BaseModel):
    role: Role
    summary: dict[str, int]
    tasks_by_status: dict[str, int]
    tasks_by_priority: dict[str, int]
    projects: list[ProjectProgress]
    upcoming_deadlines: list[DeadlineItem]
