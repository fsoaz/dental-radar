# Dental Radar — documentation

B2B sales-intelligence platform that ranks dental clinics by purchase propensity.

**MVP status:** Phases 1–7 complete (2026-06-19). The 2026-08-17 security hardening added enforced supply-chain gates, server-only frontend credentials, shared Redis rate limits, and removal of dormant auth scaffolding. The original QA release call remains in [internal/qa_report_2026-07-27.md](internal/qa_report_2026-07-27.md) as historical evidence; current changes are in the [changelog](../CHANGELOG.md).

This hub is organized by what you need to do next.

## Start

| Doc | When to read it |
|-----|-----------------|
| [Root README](../README.md) | Clone, boot the stack, find contribute links |
| [Tutorials: getting started](tutorials/getting-started.md) | First run: empty dashboard in under 10 minutes, no paid keys |
| [Glossary](reference/glossary.md) | Signal types, bands, operator key, enrichment fields |

## Operate

| Doc | When to read it |
|-----|-----------------|
| [Run the pilot pipeline](how-to/run-pilot-pipeline.md) | Discover → detect → score → enrich a region |
| [Tune scoring](how-to/tune-scoring.md) | Change weights and bands without a redeploy |
| [Deploy](how-to/deploy.md) | Production pre-flight, images, health probes, backups |
| [Roll back](how-to/rollback.md) | Previous image, migration downgrade, restore |
| [Troubleshoot](how-to/troubleshoot.md) | Test DB port, `API_KEY_NOT_CONFIGURED`, billed keys on the LAN |

## Understand

| Doc | When to read it |
|-----|-----------------|
| [Product](explanation/product.md) | Why the product exists, user stories, non-goals |
| [Architecture](explanation/architecture.md) | Layers, domain model, schema, pipeline, security |

## Look up

| Doc | When to read it |
|-----|-----------------|
| [API](reference/api.md) | Auth, errors, rate limits, curl. Schemas: `http://localhost:8000/docs` |
| [CLI](reference/cli.md) | `discover`, `detect`, `score`, `enrich`, `test-connection` |
| [Environment](reference/environment.md) | Every env var and which file it belongs in |

## Contribute

| Doc | When to read it |
|-----|-----------------|
| [CONTRIBUTING.md](../CONTRIBUTING.md) | PR, lint, tests, docs-in-the-same-PR |
| [CHANGELOG.md](../CHANGELOG.md) | Human-readable history |
| [conventions.md](standards/conventions.md) | Python / TypeScript / git |
| [api_rules.md](standards/api_rules.md) | REST conventions, error envelope |
| [ai_agent_rules.md](standards/ai_agent_rules.md) | LLM providers, prompts, retries |
| [testing.md](standards/testing.md) | Test strategy and CI |

## Internal

> **Note:** Engineering log. Not operator documentation. See [internal/README.md](internal/README.md).

| Doc | Purpose |
|-----|---------|
| [current_task.md](internal/current_task.md) | Current focus / handoff |
| [qa_report_2026-08-18.md](internal/qa_report_2026-08-18.md) | Current QA release call and post-fix verification |
| [qa_report_2026-07-27.md](internal/qa_report_2026-07-27.md) | Historical QA release call (superseded where noted by later hardening) |
| [roadmap.md](internal/roadmap.md) | Completed MVP phase plan |
| [tasks/](internal/tasks/) | Archived phase checklists |

## Remaining (pilot / post-MVP)

From QA §9.5 — not blocking a network-isolated pilot:

- Multi-page / locale-aware signal crawl
- Crawl status fields; social URLs / services
- Per-user authentication — the server-side operator `X-API-Key` covers MVP mutating routes
- Playwright E2E tests
- Measured scoring quality (Hot clinics worth contacting ≥60%)
