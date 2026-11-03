# Project: Project Management & Task Tracking System

A 7-day portfolio MVP with production-style architecture.
Full details: docs/PROJECT_CONTEXT.md | API reference: docs/API.md
Current status and next task: docs/PROGRESS.md

## Before doing anything
1. Read docs/PROJECT_CONTEXT.md, docs/API.md and docs/PROGRESS.md.
2. Continue from "Next task" in PROGRESS.md. Do not redo finished work.
3. When a task is finished, update docs/PROGRESS.md.

## Stack
- Frontend: React, TypeScript, Vite, Tailwind, React Router, Axios, Recharts, @dnd-kit
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
