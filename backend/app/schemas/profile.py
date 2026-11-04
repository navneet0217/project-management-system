from pydantic import BaseModel, ConfigDict

from app.models import ProjectStatus
from app.schemas.audit import ProjectActivityOut
from app.schemas.task import TaskOut
from app.schemas.user import UserOption, UserOut


class ProfileProject(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: ProjectStatus
    relation: str  # "Member", "Manager" or "Removed" (was a member, then removed)


class UserProfileOut(BaseModel):
    user: UserOut
    managers: list[UserOption]  # the managers of the projects this user is working on
    current_projects: list[ProfileProject]
    past_projects: list[ProfileProject]
    tasks: list[TaskOut]
    activity: list[ProjectActivityOut]
