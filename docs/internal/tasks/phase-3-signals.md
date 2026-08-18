# Phase 3 — Signal Detection (Technical Tasks)

Stories: US-C1, US-C2. Sprint S3. Goal: typed signals with evidence attached to clinics.

## Tasks
- [x] `WebsiteCrawler` port + `infrastructure/crawler/website_crawler.py` (fetch HTML, extract text, scripts, meta, links). Respect timeouts; handle missing site.
- [x] `SignalType` VO enum + `SignalWeight`.
- [x] `SignalDetectionService` (pure rules), one detector per type:
  - [x] **Hiring** — careers/jobs page or keywords (implantologist, orthodontist, receptionist, sales coordinator).
  - [x] **Advertising** — Meta Pixel (`fbq`), Google Ads/gtag, conversion tags, landing-page patterns.
  - [x] **Website quality** — viewport/responsive meta, lead form, online scheduling widget, modern markers.
  - [x] **Multi-location** — multiple addresses/branch listings; set `clinic.locations_count`.
  - [x] **High-ticket** — keywords: implants, Invisalign, clear aligners, cosmetic, veneers, oral rehab.
- [x] Each detected `Signal` stores type, applied_weight (from active config), evidence snippet/URL, confidence, detected_at.
- [x] `SignalRepository` + repo; **replace same-type signals** on re-run (idempotent).
- [x] Use case `DetectSignals.execute(clinic_id)`.
- [x] `POST /clinics/{id}/signals:detect`; `GET /clinics/{id}/signals`.
- [x] CLI `detect [--clinic-id | --all]`.
- [x] Tests: each detector fires on fixture HTML with the cue, ignores HTML without it; evidence captured.

## Acceptance
- Crawled clinic gets 0–5 typed signals with evidence + confidence; re-run replaces, no duplication.
