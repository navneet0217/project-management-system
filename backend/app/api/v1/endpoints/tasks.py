from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Priority, TaskStatus, User
from app.schemas.common import Page
from app.schemas.task import (
    ActivityOut,
    CommentCreate,
    CommentOut,
    TaskCreate,
    TaskDelete,
    TaskOut,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.services import task_service

router = APIRouter(tags=["tasks"])


@router.get("/projects/{project_id}/tasks", response_model=Page[TaskOut])
def list_project_tasks(
    project_id: int,
    status: TaskStatus | None = None,
    priority: Priority | None = None,
    assignee_id: int | None = None,
    search: str | None = Query(None, max_length=100),
    sort_by: str = "created_at",
    order: Literal["asc", "desc"] = "desc",
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),  # Kanban needs a big page; lists can pass a smaller size
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = task_service.list_tasks(
        db, user, project_id, status=status, priority=priority, assignee_id=assignee_id,
        search=search, sort_by=sort_by, order=order, page=page, size=size,
    )
    return Page[TaskOut](items=items, total=total, page=page, size=size)


@router.post("/projects/{project_id}/tasks", response_model=TaskOut, status_code=201)
def create_task(
    project_id: int,
    data: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),  # developers may create tasks for themselves; the service enforces it
):
    return task_service.create_task(db, user, project_id, data)


@router.get("/tasks", response_model=Page[TaskOut])
def list_visible_tasks(
    status: TaskStatus | None = None,
    priority: Priority | None = None,
    search: str | None = Query(None, max_length=100),
    sort_by: str = "created_at",
    order: Literal["asc", "desc"] = "desc",
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Every task the caller can see (admin: all, manager: own projects, developer: assigned)."""
    items, total = task_service.visible_tasks(
        db, user, status=status, priority=priority, search=search, sort_by=sort_by, order=order, page=page, size=size
    )
    return Page[TaskOut](items=items, total=total, page=page, size=size)


@router.get("/tasks/my", response_model=Page[TaskOut])
def my_tasks(
    status: TaskStatus | None = None,
    priority: Priority | None = None,
    search: str | None = Query(None, max_length=100),
    sort_by: str = "deadline",
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = task_service.my_tasks(db, user, status, priority, search, sort_by, order, page, size)
    return Page[TaskOut](items=items, total=total, page=page, size=size)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task, _ = task_service.get_task_for_view(db, user, task_id)
    return TaskOut.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int, data: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return task_service.update_task(db, user, task_id, data)


@router.patch("/tasks/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int, data: TaskStatusUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Used by the Kanban board. Developers may call this only for tasks assigned to them."""
    return task_service.change_status(db, user, task_id, data.status)


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    data: TaskDelete,  # a reason is mandatory (422 if missing/blank) and is saved in the project activity log
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task_service.delete_task(db, user, task_id, data.reason)
    return Response(status_code=204)


@router.get("/tasks/{task_id}/comments", response_model=list[CommentOut])
def list_comments(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_service.list_comments(db, user, task_id)


@router.post("/tasks/{task_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    task_id: int, data: CommentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return task_service.add_comment(db, user, task_id, data.body)


@router.get("/tasks/{task_id}/activities", response_model=list[ActivityOut])
def list_activities(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_service.list_activities(db, user, task_id)
