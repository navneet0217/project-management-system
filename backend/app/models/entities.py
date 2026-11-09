from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    DEVELOPER = "DEVELOPER"


class ProjectStatus(str, enum.Enum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"


class TaskStatus(str, enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"


class Priority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActivityType(str, enum.Enum):
    CREATED = "CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    ASSIGNEE_CHANGED = "ASSIGNEE_CHANGED"


class AuditAction(str, enum.Enum):
    """What happened, for the project-level audit log."""

    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    TASK_CREATED = "TASK_CREATED"
    TASK_UPDATED = "TASK_UPDATED"
    TASK_DELETED = "TASK_DELETED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_REASSIGNED = "TASK_REASSIGNED"
    TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED"
    TASK_PRIORITY_CHANGED = "TASK_PRIORITY_CHANGED"
    COMMENT_ADDED = "COMMENT_ADDED"
    MEMBER_ADDED = "MEMBER_ADDED"
    MEMBER_REMOVED = "MEMBER_REMOVED"


class AuditEntity(str, enum.Enum):
    PROJECT = "PROJECT"
    TASK = "TASK"
    MEMBER = "MEMBER"
    COMMENT = "COMMENT"


class TokenPurpose(str, enum.Enum):
    VERIFY_EMAIL = "VERIFY_EMAIL"
    RESET_PASSWORD = "RESET_PASSWORD"


def _enum(e: type[enum.Enum]) -> Enum:
    # Stored as VARCHAR (not a native DB enum) so adding a value later is a simple migration.
    return Enum(e, native_enum=False, length=20)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(_enum(Role), index=True)
    role_records: Mapped[list[RoleRecord]] = relationship(secondary="user_roles", lazy="selectin")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Soft remove: the row stays (tasks, activity and history keep pointing at it) but the user is hidden and cannot log in.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    # NULL = the user has not proved they own the email address yet (cannot log in)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )


    @property
    def roles(self) -> list[Role]:
        assigned = {Role(record.name) for record in self.role_records} or {self.role}
        return [role for role in Role if role in assigned]

    def has_role(self, role: Role) -> bool:
        return role in self.roles

    @classmethod
    def with_role(cls, role: Role):
        return cls.role_records.any(RoleRecord.name == role.value) | (
            ~cls.role_records.any() & (cls.role == role)
        )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(_enum(ProjectStatus), default=ProjectStatus.PLANNING, index=True)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )

    manager: Mapped[User | None] = relationship(foreign_keys=[manager_id])
    members: Mapped[list[ProjectMember]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    tasks: Mapped[list[Task]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    """Many-to-many link between projects and developers (composite primary key = unique pair)."""

    __tablename__ = "project_members"

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_project_status", "project_id", "status"),
        Index("ix_tasks_assignee_status", "assignee_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(_enum(TaskStatus), default=TaskStatus.TODO)
    priority: Mapped[Priority] = mapped_column(_enum(Priority), default=Priority.MEDIUM)
    deadline: Mapped[date | None] = mapped_column(Date, index=True)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )

    project: Mapped[Project] = relationship(back_populates="tasks")
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id])
    comments: Mapped[list[TaskComment]] = relationship(back_populates="task", cascade="all, delete-orphan")
    activities: Mapped[list[TaskActivity]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    @property
    def project_name(self) -> str | None:
        return self.project.name if self.project else None


class TaskComment(Base):
    __tablename__ = "task_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )

    task: Mapped[Task] = relationship(back_populates="comments")
    user: Mapped[User | None] = relationship()


class TaskActivity(Base):
    __tablename__ = "task_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    type: Mapped[ActivityType] = mapped_column(_enum(ActivityType))
    old_value: Mapped[str | None] = mapped_column(String(120))
    new_value: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )

    task: Mapped[Task] = relationship(back_populates="activities")
    user: Mapped[User | None] = relationship()


class ProjectActivity(Base):
    """Append-only audit log. entity_id/entity_label are plain values (no FK) so history survives deletions."""

    __tablename__ = "project_activities"
    __table_args__ = (Index("ix_project_activities_project_created", "project_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, native_enum=False, length=40))
    entity_type: Mapped[AuditEntity] = mapped_column(Enum(AuditEntity, native_enum=False, length=20))
    entity_id: Mapped[int | None] = mapped_column()
    entity_label: Mapped[str | None] = mapped_column(String(200))
    target_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    field: Mapped[str | None] = mapped_column(String(40))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )

    project: Mapped[Project] = relationship()
    actor: Mapped[User | None] = relationship(foreign_keys=[actor_id])
    target_user: Mapped[User | None] = relationship(foreign_keys=[target_user_id])

    @property
    def project_name(self) -> str | None:
        return self.project.name if self.project else None


class AuthToken(Base):
    """One-time emailed tokens (verify email, reset password). Only the SHA-256 hash is stored."""

    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[TokenPurpose] = mapped_column(Enum(TokenPurpose, native_enum=False, length=20))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )


class RoleRecord(Base):
    """Roles as data, so a user can hold several (users.role stays the primary role)."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )
