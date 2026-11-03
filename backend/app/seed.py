"""Create demo data:  python -m app.seed   (safe to run twice: it skips if data exists)."""
from datetime import date, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Priority, ProjectStatus, Role, TaskStatus, User
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate
from app.services import project_service, task_service

ADMIN_EMAIL = "admin@demo.dev"


def _user(db, email: str, name: str, role: Role) -> User:
    user = User(email=email, full_name=name, role=role, hashed_password=hash_password(settings.SEED_PASSWORD))
    db.add(user)
    db.flush()
    return user


def run() -> None:
    today = date.today()
    with SessionLocal() as db:
        if db.scalar(select(User.id).where(User.email == ADMIN_EMAIL)):
            print("Seed data already exists. Nothing to do.")
            return

        admin = _user(db, ADMIN_EMAIL, "Aarav Admin", Role.ADMIN)
        m1 = _user(db, "meera.manager@demo.dev", "Meera Manager", Role.MANAGER)
        m2 = _user(db, "rohan.manager@demo.dev", "Rohan Mehta", Role.MANAGER)
        devs = [
            _user(db, "dev.isha@demo.dev", "Isha Developer", Role.DEVELOPER),
            _user(db, "dev.kabir@demo.dev", "Kabir Developer", Role.DEVELOPER),
            _user(db, "dev.neha@demo.dev", "Neha Developer", Role.DEVELOPER),
            _user(db, "dev.arjun@demo.dev", "Arjun Developer", Role.DEVELOPER),
        ]
        db.commit()
        isha, kabir, neha, arjun = devs

        plans = [
            (m1, "Website Redesign", "Refresh the marketing site with the new brand.", ProjectStatus.ACTIVE, [isha, kabir, neha]),
            (m1, "Mobile App v2", "Rebuild the mobile app with offline support.", ProjectStatus.ACTIVE, [kabir, arjun]),
            (m2, "Data Platform Migration", "Move reporting to the new warehouse.", ProjectStatus.PLANNING, [neha, arjun, isha]),
        ]
        # (title, priority, status, deadline offset in days, assignee index in project, comment)
        task_sets = [
            [
                ("Design new landing page", Priority.HIGH, TaskStatus.IN_REVIEW, 2, 0, "Figma file is ready for review."),
                ("Set up CI for frontend", Priority.MEDIUM, TaskStatus.DONE, -5, 1, None),
                ("Fix navbar on mobile", Priority.CRITICAL, TaskStatus.IN_PROGRESS, -2, 2, "Reproduced on iOS Safari."),
                ("Write copy for pricing page", Priority.LOW, TaskStatus.TODO, 10, 0, None),
                ("Accessibility audit", Priority.HIGH, TaskStatus.TODO, 6, 1, None),
                ("Optimise hero images", Priority.MEDIUM, TaskStatus.IN_PROGRESS, 1, 2, None),
            ],
            [
                ("Offline sync prototype", Priority.CRITICAL, TaskStatus.IN_PROGRESS, 4, 0, "Using a local queue first."),
                ("Push notification service", Priority.HIGH, TaskStatus.TODO, 12, 1, None),
                ("Login screen redesign", Priority.MEDIUM, TaskStatus.DONE, -8, 0, None),
                ("Crash reporting setup", Priority.LOW, TaskStatus.DONE, -3, 1, None),
                ("Release checklist", Priority.MEDIUM, TaskStatus.TODO, -1, 0, None),
            ],
            [
                ("Map legacy tables", Priority.HIGH, TaskStatus.TODO, 7, 0, None),
                ("Pick ETL tooling", Priority.MEDIUM, TaskStatus.IN_PROGRESS, 3, 1, "Comparing two options."),
                ("Data quality rules", Priority.HIGH, TaskStatus.TODO, 14, 2, None),
                ("Cost estimate", Priority.LOW, TaskStatus.DONE, -4, 1, None),
            ],
        ]

        for (manager, name, desc, status, members), tasks in zip(plans, task_sets, strict=True):
            project = project_service.create_project(
                db, admin,
                ProjectCreate(
                    name=name, description=desc, status=status,
                    start_date=today - timedelta(days=20), end_date=today + timedelta(days=40),
                    manager_id=manager.id,
                ),
            )
            for dev in members:
                project_service.add_member(db, manager, project.id, dev.id)
            for title, prio, tstatus, offset, idx, comment in tasks:
                assignee = members[idx]
                task = task_service.create_task(
                    db, manager, project.id,
                    TaskCreate(title=title, priority=prio, deadline=today + timedelta(days=offset), assignee_id=assignee.id),
                )
                # Move through realistic steps so the activity timeline has history.
                path = {
                    TaskStatus.TODO: [],
                    TaskStatus.IN_PROGRESS: [TaskStatus.IN_PROGRESS],
                    TaskStatus.IN_REVIEW: [TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW],
                    TaskStatus.DONE: [TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW, TaskStatus.DONE],
                }[tstatus]
                for step in path:
                    task_service.change_status(db, assignee, task.id, step)
                if comment:
                    task_service.add_comment(db, assignee, task.id, comment)
        print("Seeded demo data.")
        print(f"Logins (password for all: {settings.SEED_PASSWORD}):")
        print("  Admin:     admin@demo.dev")
        print("  Managers:  meera.manager@demo.dev, rohan.manager@demo.dev")
        print("  Developer: dev.isha@demo.dev (also dev.kabir / dev.neha / dev.arjun @demo.dev)")


if __name__ == "__main__":
    run()
