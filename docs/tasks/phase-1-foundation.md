# Phase 1 — Foundation (Technical Tasks)

Stories: US-G1. Sprint S1. Goal: skeleton runs locally, DB + migrations + CI green.

## Tasks
- [x] Init repo layout (`backend/`, `frontend/`, `docker-compose.yml`, `.github/workflows/ci.yml`) per [architecture.md](../context/architecture.md#7-folder-structure-deliverable-6).
- [x] Backend `pyproject.toml`: FastAPI, SQLAlchemy, Alembic, pydantic-settings, pytest, ruff.
- [x] `app/main.py` FastAPI app factory + DI wiring stub; `GET /health` returns `{"status":"ok"}`.
- [x] `infrastructure/config/settings.py` (pydantic-settings) reading env; commit `.env.example`.
- [x] DB session + engine (`infrastructure/db/session.py`); `DATABASE_URL` from env.
- [x] SQLAlchemy models for all tables (clinic, location, signal, score, enrichment, scoring_config, app_user).
- [x] Alembic init; initial migration creating all tables; seed `scoring_config` v1 from `scoring_defaults.yaml`.
- [x] `docker-compose.yml`: api + postgres + frontend; migrations run on api start (`alembic upgrade head`).
- [x] CI workflow: ruff lint + pytest.
- [x] Smoke test: `GET /health` 200; assert tables + seeded config exist.

## Acceptance
- `docker compose up` → API healthy, all tables present, `scoring_config` v1 active.
