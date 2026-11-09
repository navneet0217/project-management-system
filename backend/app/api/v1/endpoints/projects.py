from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import ProjectStatus, Role, User
from app.schemas.audit import ProjectActivityOut
from app.schemas.common import Page
from app.schemas.project import MemberAdd, ProjectCreate, ProjectOut, ProjectUpdate
from app.schemas.user import UserOption
from app.services import audit_service, project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=Page[ProjectOut])
def list_projects(
    search: str | None = Query(None, max_length=100),
    status: ProjectStatus | None = None,
    member_only: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = project_service.list_projects(db, user, search, status, page, size, member_only)
    return Page[ProjectOut](items=items, total=total, page=page, size=size)


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
):
    project = project_service.create_project(db, user, data)
    return project_service.serialize(db, [project])[0]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = project_service.get_viewable(db, user, project_id)
    return project_service.serialize(db, [project])[0]


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
):
    project = project_service.update_project(db, user, project_id, data)
    return project_service.serialize(db, [project])[0]


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
):
    project_service.delete_project(db, user, project_id)
    return Response(status_code=204)


@router.get("/{project_id}/activities", response_model=Page[ProjectActivityOut])
def project_activities(
    project_id: int,
    category: Literal["tasks", "members", "project", "comments"] | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Audit timeline for a project, newest first. Visible to everyone who can see the project."""
    project = project_service.get_viewable(db, user, project_id)
    rows, total = audit_service.list_for_project(db, project, category=category, page=page, size=size)
    return Page[ProjectActivityOut](
        items=[ProjectActivityOut.model_validate(r) for r in rows], total=total, page=page, size=size
    )


@router.get("/{project_id}/members", response_model=list[UserOption])
def list_members(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return project_service.list_members(db, user, project_id)


@router.post("/{project_id}/members", response_model=list[UserOption], status_code=201)
def add_member(
    project_id: int,
    data: MemberAdd,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
):
    return project_service.add_member(db, user, project_id, data.user_id)


@router.delete("/{project_id}/members/{member_id}", status_code=204)
def remove_member(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
):
    project_service.remove_member(db, user, project_id, member_id)
    return Response(status_code=204)
