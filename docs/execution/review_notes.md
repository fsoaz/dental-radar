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
- [x] sources/google_places.py — **med** (partial) — unbounded discover pagination burns paid API quota. **Fixed:** capped via `PLACES_MAX_PAGES` (default 3). *Auth/rate-limit portion remains open (see below).*
- [ ] presentation/api + main.py — **high** — `PUT /scoring-config` and other mutating/expensive routes are fully unauthenticated. **Deferred:** JWT auth is post-MVP (Phase 2+). Compensating control: bind API to internal network + edge rate limiting; do not expose `0.0.0.0` publicly until auth ships.

Reviewed but not raised: SQLi (parameterized `ilike`), XSS (React escaping), prompt injection (bounded JSON + Pydantic), CI/dev passwords (ephemeral/dev-only).

### MVP complete — 2026-06-19
- No formal PR reviews recorded during initial build (single-session phase delivery).
- Post-MVP review recommended before production pilot: auth, rate limits on discovery/enrichment, secrets rotation.

---

_No PR-specific findings yet._
