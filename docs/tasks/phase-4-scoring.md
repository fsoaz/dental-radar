# Phase 4 — Scoring Engine (Technical Tasks)

Stories: US-D1, US-D2, US-D3. Sprint S4. Goal: config-driven ranking + bands.

## Tasks
- [x] `ScoreBreakdown` VO (map SignalType→points, sums to total) + `PriorityLevel` enum.
- [x] `ScoringConfig` model (weights + bands) load from active `scoring_config` row.
- [x] `ScoringService.compute(signals, config) -> Score` (sum weights, build breakdown, map band). Pure, no I/O.
- [x] `ScoreRepository` + repo (1 row per clinic, overwrite); store `config_version`.
- [x] Use case `ComputeScore.execute(clinic_id)` and `RescoreAll.execute()`.
- [x] `POST /clinics/{id}/score`; batch CLI `score [--all]`.
- [x] `GET /scoring-config` (active) + `PUT /scoring-config` (new version, set active) → optional trigger re-score.
- [x] Extend `GET /clinics`: full filters (`priority`, `min_score`, `max_score`, `has_website`, `signal_type`) + `sort=-score` default + score/priority in payload.
- [x] Detail endpoint returns `score.breakdown`.
- [x] Tests: boundary bands (50/51, 100/101, 150/151), breakdown sums to total, config change re-ranks without code change.

## Acceptance
- Clinics ranked by score with band; editing config + re-score re-ranks; breakdown explains the score.
