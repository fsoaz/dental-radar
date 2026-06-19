# Rollback Runbook

## When to rollback

- Error rate spike after deploy
- Failed migration (API container exits during startup)
- Broken frontend/API integration

## Fast rollback (redeploy previous image)

1. Identify the last known-good image tag (e.g. `sha-abc1234` from GHCR or a pinned `:main` from prior deploy).

2. Roll back containers:

```bash
./scripts/rollback.sh sha-<previous-commit>
```

3. Verify readiness:

```bash
curl -fsS http://localhost:8000/api/v1/health/ready
```

4. Monitor logs:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f api
```

## Database migration rollback

Alembic upgrades run automatically on API startup. **Downgrades are manual** and should be rare.

1. Stop API to prevent concurrent writes:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml stop api
```

2. Run downgrade inside a one-off container:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm api \
  alembic downgrade -1
```

3. Redeploy the previous application image tag (see above).

4. Take a fresh backup after stabilizing:

```bash
./scripts/backup-postgres.sh
```

## Restore from backup

```bash
gunzip -c backups/dental_radar_YYYYMMDDTHHMMSSZ.sql.gz | \
  docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres \
  psql -U dental_radar dental_radar
```

**Warning:** restore overwrites current data. Stop the API first and schedule downtime.

## CI verification

The deploy workflow runs `./scripts/rollback.sh smoke` after a successful smoke deploy to ensure the rollback path executes end-to-end.
