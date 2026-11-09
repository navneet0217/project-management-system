# Progress Tracker

## Users table mobile Actions column (2026-11-09)
- Actions was fixed on the right at every viewport, covering user details on narrow screens. It is now fixed only at Ant Design's desktop (`lg`) breakpoint; on mobile/tablet it scrolls with the other columns. Action buttons have a bounded, wrapping layout in both normal and Removed views.
- Frontend TypeScript, scoped oxlint and Docker production frontend build passed. Rebuilt/recreated only `web`; backend and database were not changed.
- Mock-data browser checks at 360/390/820/1440 px were offered but skipped by the user. Manual visibility, horizontal scrolling and action reachability checks remain pending.

## Users project-tag dark-mode contrast (2026-11-09)
- Replaced the custom `teal` tag color with Ant Design's theme-aware `cyan` preset in the admin Users project column and profile project tags. No API or data changes.
- Frontend TypeScript, scoped oxlint and Docker production frontend build passed. Rebuilt/recreated only `web`, making the fix available on port 8080 and the public URL.
- Browser contrast/layout verification was skipped by the user; manual light/dark checks remain pending.

## Shared showcase environment (2026-11-09)
- With user approval, backed up Windows and Docker MySQL to `%LOCALAPPDATA%/Tasklane/backups/20261109-132211/`, then replaced Docker `pms` with the Windows snapshot. Windows MySQL was not changed.
- Rebuilt backend and web from current workspace source and ran `alembic upgrade head`. Production frontend build and Vite configuration typecheck passed.
- Vite now proxies `/api` to `http://localhost:8080`. Ports 5173 and 8080 plus the current Cloudflare URL use the same Docker backend/database; all three health checks returned 200. Counts and checksums match for all 12 business/schema tables (4 users, 2 projects, 4 tasks); transient authentication-token tables were excluded from the comparison.
- Use Docker as the data source going forward. The standalone Windows backend on port 8000 and Windows MySQL remain separate and are no longer used by Vite. Sign out and sign in again on each origin after the switch. Vite source edits still require a Docker rebuild to appear on 8080/public.

## Manual showcase checklist (2026-11-09)
- Added `docs/MANUAL_TESTS.md` with user-run scenarios and local password-reset instructions; manual results remain Not Tested.
- Multi-role assignment is implemented across user Add/Edit, responses, filtering, profiles, navigation, project/task authorization, assignment and dashboard scoping. Schema uses existing migration 0005; run `alembic upgrade head` before deploying if necessary. Legacy `role` remains a compatibility field; role links control combined access. Manual/browser verification remains pending.
- Resend Gmail onboarding/reset/allocation tests cover both admin-created and self-signup users with mocked delivery. Added local backend email settings to `backend/.env.example`; real inbox delivery requires configured Resend credentials and an allowed sender/recipient.
- Local settings now load root `.env`, then `backend/.env`, with process environment variables taking precedence. This shares the root Resend key with local Uvicorn unless locally overridden. No real email or production data was used in automated checks.
- Verification: 100 backend tests passed in an isolated, network-disabled container; Ruff, frontend TypeScript (`tsc --noEmit`) and oxlint passed. Frontend editor diagnostics are clean. Vite build/browser and real inbox verification remain pending; no isolated Node runtime was available for executing the application/build configuration.

## Roadmap status (verified 2026-11-08 by running the app, not by reading code)
Rule: a feature is Done only after it was tested. Evidence = 66 backend tests + a live end-to-end run (API, RBAC, activity log, UI in 3 screen sizes, Kanban drag).

### Done (verified)
| # | Feature | Evidence |
|---|---|---|
| 1,2 | Dashboard, 8 KPI cards, count-up, teal theme | browser test |
| 3 | Dark/light toggle (persists after reload) | browser test |
| 4 | Responsive 1440 / 820 / 390 px, no horizontal overflow, bottom nav on small screens | browser test |
| 5-8 | View all on all 4 dashboard sections | browser test |
| 9,10 | Clickable Total projects / Total tasks with recent-5 popups | browser test |
| 11 | Role capsule removed | browser test |
| 12,13,16 | Project and task create/update/delete, priority, deadline, assignee | API test |
| 14,15 | Kanban drag-and-drop, saved to server | browser test (rollback path covered by unit logic only) |
| 17 | Search / filter / server-side sorting (projects, tasks, users), SQL injection safe | API test |
| 18 | Task deletion needs a reason (422 without it) | API + browser |
| 19,39 | Project activity timeline (stored in DB) | API test |
| 20 | Project member add/remove with details popup | browser test |
| 22,23 | RBAC enforced server-side, role-based nav, IDOR blocked (404) | API + browser |
| 26,27,28,29 | Active/inactive switch, profile, current projects, project history | browser test |
| 30,34,35 | Login/logout, Argon2 hashing, JWT validation, refresh rotation + reuse detection | API test |
| 37 | Login rate limit (429 after 20 tries/min per IP, in-memory) | API test |

