from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import AuditAction, AuditEntity
from app.schemas.user import UserOption


class ProjectActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    project_name: str | None = None
    action: AuditAction
    entity_type: AuditEntity
    entity_id: int | None
    entity_label: str | None
    field: str | None
    old_value: str | None
    new_value: str | None
    comment: str | None
    created_at: datetime
    actor: UserOption | None
    target_user: UserOption | None
