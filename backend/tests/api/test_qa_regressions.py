"""Regression tests for QA report 2026-07-27 critical findings."""

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.use_cases.compute_score import ComputeScore, RescoreAll, UpdateScoringConfig
from app.application.use_cases.detect_signals import DetectSignals
from app.application.use_cases.discover_clinics import DiscoverClinics
from app.domain.repositories.clinic_repo import ClinicListQuery
from app.domain.services.signal_detection_service import SignalDetectionService
from app.infrastructure.repositories.sqlalchemy_score_repo import SqlAlchemyScoreRepository
from app.infrastructure.repositories.sqlalchemy_scoring_config_repo import (
    SqlAlchemyScoringConfigRepository,
)
from app.infrastructure.repositories.sqlalchemy_signal_repo import SqlAlchemySignalRepository
from app.main import create_app
from app.presentation.api.deps import get_db_session, get_update_scoring_config
from app.presentation.middleware.rate_limit import (
    RateLimitMiddleware,
    RateLimitResult,
    parse_trusted_proxies,
)
from tests.support.fakes import FakeClinicSource, FakeWebsiteCrawler, make_clinic_data

HIRING_HTML = "<html><body>We are hiring a receptionist</body></html>"

VALID_WEIGHTS = {
    "HIRING": 25,
    "ADVERTISING": 30,
    "WEBSITE_QUALITY": 15,
    "MULTI_LOCATION": 40,
    "HIGH_TICKET": 20,
}

VALID_BANDS = [
    {"name": "COLD", "min": 0, "max": 50},
    {"name": "WARM", "min": 51, "max": 100},
    {"name": "HOT", "min": 101, "max": 150},
    {"name": "IMMEDIATE", "min": 151, "max": None},
]


@pytest.fixture
def scoring_stack(db_session):
    from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository

    clinic_repo = SqlAlchemyClinicRepository(db_session)
    signal_repo = SqlAlchemySignalRepository(db_session)
    score_repo = SqlAlchemyScoreRepository(db_session)
    scoring_repo = SqlAlchemyScoringConfigRepository(db_session)
    crawler = FakeWebsiteCrawler()
    detect = DetectSignals(
        clinic_repo,
        signal_repo,
        scoring_repo,
        crawler,
        SignalDetectionService(),
    )
    compute = ComputeScore(clinic_repo, signal_repo, score_repo, scoring_repo)
    return clinic_repo, signal_repo, score_repo, scoring_repo, crawler, detect, compute


def _seed_scored_clinic(scoring_stack, html: str = HIRING_HTML):
    clinic_repo, _signal_repo, _score_repo, _scoring_repo, crawler, detect, compute = scoring_stack
    source = FakeClinicSource([make_clinic_data(place_id=f"qa-{uuid4()}")])
    DiscoverClinics(source, clinic_repo).execute("dentist")
    clinic = clinic_repo.list_clinics(ClinicListQuery()).items[0].clinic
    crawler.set_page(clinic.website, html)
    detect.execute(clinic.id)
    compute.execute(clinic.id)
    return clinic


def test_p0_1_crawl_failure_preserves_signals(scoring_stack):
    clinic = _seed_scored_clinic(scoring_stack)
    _clinic_repo, signal_repo, _score_repo, _scoring_repo, crawler, detect, _compute = scoring_stack

    before = signal_repo.list_by_clinic(clinic.id)
    assert len(before) >= 1

    crawler.fail(clinic.website, "DNS resolution failed")
    result = detect.execute(clinic.id)

    assert result.skipped is True
    after = signal_repo.list_by_clinic(clinic.id)
    assert len(after) == len(before)
    assert {s.type for s in after} == {s.type for s in before}


def test_p0_1_missing_website_preserves_signals(scoring_stack, db_session):
    clinic = _seed_scored_clinic(scoring_stack)
    clinic_repo, signal_repo, *_rest = scoring_stack

    from app.infrastructure.db.models import ClinicModel

    model = db_session.get(ClinicModel, clinic.id)
    assert model is not None
    model.website = None
    db_session.flush()

    before = signal_repo.list_by_clinic(clinic.id)
    result = scoring_stack[5].execute(clinic.id)
    assert result.skipped is True
    assert len(signal_repo.list_by_clinic(clinic.id)) == len(before)


