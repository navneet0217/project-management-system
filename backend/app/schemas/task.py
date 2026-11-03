from datetime import date, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models import ActivityType, Priority, TaskStatus
from app.schemas.user import UserOption

DUE_SOON_DAYS = 2


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    priority: Priority = Priority.MEDIUM
    deadline: date | None = None
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    """Only fields the client actually sends are applied (so null can clear assignee/deadline)."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    priority: Priority | None = None
    deadline: date | None = None
    assignee_id: int | None = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: Priority
    deadline: date | None
    assignee: UserOption | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_overdue(self) -> bool:
        return bool(self.deadline and self.status != TaskStatus.DONE and self.deadline < date.today())

    @computed_field
    @property
    def due_soon(self) -> bool:
        if not self.deadline or self.status == TaskStatus.DONE:
            return False
        today = date.today()
        return today <= self.deadline <= today + timedelta(days=DUE_SOON_DAYS)


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user: UserOption | None
    body: str
    created_at: datetime


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: ActivityType
    old_value: str | None
    new_value: str | None
    user: UserOption | None
    created_at: datetime
