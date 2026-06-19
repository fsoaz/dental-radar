# Dental Radar — Product Requirements Document (PRD)

> Deliverable 1 (PRD) + Deliverable 9 (User Stories).
> Companion docs: [architecture.md](./architecture.md) · [roadmap.md](./roadmap.md).

## Deliverable checklist (where each lives)

| # | Deliverable | Location |
|---|-------------|----------|
| 1 | Product Requirements Document | this file |
| 2 | System Architecture | architecture.md |
| 3 | Domain Model | architecture.md |
| 4 | Database Schema | architecture.md |
| 5 | API Design | architecture.md |
| 6 | Folder Structure | architecture.md |
| 7 | MVP Roadmap | roadmap.md |
| 8 | Sprint Breakdown | roadmap.md |
| 9 | User Stories | this file |
| 10 | Technical Tasks | tasks/phase-*.md |

**Implementation status:** MVP (Phases 1–7) complete as of 2026-06-19. See [docs/README.md](../README.md).

---

## 1. Vision

Dental Radar is a **B2B sales-intelligence platform** that identifies dental clinics with the highest probability of buying a product or service and ranks them for sales outreach.

It answers one question:

> **"Which clinics should a salesperson contact first?"**

The system collects public information about dental clinics, detects growth/buying signals, computes a purchase-propensity score, and ranks clinics by likelihood of becoming customers.

## 2. Problem

Sales teams selling to dental clinics (implants, software, marketing, equipment) waste time on cold, manual prospecting. They lack a prioritized list of clinics showing buying intent. Dental Radar turns scattered public signals into a ranked call list.

## 3. Target users

| Persona | Need |
|---------|------|
| Sales rep / BDR | A ranked daily call list with reasons-to-call |
| Sales manager | Pipeline coverage, territory prioritization |
| Implant manufacturer | Clinics expanding into implantology |
| Dental software vendor | Clinics with weak/old web tech ready to upgrade |
| Marketing agency for dentists | Clinics already advertising, ripe to scale |

## 4. Success metrics (MVP)

- ≥ 500 clinics ingested for one pilot region.
- Every clinic has a computed score + priority band.
- ≥ 60% of "Hot/Immediate" clinics judged "worth contacting" by a pilot rep (manual eval).
- Dashboard loads ranked list in < 2s for 1k clinics.
- Scoring weights tunable by a non-developer (config, no redeploy).

## 5. Functional requirements

### 5.1 Clinic Discovery
Collect from public sources: clinic name, city, state, website, phone, Google rating, Google review count, website URL, social media URLs.

Sources (MVP → later):
- **Google Places API** — primary MVP source (reliable, paid per request).
- Public directories — later, behind same `ClinicSource` interface.
- Clinic websites — crawled for signals (see 5.3).

### 5.2 Clinic Profile
Each clinic stores: name, address, website, phone, Google rating, Google review count, number of locations, services offered, technology signals, marketing signals, hiring signals.