| 21,26 | **Phase 2 (2026-11-08):** Manager column, soft remove + restore (Alembic 0003 `users.deleted_at`), Removed view, `PROJECT_CREATED` in the activity log | 74 backend tests + 18 browser checks |

### Pending (verified missing by probing the API)
- **Roles model (24, 25):** multi-role behavior implemented 2026-11-09; manual verification pending. No custom role/permission administration endpoint.
- **Activity:** "Member role changed" does not exist (needs the roles model).
- **Auth (31, 32, 33, 36, 41, 42):** no forgot-password, reset-password or email verification endpoints, no email service.
- **Notifications (38):** no email on task updates.
- **To Verify (40):** task comments work (API test); no edit/delete of comments.
- **Quality gates:** no frontend tests, no dependency or security scan in CI, no DB backup, refresh token is in `localStorage`, CORS allows all methods, no `docs/architecture` or module READMEs.

### Plan (user-approved order)
1 verify (this section) -> 2 users grid -> 3 CI + Vitest -> 4 security hardening -> 5 reset/verify email (Resend) -> 6 notifications -> 7 multi-role + permissions -> 8 frontend `modules/` -> 9 docs + diagrams.

## Branding
- App name: **Tasklane** (name + logo in `frontend/src/components/Logo.tsx`, favicon `frontend/public/favicon.svg`, colours in `frontend/src/lib/brand.ts`). Teal theme (#0d9488). Logo = three rising Kanban lanes on a teal tile.

## Requirements batch 2 (spec pasted by user, built one screen at a time)
- [x] 1. Dashboard: View all on the 4 cards, clickable Total projects / Total tasks (recent-5 popups), role tag removed, new `GET /tasks` + "All tasks" page (admin/manager).
- [x] 2. Users: Active/Inactive switch in the table (confirm on deactivate), server-side column sorting, Projects column, View profile popup (`GET /users/{id}/profile`).
- [x] 3. My Tasks: developer can add / edit / delete own tasks (shared `TasksTable` + `TaskFormModal` self mode), column sorting, status dropdown.
- [x] 4. Projects: delete-task popup with mandatory reason, Activity tab (audit service + `project_activities` table, Alembic 0002), member-add popup showing user details with Cancel / Add.
- [ ] 5. Integration pass on the deployed stack: run `alembic upgrade head` (deploy does it), then check each screen on the public URL.
- Notes: the DB has no `username` column, so profiles show name, email, status and member-since instead. Managers can open profiles of developers only.

## Auth pages
- Signup: `POST /api/v1/auth/signup` {email, full_name, password}; role is always DEVELOPER (server-side). Since migration 0004 it returns no tokens: the user must click the emailed link (`/verify-email`). Also `/forgot-password`, `/reset-password`. Pages share `components/AuthShell.tsx`.
- Email (Resend, `services/email_service.py`) + task-update notifications (`services/notification_service.py`, hooked into `audit_service.record`). Env: `RESEND_API_KEY`, `EMAIL_FROM`, `APP_URL`. Sandbox sender `onboarding@resend.dev` only delivers to the Resend account owner until a domain is verified. 92 backend tests pass.
- Next idea: SSO via OAuth2/OIDC (Google/GitHub), see chat notes.

## Docker / CI-CD (built, local stack verified)
- `docker-compose.yml` = mysql + backend + web (Nginx + built React) + cloudflared quick tunnel (random https URL, changes when the cloudflared container restarts). Run: `docker compose up -d --build`, then `docker compose exec -T backend alembic upgrade head`. App on http://localhost:8080, public URL: run summary on GitHub Actions, or `docker compose logs cloudflared | findstr trycloudflare`.
- Stable URL (later): Cloudflare named tunnel needs a domain; ngrok free static domain is the free alternative.
- `.github/workflows/ci-cd.yml`: backend + frontend checks -> build/push images to GHCR (tag = commit SHA + latest) -> deploy on self-hosted runner (needs repo variable `ENABLE_DEPLOY=true` and the secrets listed in `.env.example`). Not yet tested on GitHub.
- Rollback: set `IMAGE_TAG=<old sha>` in `.env`, then `docker compose pull && docker compose up -d`.

## Current day: Day 5 (frontend). Backend (Days 1-4) is DONE and tested.

## Frontend stack (rewritten)
React + Vite + TypeScript, **Redux Toolkit** (auth + UI slices in `src/store`), **Ant Design** (UI, dark mode via `ConfigProvider`), React Router, Axios, Recharts. Tailwind, Zustand and react-hot-toast were removed.
Day 5 pages built: login, dashboard, projects (+detail with members, tasks, comments/activity drawer), my tasks, users (ADMIN). `pnpm build` passes; not yet tested end-to-end against the running backend.
Run from `frontend/`: `pnpm install`, `pnpm dev` (proxies /api to Docker on localhost:8080; start the Docker stack first).

## Done
- [x] Monorepo structure, .gitignore, .env.example files, docker-compose.dev.yml (MySQL)
- [x] SQLAlchemy models for all 7 tables + Alembic migration 0001
- [x] Argon2, JWT access + rotating refresh tokens, login/refresh/logout/me, rate limit on login
- [x] RBAC dependencies; users, projects (+members), tasks, comments, activity timeline, dashboard APIs
- [x] Seed script (`python -m app.seed`)
- [x] 36 pytest tests passing (auth, permissions, tasks, filters, dashboards), ruff clean
- [ ] Verified against real MySQL 8 (tests/seed ran on SQLite) -> do this first on your PC, see below
- [ ] Context files committed and pushed to GitHub

## Next task (done: backend, frontend core, signup, Docker, CI/CD, deploy on own PC with Cloudflare quick tunnel)
Build in this order. After 1-9 the MVP is demo-ready.
1. [x] Kanban board: dnd-kit drag-and-drop, optimistic move with rollback, pointer-based drop (`components/KanbanBoard.tsx`, Board/List tabs on project page).
2. [x] Dashboard KPI cards with a 3D look (tilt on hover, gradients, count-up) in `components/KpiCard.tsx`.
3. [x] UI polish: indigo theme, gradient sidebar, sticky header, page fade, skeletons, empty states, mobile layout, dark mode. Still open: replace deprecated antd `List`, use `App.useApp()` for message (static `message` warns about theme).
4. [x] Frontend refactor: constants in `lib/options.ts`, `StatusTag` is component-only, project page split into `components/project/*`. Lint is clean.
5. [x] Performance: lazy-loaded routes, main bundle 1.7 MB -> 129 KB (Dashboard chunk 359 KB because of Recharts).
6. Tests in CI: Vitest + React Testing Library (login, signup, route guards), more backend tests.
7. Profile and account: edit profile, change password, forgot/reset password.
8. Notifications and a project activity feed.
9. Security hardening: refresh token in an httpOnly cookie, stricter rate limits, daily DB backup.
10. Later (not needed for the demo): SSO (Google/GitHub OAuth2, needs a stable URL), README with screenshots and an architecture diagram.

## How to run the backend (from project-management-system/)
```bash
cp .env.example .env                         # then edit the passwords
docker compose -f docker-compose.dev.yml up -d
cd backend
python -m venv venv && source venv/bin/activate     # Windows Git Bash: source venv/Scripts/activate
pip install -r requirements-dev.txt
cp .env.example .env                         # set SECRET_KEY (command is inside the file), match the MySQL password
alembic upgrade head                         # creates the tables
python -m app.seed                           # demo data
uvicorn app.main:app --reload                # Swagger: http://localhost:8000/api/docs
python -m pytest                             # tests (use SQLite in memory, no MySQL needed)
ruff check .
```
In Swagger: call POST /auth/login, copy `access_token`, click "Authorize", paste it.

## Notes and decisions
- Repositories layer skipped on purpose (services talk to SQLAlchemy directly) to avoid needless complexity.
- Swagger lives at /api/docs (not /docs) so the Nginx "/api" proxy rule covers it.
- Rate limiter is in-memory: fine for one backend container, would need Redis for several.

## Demo logins (after seeding, password Demo@12345)
admin@demo.dev, meera.manager@demo.dev, rohan.manager@demo.dev, dev.isha@demo.dev
