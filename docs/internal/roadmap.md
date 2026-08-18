# Dental Radar — MVP Roadmap & Sprint Breakdown

> Deliverables 7 (Roadmap) + 8 (Sprint Breakdown).
> Per-phase technical tasks: [tasks/](./tasks/). Requirements: [product.md](../explanation/product.md).

Principle: ship a thin vertical slice fast, validate with one pilot region, then deepen. Each phase ends with something demonstrable.

**MVP status:** All phases (S1–S7) shipped 2026-06-19. QA remediation 2026-07-27 → pilot with reservations ([qa_report §9](./qa_report_2026-07-27.md#96-revised-release-recommendation)). See [docs/README.md](../README.md).

---

## Phases (Deliverable 7)

### Phase 1 — Foundation ✅
- **Goal:** Project skeleton runs locally.
- **Scope:** Repo layout, backend (FastAPI app factory, settings), Postgres + Alembic, base entities/tables, `docker compose up`, CI lint+test.
- **Exit:** `GET /health` green; migrations create all tables; `scoring_config` v1 seeded. *(US-G1)*

### Phase 2 — Clinic Discovery ✅
- **Goal:** Real clinics in the DB.
- **Scope:** `ClinicSource` port + `GooglePlacesClient`, `DiscoverClinics` use case, upsert by `place_id`, `POST /clinics/discover`, `GET /clinics`, CLI `discover`.
- **Exit:** Ingest ≥ 500 clinics for pilot region; list endpoint returns them. *(US-A1, US-A2, US-B1)*

### Phase 3 — Signal Detection ✅
- **Goal:** Signals attached to clinics.
- **Scope:** `WebsiteCrawler`, `SignalDetectionService` (5 signal types), evidence capture, `POST /clinics/{id}/signals:detect`, CLI `detect`.
- **Exit:** Each crawled clinic has 0–5 typed signals with evidence + confidence. *(US-C1, US-C2)*

### Phase 4 — Scoring Engine ✅
- **Goal:** Ranked clinics.
- **Scope:** `ScoringService`, config-driven weights/bands, `score` table, `GET/PUT /scoring-config`, `POST /clinics/{id}/score`, batch re-score, sort by score.
- **Exit:** Clinics ranked + banded; editing config re-ranks with no redeploy. *(US-D1, US-D2, US-D3)*

### Phase 5 — AI Enrichment ✅
- **Goal:** Qualitative AI read per clinic.
- **Scope:** `LLMProvider` interface + factory, GPT/Claude/Gemini, prompt v1, `EnrichClinic` use case, `POST /clinics/{id}/enrich`, persist 4 scores + explanation + provider/model/prompt_version.
- **Exit:** Enrichment returns 4 scores + explanation; provider swappable via `AI_PROVIDER`. *(US-E1, US-E2)*

### Phase 6 — Dashboard ✅
- **Goal:** Reps use it.
- **Scope:** Next.js list page (search/filter/sort, columns Name/City/Score/Growth/Priority), clinic detail page (profile + signals + AI breakdown), API client.
- **Exit:** Rep can search, filter, open a clinic, see why it ranks. *(US-F1, US-F2)*

### Phase 7 — Deployment ✅
- **Goal:** Repeatable releases.
- **Scope:** Dockerfiles, compose, CI/CD (test → build → deploy), env/secrets, logging/health monitoring, rollback runbook.
- **Exit:** Push to main deploys; rollback documented. *(US-G2)*

---

## Sprint breakdown (Deliverable 8)

~2-week sprints, one engineer assumed (scale by adding parallel tracks). Phases map roughly 1:1 to sprints; heavy phases split.

| Sprint | Phase(s) | Deliverable | Status |
|--------|----------|-------------|--------|
| **S1** | Phase 1 | Skeleton + DB + CI + health endpoint; all tables + seeded config | ✅ |
| **S2** | Phase 2 | Google Places discovery + list endpoint + ≥500 clinics ingested | ✅ |
| **S3** | Phase 3 | Crawler + 5 signal detectors + evidence persistence | ✅ |
| **S4** | Phase 4 | Scoring engine + config API + ranking + re-score batch | ✅ |
| **S5** | Phase 5 | LLM provider abstraction + GPT default + enrichment endpoint | ✅ |
| **S6** | Phase 6 | Dashboard list + detail pages wired to API | ✅ |
| **S7** | Phase 7 | Dockerize + CI/CD + monitoring + rollback runbook | ✅ |

### Dependencies (critical path)
```
S1 → S2 → S3 → S4 → S6 → S7
                 ↘ S5 ↗
```
S5 (AI) can run in parallel with S3/S4 once discovery (S2) lands, since it only needs clinic profile + site text; richer if signals/score exist.

### Cross-cutting (every sprint)
- Tests per [standards/testing.md](../standards/testing.md) (unit domain, integration infra, API contract).
- Update [work_log.md](./work_log.md) and [current_task.md](./current_task.md).
- Keep `.env.example` and `.env.production.example` current.

### MVP demo definition (achieved)
Ingest a pilot region → signals detected → scored/ranked → AI-enriched → rep opens dashboard, filters to **Hot/Immediate**, opens a clinic, reads the score breakdown + AI explanation.

```bash
python cli.py discover --query "dentist in Lisbon"
python cli.py detect --all && python cli.py score --all && python cli.py enrich --all
open http://localhost:3000/clinics
```

---

## Post-MVP (not scheduled)

- JWT auth + operator login
- Playwright E2E in CI
- Additional discovery sources beyond Google Places
- Async job queue for batch pipelines
- Multi-tenant / team roles