def test_p0_2_invalid_band_name_rejected(client):
    response = client.put(
        "/api/v1/scoring-config",
        json={
            "weights": VALID_WEIGHTS,
            "bands": [{"name": "SUPER_HOT", "min": 0, "max": None}],
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_p1_5_band_gaps_rejected(client):
    response = client.put(
        "/api/v1/scoring-config",
        json={
            "weights": VALID_WEIGHTS,
            "bands": [
                {"name": "COLD", "min": 0, "max": 10},
                {"name": "HOT", "min": 50, "max": None},
            ],
        },
    )
    assert response.status_code == 422


def test_p1_6_empty_weights_rejected(client):
    response = client.put(
        "/api/v1/scoring-config",
        json={"weights": {}, "bands": VALID_BANDS},
    )
    assert response.status_code == 422


def test_p1_6_scoring_uses_config_not_stale_weight(scoring_stack):
    clinic = _seed_scored_clinic(scoring_stack)
    _clinic_repo, signal_repo, score_repo, scoring_repo, *_rest, compute = scoring_stack

    scoring_repo.update_active_config(
        weights={**VALID_WEIGHTS, "HIRING": 0},
        bands=VALID_BANDS,
    )
    compute.execute(clinic.id)
    score = score_repo.get_by_clinic(clinic.id)
    assert score is not None
    assert score.breakdown.to_dict().get("HIRING", 0) == 0
    assert score.total == 0


def test_p1_7_oversized_weight_rejected(client):
    response = client.put(
        "/api/v1/scoring-config",
        json={
            "weights": {**VALID_WEIGHTS, "HIRING": 3_000_000_000},
            "bands": [{"name": "COLD", "min": 0, "max": None}],
        },
    )
    assert response.status_code == 422


def test_p1_4_discover_missing_key_returns_envelope(db_session, monkeypatch):
    from app.application.use_cases.discover_clinics import DiscoverClinics
    from app.infrastructure.config import settings as settings_module
    from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository
    from app.infrastructure.sources.google_places import GooglePlacesClient
    from app.presentation.api.deps import get_clinic_source, get_db_session, get_discover_clinics

    monkeypatch.setattr(settings_module.settings, "google_places_api_key", "")

    app = create_app()
    repo = SqlAlchemyClinicRepository(db_session)
    source = GooglePlacesClient("")
    discover = DiscoverClinics(source, repo)

    def override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_clinic_source] = lambda: source
    app.dependency_overrides[get_discover_clinics] = lambda: discover

    with TestClient(app) as api_client:
        response = api_client.post(
            "/api/v1/clinics/discover",
            json={"query": "dentist in Lisbon"},
        )
        assert response.status_code == 503
        body = response.json()
        assert body["error"]["code"] == "DISCOVERY_UNAVAILABLE"
        assert "not configured" in body["error"]["message"].lower()

    app.dependency_overrides.clear()


def test_p2_12_invalid_filters_return_422(client):
    assert client.get("/api/v1/clinics?priority=BOGUS").status_code == 422
    assert client.get("/api/v1/clinics?signal_type=NOPE").status_code == 422
    assert client.get("/api/v1/clinics?sort=;DROP").status_code == 422
    assert client.get("/api/v1/clinics?min_score=200&max_score=10").status_code == 422


def test_p2_14_detail_includes_detected_at(scoring_stack, client, db_session):
    clinic = _seed_scored_clinic(scoring_stack)
    from app.presentation.api.deps import get_db_session

    app = create_app()

    def override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    with TestClient(app) as api_client:
        detail = api_client.get(f"/api/v1/clinics/{clinic.id}").json()
        assert detail["signals"]
        assert detail["signals"][0]["detected_at"] is not None
    app.dependency_overrides.clear()


def test_p2_18_literal_percent_search(scoring_stack):
    clinic_repo, *_rest = scoring_stack
    source = FakeClinicSource([make_clinic_data(place_id=f"pct-{uuid4()}", name="50% Off Dental")])
    DiscoverClinics(source, clinic_repo).execute("dentist")

    all_rows = clinic_repo.list_clinics(ClinicListQuery(q="%"))
    # Literal % should not match every clinic via LIKE wildcard.
    assert all(item.clinic.name.find("%") >= 0 for item in all_rows.items) or all_rows.total == 0

    named = clinic_repo.list_clinics(ClinicListQuery(q="50%"))
    assert named.total >= 1
    assert any("50%" in item.clinic.name for item in named.items)


def test_p3_21_noop_config_keeps_version(scoring_stack, db_session):
    clinic = _seed_scored_clinic(scoring_stack)
    clinic_repo, _signal_repo, _score_repo, scoring_repo, *_rest, compute = scoring_stack
    update = UpdateScoringConfig(scoring_repo, RescoreAll(clinic_repo, compute))

    app = create_app()

    def override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_update_scoring_config] = lambda: update

    with TestClient(app) as api_client:
        first = api_client.put(
            "/api/v1/scoring-config",
            json={"weights": VALID_WEIGHTS, "bands": VALID_BANDS, "rescore": False},
        )
        assert first.status_code == 200
        version = first.json()["version"]
        second = api_client.put(
            "/api/v1/scoring-config",
            json={"weights": VALID_WEIGHTS, "bands": VALID_BANDS, "rescore": False},
        )
        assert second.status_code == 200
        assert second.json()["version"] == version

    app.dependency_overrides.clear()
    assert clinic.id  # keep fixture used


