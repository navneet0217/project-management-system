# Architecture

```
Browser -> Nginx (frontend container) -> /api -> FastAPI -> MySQL 8
                                                 |-> Resend (email)
Cloudflare quick tunnel exposes Nginx publicly.
```

- **Frontend** (`frontend/src`): React + TS + Vite, Ant Design, Redux Toolkit (auth, ui), Axios with refresh-on-401, dnd-kit Kanban.
- **Backend** (`backend/app`): `api/v1/endpoints` (thin routes) -> `services/` (business rules, RBAC checks) -> `models/` (SQLAlchemy). Alembic migrations 0001-0004.
- **Auth**: JWT access (15 min) + rotating refresh (7 days), Argon2 hashes, mandatory email verification, single-use hashed reset/verify tokens.
- **Audit + notifications**: every change goes through `audit_service.record()`, which also queues emails (sent only after commit).
- **Roles**: ADMIN, MANAGER, DEVELOPER, enforced on the backend.

## Testing
`cd backend && python -m pytest` (92 tests: permissions, auth, email, notifications). Lint: `ruff check .`.

## CI/CD
`.github/workflows/ci-cd.yml`: backend (ruff, pytest, pip-audit), frontend (lint, build, pnpm audit; audits are non-blocking), then build images and deploy on the self-hosted runner with Docker Compose.

## Future work (not built)
Refresh token in an httpOnly cookie, Vitest UI tests, DB backup script, Swagger gating in production, moving the other features (projects, tasks, users) into `modules/` like auth, and enforcing the new `roles`/`permissions` tables in the services (migration 0005 creates and backfills them; `users.role` is still what RBAC checks today).
