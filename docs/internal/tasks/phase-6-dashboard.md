# Phase 6 — Dashboard (Technical Tasks)

Stories: US-F1, US-F2. Sprint S6. Goal: reps use a ranked, searchable UI.

## Tasks
- [x] Next.js app (app router) + TypeScript + Tailwind + shadcn/ui init.
- [x] Typed API client in `lib/` (clinics list, clinic detail, scoring-config) + shared `types.ts`.
- [x] `app/clinics/page.tsx` — ranked list:
  - [x] Columns: **Clinic Name · City · Score · Growth Probability · Priority Level**.
  - [x] Search box (name/city → `q`).
  - [x] Filters: state, priority band, score range, has-website, signal type.
  - [x] Sort by score desc default; pagination.
- [x] Components: `ClinicTable`, `FilterBar`, `ScoreBadge` (band color), `PriorityTag`.
- [x] `app/clinics/[id]/page.tsx` — detail: profile, contact, rating/reviews, locations, services, `SignalList` (with evidence), `AIBreakdown` (4 scores + explanation), score breakdown.
- [x] Loading/empty/error states.
- [x] Wire to backend base URL via env (`NEXT_PUBLIC_API_URL`).
- [x] Tests: ClinicTable renders rows, FilterBar updates query, detail renders breakdown (Vitest); optional Playwright happy path.

## Acceptance
- Rep searches, filters to Hot/Immediate, opens a clinic, sees why it ranks (signals + AI explanation). List < 2s for 1k clinics.
