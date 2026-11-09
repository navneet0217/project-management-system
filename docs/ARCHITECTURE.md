# Architecture

```
Browser -> Nginx (frontend container) -> /api -> FastAPI -> MySQL 8
                                                 |-> Resend (email)
Cloudflare quick tunnel exposes Nginx publicly.
```

- **Frontend** (`frontend/src`): React + TS + Vite, Ant Design, Redux Toolkit (auth, ui), Axios with refresh-on-401, dnd-kit Kanban.
- **Backend** (`backend/app`): `api/v1/endpoints` (thin routes) -> `services/` (business rules, RBAC checks) -> `models/` (SQLAlchemy). Alembic migrations 0001-0005.
- **Auth**: JWT access (15 min) + rotating refresh (7 days), Argon2 hashes, mandatory email verification, single-use hashed reset/verify tokens.
- **Audit + notifications**: every change goes through `audit_service.record()`, which also queues emails (sent only after commit).
- **Roles**: ADMIN, MANAGER, DEVELOPER, assigned through `users -> user_roles -> roles`. SQLAlchemy loads assigned roles in batches; backend checks combine them while retaining resource ownership restrictions. `users.role` caches the highest role for compatibility, with a fallback for legacy users without assignment links. Only admins grant roles; public signup remains DEVELOPER-only. Role/permission definitions remain in `roles -> role_permissions -> permissions`; custom permission administration is not exposed.

## Testing
From `backend/`: `python -m pytest` (100 tests: permissions, auth, email, notifications). Lint: `ruff check .`. Static frontend checks from `frontend/`: `pnpm exec tsc -p tsconfig.app.json --noEmit` and `pnpm lint`. Live browser and actual inbox delivery checks are recorded separately in `docs/MANUAL_TESTS.md`.

## CI/CD
`.github/workflows/ci-cd.yml`: backend (ruff, pytest, pip-audit), frontend (lint, build, pnpm audit; audits are non-blocking), then build images and deploy on the self-hosted runner with Docker Compose.

## Future work (not built)
Refresh token in an httpOnly cookie, Vitest UI tests, DB backup script, Swagger gating in production, and custom permission administration. Built-in role assignments are enforced in the services; frontend features are organized under `modules/`.
