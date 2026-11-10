# API reference (all under /api/v1, Swagger UI at /api/docs)

Auth header for everything except login/refresh/health: `Authorization: Bearer <access_token>`
Errors always look like `{"detail": "message"}` (422 validation errors have a list in `detail`).
Lists return `{items, total, page, size}`.

## Auth
| Method | Path | Who | Notes |
|---|---|---|---|
| POST | /auth/login | anyone | body `{email, password}` -> `{access_token, refresh_token, token_type}` |
| POST | /auth/refresh | anyone | body `{refresh_token}` -> NEW pair (old refresh token is now dead) |
| POST | /auth/logout | anyone | body `{refresh_token}` -> 204 |
| GET | /auth/me | any user | current user |
| POST | /auth/signup | anyone | body `{email, full_name, password}` -> 201 `{detail}`; sends a verification email, no tokens until verified |
| POST | /auth/verify-email | anyone | body `{token}`; single use, 24 h |
| POST | /auth/resend-verification | anyone | body `{email}` -> 202 (never reveals if the email exists) |
| ~~POST~~ | ~~/auth/forgot-password~~ (disabled for now) | anyone | body `{email}` -> 202 (same privacy rule) |
| ~~POST~~ | ~~/auth/reset-password~~ (disabled for now) | anyone | body `{token, password}`; 30 min, single use, revokes all refresh tokens |

Login returns 403 "verify your email" until the address is verified. Admin-created, seeded and pre-existing users count as verified (migration 0004). Email is only used for signup verification (Resend when `RESEND_API_KEY` is set, otherwise logged).

## Notifications (in-app, migration 0006)

| Method | Path | Who | Notes |
|---|---|---|---|
| GET | /notifications | any user | own latest 30: `{items:[{id, project_id, title, body, is_read, created_at}], unread}` |
| POST | /notifications/{id}/read | any user | marks own notification read, 204 |
| POST | /notifications/read-all | any user | 204 |

Task, comment and member changes notify the project manager and the assignee (never the actor), in the same transaction as the change.

Access token lives 15 min, refresh token 7 days. Frontend: on 401, call /auth/refresh once, retry the request;
if that fails, log out.

## Users (ADMIN only unless noted)
| Method | Path | Notes |
|---|---|---|
| GET | /users | query: search, role, is_active, removed (true = only soft-removed users), sort_by (full_name, email, role, is_active, created_at), order, page, size. Each user includes `projects` (current, not completed: as member or manager), `managers` (managers of the projects they work on) and `deleted_at`. Removed users are hidden unless `removed=true` |
| POST | /users | `{email, full_name, password, roles}`; `roles` is a nonempty array of ADMIN, MANAGER, DEVELOPER |
| GET | /users/{id} | |
| PATCH | /users/{id} | `{full_name?, roles?, is_active?, password?}`; roles replaces the assigned set (admin cannot deactivate self or remove their own ADMIN role) |
| DELETE | /users/{id} | **Soft remove** (ADMIN): sets `deleted_at`, deactivates, revokes sessions; history is kept. 400 for yourself, 409 if they manage an active project |
| POST | /users/{id}/restore | Undo a soft remove (ADMIN). The user stays inactive until activated |
| GET | /users/options | ADMIN + MANAGER. Dropdown list of active users, query: role |
| GET | /users/{id}/profile | ADMIN (anyone), MANAGER (developers only). `{user, managers, current_projects, past_projects, tasks, activity}`. Past = completed projects + projects the user was removed from |

User responses include `roles`. Role filters and user options match any assigned role. The legacy `role` input still replaces assignments with one role; when both inputs are supplied, `roles` takes precedence. Output `role` is the highest assigned role (ADMIN, then MANAGER, then DEVELOPER), retained for dashboard/client compatibility. Assignment records in `user_roles` control authorization; records with no links fall back to the legacy role until assigned through the API. Only ADMIN can grant roles; public signup always creates a DEVELOPER.

A MANAGER + DEVELOPER sees managed projects plus member projects, and managed tasks plus personally assigned tasks. They can manage only their own projects; elsewhere developer restrictions apply. ADMIN permissions take precedence. `GET /projects?member_only=true` limits the result to actual memberships for the My Tasks project picker.

## Projects
| Method | Path | Who | Notes |
|---|---|---|---|
| GET | /projects | any | scoped by role. query: search, status, page, size |
| POST | /projects | ADMIN, MANAGER | `{name, description?, status?, start_date?, end_date?, manager_id?}` |
| GET | /projects/{id} | members/manager/admin | includes member_count, total_tasks, done_tasks, completion_percentage |
| PATCH | /projects/{id} | project manager, admin | only admin may change manager_id |
| DELETE | /projects/{id} | project manager, admin | 409 if open tasks exist |
| GET | /projects/{id}/activities | anyone who can see the project | audit timeline, newest first. query: category (tasks, members, project, comments), page, size. Each entry: actor, action, entity_label, field, old_value, new_value, comment, created_at |
| GET | /projects/{id}/members | anyone who can see the project | |
| POST | /projects/{id}/members | project manager, admin | `{user_id}` (developers only) |
| DELETE | /projects/{id}/members/{user_id} | project manager, admin | unassigns their tasks |

