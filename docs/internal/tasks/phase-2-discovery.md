# Phase 2 — Clinic Discovery (Technical Tasks)

Stories: US-A1, US-A2, US-B1. Sprint S2. Goal: real clinics in DB from Google Places.

## Tasks
- [x] Define `ClinicSource` port (`application/ports/clinic_source.py`): `search(query) -> list[ClinicData]`.
- [x] `infrastructure/sources/google_places.py`: `GooglePlacesClient` (Text Search + Place Details for phone/website/rating/reviews).
- [x] `ClinicData` DTO (name, place_id, address, phone, website, rating, review_count, social_urls).
- [x] `Clinic` entity + `Address` VO + `Location` entity.
- [x] `ClinicRepository` port + `SqlAlchemyClinicRepo` with **upsert by place_id**.
- [x] Use case `DiscoverClinics.execute(query)` → fetch, map, upsert; create primary `Location`.
- [x] `POST /clinics/discover` (body: query/region) → 202, returns count ingested.
- [x] `GET /clinics` list with pagination + basic `q`/`state` filter (full filters land in Phase 4).
- [x] `GET /clinics/{id}` detail (profile; signals/score/enrichment nullable until later phases).
- [x] CLI `discover --query "dentist in <city>"`.
- [x] Tests: upsert dedupe (same place_id updates), mapping, list pagination; Places client mocked.

## Acceptance
- Ingest ≥ 500 clinics for pilot region; re-run updates, no duplicates; list + detail return data.
