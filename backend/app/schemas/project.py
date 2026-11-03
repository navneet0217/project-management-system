from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models import ProjectStatus
from app.schemas.user import UserOption


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: date | None = None
    end_date: date | None = None
    manager_id: int | None = None  # admins may set this; managers always manage their own projects

    @model_validator(mode="after")
    def _dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    status: ProjectStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    manager_id: int | None = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None
    status: ProjectStatus
    start_date: date | None
    end_date: date | None
    manager: UserOption | None
    member_count: int
    total_tasks: int
    done_tasks: int
    completion_percentage: float
    created_at: datetime


class MemberAdd(BaseModel):
    user_id: int
