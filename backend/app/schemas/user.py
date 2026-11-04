from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import ProjectStatus, Role


def _check_password(value: str) -> str:
    if not (any(c.isalpha() for c in value) and any(c.isdigit() for c in value)):
        raise ValueError("Password must contain at least one letter and one number")
    return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class SignupRequest(BaseModel):
    """Public self-signup. No role field on purpose: the server always assigns DEVELOPER."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)

    _pw = field_validator("password")(_check_password)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=200)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOption(BaseModel):
    """Minimal user info, safe to embed in other responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    role: Role


class UserOut(UserOption):
    email: str
    is_active: bool
    created_at: datetime


class ProjectRef(BaseModel):
    """A project reference for the Users table (current allocation)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: ProjectStatus


class UserListItem(UserOut):
    projects: list[ProjectRef] = []


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.DEVELOPER

    _pw = field_validator("password")(_check_password)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _pw(cls, value: str | None) -> str | None:
        return _check_password(value) if value is not None else value
