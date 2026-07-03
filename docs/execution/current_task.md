# Current Task

> Single source of truth for what's being worked on right now. Update at the start of each work session.

- **Phase:** MVP complete (Phases 1–7)
- **Sprint:** S7 done
- **Status:** Ready for pilot
- **Owner:** —
- **Docs index:** [README.md](../README.md)

## Now
_All MVP phases shipped. Focus: pilot with real clinic data in a target region._

## Pilot checklist

1. Configure `.env` — `GOOGLE_PLACES_API_KEY`, LLM keys (`OPENAI_API_KEY`, etc.)
2. `docker compose up --build`
3. `python cli.py discover --query "dentist in <region>"`
4. `python cli.py test-connection`
5. `python cli.py detect --all && python cli.py score --all && python cli.py enrich --all`
6. Open http://localhost:3000/clinics — filter Hot/Immediate, review detail pages
7. Tune scoring via `PUT /api/v1/scoring-config` if needed

See [README.md](../README.md) (pilot workflow) and [runbooks/deploy.md](../runbooks/deploy.md) for production.

## Blockers
- None.

## Post-MVP backlog (unscheduled)
- JWT auth (`POST /auth/login`)
- Playwright E2E
- Async job queue for batch pipelines
