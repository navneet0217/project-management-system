from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int | None
    title: str
    body: str
    is_read: bool
    created_at: datetime


class NotificationList(BaseModel):
    items: list[NotificationOut]
    unread: int


@router.get("", response_model=NotificationList)
def my_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items, unread = notification_service.list_for(db, user)
    return {"items": items, "unread": unread}


@router.post("/read-all", status_code=204)
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    notification_service.mark_read(db, user)


@router.post("/{notification_id}/read", status_code=204)
def read_one(notification_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    notification_service.mark_read(db, user, notification_id)
