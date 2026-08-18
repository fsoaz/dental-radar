# Phase 7 — Deployment (Technical Tasks)

Stories: US-G2. Sprint S7. Goal: repeatable releases + basic monitoring.

## Tasks
- [x] Backend `Dockerfile` (multi-stage, non-root, command-aware entrypoint); Compose runs Alembic through a one-shot migrator before API/worker startup.
- [x] Frontend `Dockerfile` (Next.js build + run).
- [x] Production `docker-compose` / deploy manifest (api, frontend, postgres, env/secrets).
- [x] Secrets via env / secret store; no secrets in image or repo.
- [x] CI/CD: on merge to `main` → lint + tests → build images → push → deploy.
- [x] Health checks wired to orchestrator (`/health`); readiness gate on migrations.
- [x] Basic monitoring: structured logs, request logging, error capture; uptime check on `/health`.
- [x] Backups: scheduled Postgres dump.
- [x] Rollback runbook (redeploy previous image tag; migration rollback notes).
- [x] Document deploy + rollback in README.

## Acceptance
- Push to `main` deploys automatically; health green post-deploy; rollback documented and tested once.
