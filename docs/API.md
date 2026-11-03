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

Access token lives 15 min, refresh token 7 days. Frontend: on 401, call /auth/refresh once, retry the request;
if that fails, log out.

## Users (ADMIN only unless noted)
| Method | Path | Notes |
|---|---|---|
| GET | /users | query: search, role, is_active, page, size |
| POST | /users | `{email, full_name, password, role}` |
| GET | /users/{id} | |
| PATCH | /users/{id} | `{full_name?, role?, is_active?, password?}` (admin cannot deactivate/demote self) |
| GET | /users/options | ADMIN + MANAGER. Dropdown list of active users, query: role |

## Projects
| Method | Path | Who | Notes |
|---|---|---|---|
| GET | /projects | any | scoped by role. query: search, status, page, size |
| POST | /projects | ADMIN, MANAGER | `{name, description?, status?, start_date?, end_date?, manager_id?}` |
| GET | /projects/{id} | members/manager/admin | includes member_count, total_tasks, done_tasks, completion_percentage |
| PATCH | /projects/{id} | project manager, admin | only admin may change manager_id |
| DELETE | /projects/{id} | project manager, admin | 409 if open tasks exist |
| GET | /projects/{id}/members | anyone who can see the project | |
| POST | /projects/{id}/members | project manager, admin | `{user_id}` (developers only) |
| DELETE | /projects/{id}/members/{user_id} | project manager, admin | unassigns their tasks |

## Tasks
| Method | Path | Who | Notes |
|---|---|---|---|
| GET | /projects/{id}/tasks | anyone who can see the project | query: status, priority, assignee_id, search, sort_by (created_at, deadline, priority, status, title), order, page, size (default 50, max 200) |
| POST | /projects/{id}/tasks | project manager, admin | `{title, description?, priority?, deadline?, assignee_id?}` |
| GET | /tasks/my | any | tasks assigned to me |
| GET | /tasks/{id} | anyone who can see the project | |
| PATCH | /tasks/{id} | project manager, admin | send only fields to change; `assignee_id: null` unassigns |
| PATCH | /tasks/{id}/status | assignee, project manager, admin | `{status}`. **Kanban uses this one.** |
| DELETE | /tasks/{id} | project manager, admin | |
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
