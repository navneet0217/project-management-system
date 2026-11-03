# Progress Tracker

## Auth pages
- Signup: `POST /api/v1/auth/signup` {email, full_name, password}; role is always DEVELOPER (server-side), returns tokens. Frontend `/signup` + redesigned `/login` share `components/AuthShell.tsx`. 40 backend tests pass.
- Next idea: SSO via OAuth2/OIDC (Google/GitHub), see chat notes.

## Docker / CI-CD (built, local stack verified)
- `docker-compose.yml` = mysql + backend + web (Nginx + built React) + cloudflared quick tunnel. Run: `docker compose up -d --build`, then `docker compose exec -T backend alembic upgrade head`. App on http://localhost:8080, public URL: `docker compose logs cloudflared | findstr trycloudflare`.
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

## Next task
1. Verify the backend on MySQL (commands below).
2. Day 5: React frontend core (see docs/API.md for every endpoint):
   layout + sidebar with role-based navigation, login page, auth context, Axios instance with
   refresh-token interceptor, protected routes, user management page, project list/detail,
   task list + form, toasts, loading/error states, dark mode.

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
