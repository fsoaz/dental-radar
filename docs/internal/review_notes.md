# Review Notes

> Code-review findings per PR/sprint. One line per finding: `location — severity — problem — fix`. Resolve or carry forward.

## Template
```
### PR #<n> / <branch> — <date>
- [ ] path:line — <high|med|low> — <problem>. <fix>.
```

---

### Security review — 2026-06-19
Findings from automated security review of branch changes. 1 High, 3 Medium.
- [x] crawler/website_crawler.py — **med** — SSRF: redirect-following fetch with no scheme/IP allowlist (cloud metadata, internal services reachable). **Fixed:** `assert_public_url()` (http(s)-only + private/link-local/metadata denylist) + manual per-hop redirect validation (`UnsafeUrlError`). Tests in `tests/unit/test_website_crawler.py`.
- [x] ai/providers/base_provider.py — **med** — Gemini API key sent in `?key=` query string (leaks to access logs). **Fixed:** moved to `x-goog-api-key` header.
- [x] sources/google_places.py — **med** (partial) — unbounded discover pagination burns paid API quota. **Fixed:** capped via `PLACES_MAX_PAGES` (default 3). *Auth/rate-limit portion closed in QA remediation 2026-07-27.*
- [x] presentation/api + main.py — **high** — mutating/expensive routes unauthenticated. **Fixed (2026-07-27):** operator `X-API-Key` on mutating routes; fail-closed without `API_KEY`; in-app rate limits; `/docs` off in production; prod bind `127.0.0.1`. See [qa_report_2026-07-27.md](qa_report_2026-07-27.md) §9. JWT login remains post-MVP.

Reviewed but not raised: SQLi (parameterized `ilike`), XSS (React escaping), prompt injection (bounded JSON + Pydantic), CI/dev passwords (ephemeral/dev-only).

### MVP QA — 2026-07-27
- Full product/QA review + post-fix verification: [qa_report_2026-07-27.md](qa_report_2026-07-27.md).
- Release call revised to **Yes, with reservations** (pilot behind network isolation).
- Introduced-then-fixed: rate-limiter XFF bypass when uvicorn trusted loopback (§9.3).

### MVP complete — 2026-06-19
- No formal PR reviews recorded during initial build (single-session phase delivery).
- Post-MVP review recommended before production pilot: auth, rate limits on discovery/enrichment, secrets rotation. → Addressed in QA remediation 2026-07-27 (operator API key + rate limits); secrets rotation remains an ops practice.

### Security audit — 2026-08-17
Independent static-review security audit of `main` @ 9ec1c09, run through two correction rounds with the maintainer (severity recalibration, then wording precision) before remediation. 0 Critical/High, 1 Medium, 3 Low, 2 Informational — all six closed same-day. Full report retained as a private Claude Artifact (not committed to the repo).

- [x] .github/workflows/ci.yml, deploy.yml — **med** — no secret-scanning or dependency-CVE gate in CI (no gitleaks, no Dependabot, no `pip-audit`/`npm audit`). **Fixed:** gitleaks (commit-SHA pinned) + `pip-audit` against a `uv`-locked export of production deps + `npm audit --audit-level=high` in a new `security` job; `.github/dependabot.yml` covers pip/npm/github-actions; every workflow action moved from a floating tag to a commit-SHA pin; `backend/uv.lock` added (closes the prior floor-constraints-only gap too).
- [x] backend/app/infrastructure/db/models.py, config/settings.py — **low** — dead `app_user` table + `jwt_secret` (insecure default `"change-me-in-production"`), zero runtime path, but forced onto every prod deploy via `docker-compose.prod.yml`. **Fixed:** both removed; migration `0004_drop_app_user` (reversible downgrade).
- [x] frontend/lib/api.ts — **low** — operator API key stored in browser `localStorage`, readable by any same-origin script. **Fixed:** replaced with a same-origin Node-runtime BFF route (`frontend/app/api/backend/[...path]/route.ts`) that holds `API_KEY` server-side only; also retires the old build-time `NEXT_PUBLIC_API_URL` baking (P1-9-adjacent) as a side effect.
- [x] backend/app/presentation/middleware/rate_limit.py — **low** — rate-limit buckets were per-process, don't hold across replicas. **Fixed:** Redis-backed shared store (atomic `INCR`+`PEXPIRE`), fails closed with 503 if Redis is unreachable rather than opening the billed routes it guards.
- [x] .env, backend/.env — **info** — mode 644 (compensating control already present: containing directory mode 700). **Fixed:** `chmod 600` as defense-in-depth.
- [x] docker-compose.yml, docker-compose.prod.yml — **info** — dev stack bound to all interfaces, known/open per [qa_report_2026-07-27.md](qa_report_2026-07-27.md) §9.5. **Fixed:** dev services and the prod frontend port now bind `127.0.0.1` by default (`FRONTEND_BIND`).

Re-verified in source, not re-raised: SSRF guard, fail-closed auth, rate-limiter XFF trust boundary, scoring-config validation, prod-compose secret enforcement, Dockerfile hardening — all still hold from the 2026-07-27 pass. Also confirmed clean this round: LLM provider error handling never leaks upstream detail to clients (all three providers, not just Gemini), no CORS wildcard in shipped config/template, Next.js locked past the CVE-2025-29927 fix line.

---

_No PR-specific findings yet._
