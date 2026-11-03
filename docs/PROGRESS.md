# Progress Tracker

## Branding
- App name: **Tasklane** (name + logo in `frontend/src/components/Logo.tsx`, favicon `frontend/public/favicon.svg`, colours in `frontend/src/lib/brand.ts`). Teal theme (#0d9488). Logo = three rising Kanban lanes on a teal tile.

## Auth pages
- Signup: `POST /api/v1/auth/signup` {email, full_name, password}; role is always DEVELOPER (server-side), returns tokens. Frontend `/signup` + redesigned `/login` share `components/AuthShell.tsx`. 40 backend tests pass.
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
Run from `frontend/`: `pnpm install`, `pnpm dev` (proxies /api to localhost:8000).

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
