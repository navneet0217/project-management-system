# Project Context

## Goal
Portfolio-quality MVP built in 7 days, deployed on my own PC using Cloudflare Tunnel.
A working deployed MVP matters more than many unfinished features.

## Roles
- Admin: manages all users and projects, sees all analytics.
- Manager: manages own projects, members and tasks, sees project analytics.
- Developer: sees projects they belong to, updates status of ONLY their own tasks, comments, personal dashboard.

## Database (7 tables)
users, projects, project_members, tasks, task_comments, task_activities, refresh_tokens
- Task status: TODO, IN_PROGRESS, IN_REVIEW, DONE
- Priority: LOW, MEDIUM, HIGH, CRITICAL
- Project status: PLANNING, ACTIVE, ON_HOLD, COMPLETED
- Enums are stored as VARCHAR (not native DB enums).

## Key design decisions (already implemented in backend)
- If a user cannot see a project/task, the API returns 404 (not 403) so IDs cannot be probed.
  403 is only used when the user can see it but lacks the right to change it.
- Refresh tokens are single-use (rotation). Reusing an old one revokes all of that user's sessions.
- Only a hash of each refresh token is stored in the DB.
- Deactivating a user takes effect immediately (the user is re-checked on every request).
- A project cannot be deleted while it has open (not DONE) tasks (409).
- Removing a member unassigns their tasks in that project and records it in the activity timeline.
- Dashboard definitions: pending = TODO, in progress = IN_PROGRESS + IN_REVIEW, completed = DONE,
  overdue = deadline in the past and not DONE, due soon = deadline within 2 days.
- Simple in-memory rate limit on login/refresh (per client IP, reads CF-Connecting-IP / X-Forwarded-For).
- Passwords: Argon2. Password rule: min 8 chars, at least one letter and one number.

## Features
Core: auth (JWT access + refresh), user management, projects, members, tasks, comments, role-based dashboards.
Standout:
1. Kanban drag-and-drop with optimistic updates (rollback if server rejects)
2. Activity timeline per task (status and assignee changes)
3. Recharts dashboards per role
4. Dark mode
5. Seed script with demo data (`python -m app.seed`)
6. Overdue and due-soon badges (backend already returns `is_overdue` and `due_soon` on every task)
7. Live demo with demo logins in the README
Out of scope (Version 2): WebSockets, email, password reset, multi-tenancy, advanced analytics.

## Folder structure
- backend/app/ : api/v1/endpoints, core, models, schemas, services, db, seed.py, main.py
- backend/tests/, backend/alembic/
- frontend/src/ : api, components, features, hooks, layouts, pages, routes, context, types, utils
- nginx/
- docker-compose.dev.yml (MySQL for local dev), docker-compose.yml (production, Day 6), .env.example

## Request flow
Cloudflare Tunnel -> Nginx -> React static files, and /api -> FastAPI -> MySQL (private Docker network, never public)

## Shared local/showcase data
The Vite frontend on port 5173 proxies `/api` to Docker Nginx on port 8080, which uses the same backend/database as Cloudflare. Start Docker before using Vite. The Windows MySQL database and optional standalone backend on port 8000 are separate; edits there do not update Docker. After changing frontend/backend source, rebuild the Docker services to update the public app. Never remove the database volume to refresh application code.

## Git workflow
main (stable) <- dev (integration) <- feature/* branches.
CI must pass before merging into dev.
Push to dev triggers: build images, push to GHCR, SSH to server, pull, restart with Compose, health check.
Rollback: redeploy a previous image tag.

## 7-day plan
1. Design and setup
2. Models, migrations, Argon2, JWT auth, RBAC, seed part 1
3. User and project APIs, permissions, tests
4. Task, comment, activity and dashboard APIs, seed part 2
5. Frontend core (layout, login, routes, users, projects, tasks, dark mode)
6. Kanban, task detail, charts, badges, Dockerfiles, Compose, Nginx
7. CI/CD, GHCR, Cloudflare Tunnel, deploy, README

## Cut order if behind schedule
dark mode, badges, pagination, extra tests, chart variety.
Never cut: auth and roles, projects, tasks, Kanban, Docker, deployment.