### 5.3 Signal Detection Engine
Detects the signals below and attaches a weight to each. Weights are **config-driven** (see [architecture.md → Scoring config](./architecture.md#scoring-engine--configuration)).

| Signal | Detects | Default weight |
|--------|---------|---------------:|
| Hiring activity | Implantologist / orthodontist / receptionist / sales-coordinator openings | **+25** |
| Advertising activity | Meta Pixel, Google Ads tags, conversion tracking, landing pages | **+30** |
| Website quality | Modern design, mobile responsive, lead forms, online scheduling | **+15** |
| Multi-location presence | Single / two / franchise / multiple branches | **+40** |
| High-ticket procedures | Implants, Invisalign, clear aligners, cosmetic, veneers, oral rehab | **+20** |

Each detected signal stores: type, weight applied, raw evidence (URL/snippet), detected_at, confidence.

### 5.4 Scoring Engine
```
Score = Hiring + Advertising + Website + Locations + HighTicket
```
Sum of weights of detected signals (plus optional AI contribution — see 5.5). **Configurable without code changes** (weights + bands in DB).

Priority bands:

| Band | Score |
|------|-------|
| Cold | 0–50 |
| Warm | 51–100 |
| Hot | 101–150 |
| Immediate Outreach | 150+ |

### 5.5 AI Enrichment Layer
An LLM analyzes the clinic website + profile and returns:
- Growth Probability (0–100)
- Technology Maturity (0–100)
- Marketing Sophistication (0–100)
- Expansion Probability (0–100)
- Short natural-language explanation.

Example explanation: *"Clinic appears growth-oriented due to active implant marketing, a modern website, and multiple service offerings."*

Default provider **OpenAI GPT**; Claude and Gemini pluggable behind one interface (`AI_PROVIDER=gpt|claude|gemini`). Provider design in architecture.md.

### 5.6 Dashboard
- Ranked clinic list (default sort by score desc).
- Search (name/city).
- Filters (state, priority band, score range, has-website, signal type).
- Clinic detail page (full profile, signals with evidence, AI breakdown + explanation).
- List columns: **Clinic Name · City · Score · Growth Probability · Priority Level**.

## 6. Non-goals (MVP, out of scope)
- CRM/email automation, outreach sending.
- Auth beyond a single admin/operator role + API key.
- Real-time re-scoring; batch refresh is fine.
- Multi-tenant billing.
- Scraping beyond Google Places + each clinic's own site.
- Mobile app.

---

## 7. User stories

Format: **As a `<role>`, I want `<capability>` so that `<value>`.** Each story lists acceptance criteria (AC). Stories link to technical tasks in `tasks/phase-*.md`.

### Epic A — Clinic Discovery  *(→ phase-2-discovery.md)*
- **US-A1** As an operator, I want to ingest clinics for a city/region from Google Places so that I have a base dataset.
  - AC: given a query (e.g. "dentist in Lisbon"), the system fetches and stores name, address, phone, website, rating, review_count; duplicates (same place_id) are upserted, not duplicated.
- **US-A2** As an operator, I want re-running ingestion to update existing clinics so that data stays fresh without duplicates.
  - AC: re-running updates rating/review_count/updated_at; place_id is the dedupe key.

### Epic B — Clinic Profile  *(→ phase-2-discovery.md)*
- **US-B1** As a rep, I want a full clinic profile so that I understand the prospect before calling.
  - AC: profile shows name, address, contact, rating, reviews, locations count, services, all detected signals with evidence, and AI breakdown if enriched.

### Epic C — Signal Detection  *(→ phase-3-signals.md)*
- **US-C1** As the system, I want to detect hiring/advertising/website/multi-location/high-ticket signals from a clinic's site so that score reflects buying intent.
  - AC: each detected signal persists type, applied weight, evidence snippet/URL, confidence, detected_at.
- **US-C2** As an operator, I want signal detection re-runnable per clinic so that I can refresh after a site change.
  - AC: re-running replaces prior signals of the same type for that clinic.

### Epic D — Scoring & Ranking  *(→ phase-4-scoring.md)*
- **US-D1** As a rep, I want clinics ranked by score so that I contact the most likely buyers first.
  - AC: list sorts by score desc; each clinic shows score + band.
- **US-D2** As a sales manager, I want to tune signal weights and band thresholds without a developer so that scoring matches our offer.
  - AC: editing config via API/admin recomputes scores on next run; no redeploy.
- **US-D3** As a rep, I want a score breakdown so that I know *why* a clinic ranks high.
  - AC: detail page shows per-signal contribution summing to the score.

### Epic E — AI Enrichment  *(→ phase-5-ai-enrichment.md)*
- **US-E1** As a rep, I want an AI growth/tech/marketing/expansion read plus a one-line explanation so that I get a fast qualitative judgment.
  - AC: enrichment returns four 0–100 scores + explanation; persisted with provider + model + prompt version.
- **US-E2** As an operator, I want to switch LLM provider via config so that I control cost/quality.
  - AC: setting `AI_PROVIDER` swaps GPT/Claude/Gemini with no code change; output schema identical.

### Epic F — Dashboard  *(→ phase-6-dashboard.md)*
- **US-F1** As a rep, I want a searchable, filterable ranked list so that I build my call list.
  - AC: search by name/city; filter by state, band, score range; columns Name/City/Score/Growth/Priority.
- **US-F2** As a rep, I want a clinic detail page so that I see everything in one view.
  - AC: detail shows profile + signals + evidence + AI breakdown.

### Epic G — Foundation & Deployment  *(→ phase-1-foundation.md, phase-7-deployment.md)*
- **US-G1** As a developer, I want the app to run locally via one command so that onboarding is fast.
  - AC: `docker compose up` starts API + Postgres + frontend; health check green.
- **US-G2** As an operator, I want the app deployed with CI/CD so that releases are repeatable.
  - AC: push to main runs tests + builds images + deploys; rollback documented.
