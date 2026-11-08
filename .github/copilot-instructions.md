# Project: Project Management & Task Tracking System

A 7-day portfolio MVP with production-style architecture.
Full details: docs/PROJECT_CONTEXT.md | API reference: docs/API.md
Current status and next task: docs/PROGRESS.md

## Before doing anything
1. Read docs/PROJECT_CONTEXT.md, docs/API.md and docs/PROGRESS.md.
2. Continue from "Next task" in PROGRESS.md. Do not redo finished work.
3. When a task is finished, update docs/PROGRESS.md.

## Stack
- Frontend: React, TypeScript, Vite, Ant Design, Redux Toolkit, React Router, Axios, Recharts, @dnd-kit
- Backend: FastAPI, SQLAlchemy 2.0, Pydantic, Alembic, JWT (access + refresh), Argon2, Pytest
- Database: MySQL 8.0
- DevOps: Docker, Docker Compose, Nginx, GitHub Actions, GHCR, Cloudflare Tunnel

## Rules
- Roles: ADMIN, MANAGER, DEVELOPER. Enforce RBAC on the backend, never only in the UI.
- API prefix: /api/v1. Swagger at /api/docs. Business logic lives in services/, not in route files.
- Never hardcode secrets. Use .env (never committed) and update .env.example.
- Add tests for permission checks and critical flows. Backend tests: `cd backend && python -m pytest`.
- Lint: `cd backend && ruff check .`
- Work in small steps, one day at a time. Explain decisions in simple English (the developer knows Angular, is learning React/FastAPI/Docker/CI-CD).
- Give exact terminal commands and say which directory to run them from.
- Branches: feature/* from dev, PR into dev. Never commit directly to main.
- Keep code consistent across frontend, backend, database, Docker and CI/CD.

## Engineering discipline (Ponytail, from DietrichGebert/ponytail, MIT)
The smallest complete change wins. Project rules above still apply.

**Before you write:** read the task and the code it touches. List every place the change must reach (callers, tests, fixtures, config, exports) and what it could break for users. That is scope; extra features are not.

**Take the first option that fully works:**
1. Does it need to exist? Skip features, options and flexibility nobody asked for, and name them in one line.
2. Already in this codebase (helper, component, service, pattern)? Reuse it the way the surrounding code does.
3. Standard library or platform feature? Use it, unless the project has its own (a house component beats a native widget).
4. An installed dependency? Use it. Never add a dependency for a few lines.
5. Otherwise write the minimum code that works.

- Be lazy about the solution, never about the change: finish every part the task needs, including callers, tests and fixtures it breaks.
- No abstraction, wrapper, option, config or "for later" code nobody asked for. Keep the existing layers and conventions.
- Bug fix: grep every caller of the function you touch, then fix the root cause once in the shared code.
- Code you move or merge keeps its error handling and validation.
- New non-trivial logic (branch, loop, parser, money, security) gets at least one small test.
- Comment only the why the code cannot show, in one line.
- Never cut: validation at trust boundaries, error handling that prevents data loss, security, accessibility, anything the user asked for.
- End each reply with one or two lines: what you skipped or did not check, and any risk the user must know.

## Installed agent skills (in .agents/skills/)
- archify: architecture, ERD and flow diagrams from the real code (use for docs/architecture).
- security-audit: Cloudflare security review. Run the full workflow only when asked for an audit.
- unslop: rewrites PROSE (docs, README, copy) to remove AI writing patterns. It does not review code.