## Tasks
| Method | Path | Who | Notes |
|---|---|---|---|
| GET | /projects/{id}/tasks | anyone who can see the project | query: status, priority, assignee_id, search, sort_by (created_at, deadline, priority, status, title), order, page, size (default 50, max 200) |
| POST | /projects/{id}/tasks | project manager, admin; **developers** for themselves | `{title, description?, priority?, deadline?, assignee_id?}`. A developer (member of the project) always gets assignee = self; assigning someone else is 403 |
| GET | /tasks | any | every task the caller can see (admin: all, manager: own projects, developer: assigned). query: status, priority, search, sort_by, order, page, size (default 10). Each task includes `project_name`. |
| GET | /tasks/my | any | tasks assigned to me |
| GET | /tasks/{id} | anyone who can see the project | |
| PATCH | /tasks/{id} | project manager, admin; the task's assignee | send only fields to change; `assignee_id: null` unassigns. The assignee (developer) may change title, description, priority, deadline but not the assignee |
| PATCH | /tasks/{id}/status | assignee, project manager, admin | `{status}`. **Kanban uses this one.** |
| DELETE | /tasks/{id} | project manager, admin; a developer only for tasks assigned to them that they created | **body `{reason}` is mandatory** (min 3 chars, else 422); the reason is saved in the project activity |
| GET/POST | /tasks/{id}/comments | anyone who can see the project | POST `{body}` |
| GET | /tasks/{id}/activities | anyone who can see the project | newest first. type: CREATED, STATUS_CHANGED, ASSIGNEE_CHANGED |

Every task response includes: `assignee {id, full_name, role} | null`, `is_overdue`, `due_soon`.

## Dashboard
GET /dashboard -> `{role, summary{...}, tasks_by_status, tasks_by_priority, projects[], upcoming_deadlines[]}`
`summary` keys depend on role:
- ADMIN: total_users, total_projects, active_projects, completed_projects, total_tasks, pending_tasks, in_progress_tasks, completed_tasks, overdue_tasks
- MANAGER: managed_projects, team_members, total_tasks, pending_tasks, in_progress_tasks, completed_tasks, overdue_tasks
- DEVELOPER: assigned_tasks, total_tasks, pending_tasks, in_progress_tasks, completed_tasks, overdue_tasks

## Health
GET /health -> `{"status":"ok"}` (checks the database)

## Demo logins (after `python -m app.seed`, password `Demo@12345`)
admin@demo.dev | meera.manager@demo.dev | rohan.manager@demo.dev | dev.isha@demo.dev (also dev.kabir, dev.neha, dev.arjun @demo.dev)

## Local email delivery

Set `RESEND_API_KEY`, `EMAIL_FROM`, and `APP_URL` in the root `.env`. Local Uvicorn reads this first, then `backend/.env`; backend values override root values (including an explicitly empty key). Process environment variables take precedence over both. Docker Compose passes root settings into the container. Restart the backend after changes; for changed Compose environment values, recreate it (`docker compose up -d --force-recreate backend` from the repository root). `APP_URL` must be the frontend origin, usually `http://localhost:5173` for Vite or `http://localhost:8080` for Docker.

Gmail and other valid addresses use the same flow: signup verifies inbox ownership, while admin-created users are already trusted. A Gmail-looking address alone does not prove that the inbox exists. Resend's sandbox sender only delivers to the account owner's address; verify a sender domain and use its sender address to deliver to arbitrary registered users. No key means console-only email. Forgot-password confirmation does not guarantee delivery: inspect backend logs for provider errors. Task and membership changes no longer send email: they create in-app notifications (bell icon).

## Project activity (audit log)
Stored in table `project_activities` (Alembic 0002). Written by `audit_service.record()` in the same transaction as the change.
Actions: PROJECT_CREATED, PROJECT_UPDATED, TASK_CREATED, TASK_UPDATED, TASK_DELETED, TASK_ASSIGNED, TASK_REASSIGNED, TASK_STATUS_CHANGED,
TASK_PRIORITY_CHANGED, COMMENT_ADDED, MEMBER_ADDED, MEMBER_REMOVED. Entities: PROJECT, TASK, MEMBER, COMMENT.
Timestamps are UTC without a timezone suffix; the frontend (`lib/dates.ts`) adds the `Z`.