# --- Rate limiter: X-Forwarded-For spoofing + unbounded memory (post-fix review) ---


class FakeRateLimitStore:
    def __init__(self, *, failing: bool = False) -> None:
        self.counts: dict[str, int] = {}
        self.failing = failing

    async def increment(self, key: str, window_seconds: int) -> RateLimitResult:
        if self.failing:
            raise ConnectionError("redis unavailable")
        self.counts[key] = self.counts.get(key, 0) + 1
        return RateLimitResult(self.counts[key], window_seconds)

    async def ping(self) -> None:
        return None

    async def close(self) -> None:
        return None


def _rate_limited_app(*, store: FakeRateLimitStore | None = None, **middleware_kwargs) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        store=store or FakeRateLimitStore(),
        **middleware_kwargs,
    )

    @app.post("/api/v1/clinics/discover")
    async def _discover() -> dict:
        return {"ok": True}

    return app


def test_rate_limit_not_bypassable_by_forged_forwarded_for():
    """Untrusted peers must not be able to reset their bucket via X-Forwarded-For."""
    app = _rate_limited_app(limit=3, window_seconds=60)

    with TestClient(app, client=("203.0.113.10", 5555)) as api_client:
        for _ in range(3):
            assert api_client.post("/api/v1/clinics/discover").status_code == 200

        blocked = api_client.post("/api/v1/clinics/discover")
        assert blocked.status_code == 429

        # Same caller, rotating the forgeable header — must stay blocked.
        for index in range(5):
            spoofed = api_client.post(
                "/api/v1/clinics/discover",
                headers={"X-Forwarded-For": f"10.9.{index}.{index}"},
            )
            assert spoofed.status_code == 429, "X-Forwarded-For reset an active rate limit"


def test_rate_limit_honours_forwarded_for_from_trusted_proxy():
    """Behind a configured proxy the real client, not the proxy, is limited."""
    app = _rate_limited_app(limit=2, window_seconds=60, trusted_proxies="203.0.113.10")

    with TestClient(app, client=("203.0.113.10", 5555)) as api_client:
        for _ in range(2):
            assert (
                api_client.post(
                    "/api/v1/clinics/discover",
                    headers={"X-Forwarded-For": "198.51.100.7"},
                ).status_code
                == 200
            )
        assert (
            api_client.post(
                "/api/v1/clinics/discover",
                headers={"X-Forwarded-For": "198.51.100.7"},
            ).status_code
            == 429
        )
        # A different downstream client behind the same proxy is unaffected.
        assert (
            api_client.post(
                "/api/v1/clinics/discover",
                headers={"X-Forwarded-For": "198.51.100.8"},
            ).status_code
            == 200
        )


def test_rate_limit_is_shared_across_app_instances():
    store = FakeRateLimitStore()
    first_app = _rate_limited_app(store=store, limit=3, window_seconds=60)
    second_app = _rate_limited_app(store=store, limit=3, window_seconds=60)

    with (
        TestClient(first_app, client=("203.0.113.10", 5555)) as first_client,
        TestClient(second_app, client=("203.0.113.10", 5555)) as second_client,
    ):
        assert first_client.post("/api/v1/clinics/discover").status_code == 200
        assert second_client.post("/api/v1/clinics/discover").status_code == 200
        assert first_client.post("/api/v1/clinics/discover").status_code == 200
        blocked = second_client.post("/api/v1/clinics/discover")

    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "60"


def test_rate_limit_fails_closed_when_store_is_unavailable():
    app = _rate_limited_app(store=FakeRateLimitStore(failing=True), limit=3)

    with TestClient(app) as api_client:
        response = api_client.post("/api/v1/clinics/discover")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "RATE_LIMIT_UNAVAILABLE"


def test_parse_trusted_proxies_ignores_garbage():
    networks = parse_trusted_proxies("10.0.0.0/8, not-an-ip, 192.168.1.5, ")
    assert len(networks) == 2


def test_entrypoint_does_not_trust_forwarded_headers_by_default():
    """uvicorn must not rewrite the peer address from X-Forwarded-For by default.

    A non-empty --forwarded-allow-ips makes uvicorn overwrite scope["client"]
    from the header before any middleware runs, which silently defeats the
    per-IP rate limiter. The API binds to loopback behind a same-host proxy, so
    a 127.0.0.1 default would trust every caller.
    """
    entrypoint = (
        Path(__file__).resolve().parents[2] / "scripts" / "docker-entrypoint.sh"
    ).read_text()
    assert 'FORWARDED_ALLOW_IPS="${FORWARDED_ALLOW_IPS:-}"' in entrypoint
    assert "--forwarded-allow-ips=*" not in entrypoint
    assert ":-127.0.0.1}" not in entrypoint
