import os
from types import SimpleNamespace

# Must be set BEFORE the app is imported (settings are read at import time).
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256-tests"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.security import create_access_token, hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Priority, Project, ProjectMember, ProjectStatus, Role, Task, User  # noqa: E402

PASSWORD = "Passw0rd1"

# Cheap Argon2 settings so the test suite runs fast (production keeps the strong defaults).
import argon2  # noqa: E402

import app.core.security as _security  # noqa: E402

_security._ph = argon2.PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture()
def client(session_factory):
    def override():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def _user(db, email, role, name=None):
    user = User(email=email, full_name=name or email.split("@")[0], role=role, hashed_password=hash_password(PASSWORD))
    db.add(user)
    db.flush()
    return user


@pytest.fixture()
def world(db):
    """admin, 2 managers, 3 developers. p1 (manager1; dev1, dev2 are members), p2 (manager2). t1 -> dev1 in p1."""
    w = SimpleNamespace(
        admin=_user(db, "admin@test.dev", Role.ADMIN),
        m1=_user(db, "m1@test.dev", Role.MANAGER),
        m2=_user(db, "m2@test.dev", Role.MANAGER),
        dev1=_user(db, "dev1@test.dev", Role.DEVELOPER),
        dev2=_user(db, "dev2@test.dev", Role.DEVELOPER),
        dev3=_user(db, "dev3@test.dev", Role.DEVELOPER),
    )
    w.p1 = Project(name="Project One", status=ProjectStatus.ACTIVE, manager_id=w.m1.id)
    w.p2 = Project(name="Project Two", status=ProjectStatus.ACTIVE, manager_id=w.m2.id)
    db.add_all([w.p1, w.p2])
    db.flush()
    db.add_all([ProjectMember(project_id=w.p1.id, user_id=w.dev1.id), ProjectMember(project_id=w.p1.id, user_id=w.dev2.id)])
    w.t1 = Task(project_id=w.p1.id, title="First task", priority=Priority.HIGH, assignee_id=w.dev1.id, created_by=w.m1.id)
    db.add(w.t1)
    db.commit()
    return w


def auth(user) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}
